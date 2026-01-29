#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
FeatrixXGBoostClassifier - XGBoost classifier using Featrix embeddings as features.

Usage:
    from featrix.neural.xgboost_classifier import FeatrixXGBoostClassifier

    clf = FeatrixXGBoostClassifier(embedding_space)
    clf.fit(train_df, target_col='label')
    predictions = clf.predict(test_df)
    probabilities = clf.predict_proba(test_df)
"""
import logging
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder

try:
    import xgboost as xgb
except ImportError as e:
    raise ImportError(
        "XGBoost is required for FeatrixXGBoostClassifier. "
        "Install with: pip install xgboost"
    ) from e

from featrix.neural.embedded_space import EmbeddingSpace

logger = logging.getLogger(__name__)


class FeatrixXGBoostClassifier:
    """
    XGBoost classifier using Featrix embeddings as features.

    Combines Featrix representation learning with XGBoost gradient boosting.

    Booster Types:
        - 'gbtree' (default): Gradient boosted decision trees. Good for non-linear
          relationships but prone to overfitting on high-dimensional embeddings.
          Uses max_depth, min_child_weight, gamma for regularization.

        - 'gblinear': Linear booster - essentially regularized logistic regression
          with gradient boosting. No trees, just learns linear weights on the
          embedding dimensions. Much less prone to overfitting, but can only
          capture linear relationships. Uses lambda (L2) and alpha (L1) for
          regularization. Good choice when embeddings already capture non-linear
          structure and you just need a simple linear classifier on top.

    Args:
        embedding_space: The trained EmbeddingSpace to encode features
        xgb_params: Override default XGBoost parameters
        name: Optional name for this classifier
        use_linear_booster: If True, use gblinear instead of gbtree (default: False)
    """

    def __init__(
        self,
        embedding_space: EmbeddingSpace,
        xgb_params: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        use_linear_booster: bool = False,
    ):
        self.embedding_space = embedding_space
        self.d_model = embedding_space.d_model
        self.name = name
        self.use_linear_booster = use_linear_booster
        self.xgb_model: Optional[xgb.XGBClassifier] = None
        self.target_col: Optional[str] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.n_classes: Optional[int] = None
        self.classes_: Optional[np.ndarray] = None

        if use_linear_booster:
            # LINEAR BOOSTER: Regularized logistic regression via gradient boosting
            # No trees - just learns linear weights on embedding dimensions
            # Much less prone to overfitting than tree-based methods
            self.xgb_params = {
                'booster': 'gblinear',       # Linear booster (no trees)
                'learning_rate': 0.1,        # Can be higher since no tree overfitting
                'n_estimators': 100,         # Number of boosting rounds
                'reg_alpha': 0.5,            # L1 regularization (sparsity)
                'reg_lambda': 1.0,           # L2 regularization (shrinkage)
                'random_state': 42,
                'n_jobs': -1,
                'verbosity': 0,
            }
        else:
            # TREE BOOSTER with MODERATE regularization
            # Extreme regularization made val AUC worse (0.58 vs 0.66)
            # Try moderate settings - allow some complexity but prevent extreme overfitting
            self.xgb_params = {
                'booster': 'gbtree',         # Tree booster (default)
                'max_depth': 3,              # Moderate depth (was 1 extreme, 2 aggressive)
                'learning_rate': 0.1,        # Standard learning rate
                'n_estimators': 100,         # Standard number of trees
                'subsample': 0.8,            # Light subsampling
                'colsample_bytree': 0.8,     # Light feature sampling
                'min_child_weight': 1,       # Standard (default)
                'reg_alpha': 0.0,            # No L1 regularization
                'reg_lambda': 1.0,           # Light L2 regularization (default)
                'gamma': 0.0,                # No min loss reduction
                'random_state': 42,
                'n_jobs': -1,
                'verbosity': 0,
            }
        if xgb_params:
            self.xgb_params.update(xgb_params)

        self.training_time_: Optional[float] = None
        self.encoding_time_: Optional[float] = None
        self.fit_metrics_: Optional[Dict[str, float]] = None

    def _encode_dataframe(self, df: pd.DataFrame, batch_size: int = 256,
                          exclude_cols: Optional[List[str]] = None) -> np.ndarray:
        """Encode DataFrame into embeddings."""
        exclude_cols = exclude_cols or []
        cols_to_use = [c for c in df.columns if c not in exclude_cols]
        records = df[cols_to_use].to_dict('records')
        return self.embedding_space.encode_records_batch(records, batch_size=batch_size, short=False)

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Union[pd.Series, np.ndarray]] = None,
            target_col: Optional[str] = None, eval_set: Optional[List[tuple]] = None,
            batch_size: int = 256, verbose: bool = True) -> 'FeatrixXGBoostClassifier':
        """
        Fit the classifier.

        Args:
            X: DataFrame with target_col, or feature array
            y: Target values (if X doesn't contain target)
            target_col: Name of target column in X
            eval_set: Optional [(X_val, y_val)] for early stopping
            batch_size: Encoding batch size
            verbose: Print progress
        """
        # ====================================================================
        # CRITICAL: Assert no internal __featrix_ columns leaked into training
        # ====================================================================
        from featrix.neural.utils import assert_no_internal_columns
        if hasattr(self, 'embedding_space') and self.embedding_space:
            if hasattr(self.embedding_space, 'col_codecs') and self.embedding_space.col_codecs:
                assert_no_internal_columns(
                    list(self.embedding_space.col_codecs.keys()),
                    context="FeatrixXGBoostClassifier.fit() embedding_space.col_codecs",
                    raise_error=True
                )
        # Also check the input DataFrame columns
        if isinstance(X, pd.DataFrame):
            assert_no_internal_columns(
                list(X.columns),
                context="FeatrixXGBoostClassifier.fit() input DataFrame columns",
                raise_error=True
            )

        start_time = time.time()

        if isinstance(X, pd.DataFrame):
            if target_col is not None:
                self.target_col = target_col
                if target_col not in X.columns:
                    raise ValueError(f"Target column '{target_col}' not in DataFrame")
                y_train = X[target_col].values
                df_train = X
            elif y is not None:
                y_train = y if isinstance(y, np.ndarray) else y.values
                df_train = X
                self.target_col = None
            else:
                raise ValueError("Provide target_col or y")
        else:
            if y is None:
                raise ValueError("y required when X is array")
            y_train = y if isinstance(y, np.ndarray) else np.array(y)
            df_train = pd.DataFrame(X)
            self.target_col = None

        self.label_encoder = LabelEncoder()
        if y_train.dtype == 'bool':
            y_train = y_train.astype(int)
        elif y_train.dtype == 'object':
            y_train = self.label_encoder.fit_transform(y_train)
        else:
            self.label_encoder.fit(y_train)
            y_train = self.label_encoder.transform(y_train)

        self.n_classes = len(self.label_encoder.classes_)
        self.classes_ = self.label_encoder.classes_

        if verbose:
            logger.info(f"FeatrixXGBoostClassifier: {len(df_train)} samples, {self.n_classes} classes, d={self.d_model}")

        encode_start = time.time()
        exclude = [self.target_col] if self.target_col else []
        X_train = self._encode_dataframe(df_train, batch_size=batch_size, exclude_cols=exclude)
        self.encoding_time_ = time.time() - encode_start

        if verbose:
            logger.info(f"  Encoding: {self.encoding_time_:.1f}s")

        xgb_params = self.xgb_params.copy()
        if self.n_classes == 2:
            xgb_params['objective'] = 'binary:logistic'
            xgb_params['eval_metric'] = 'logloss'
        else:
            xgb_params['objective'] = 'multi:softprob'
            xgb_params['eval_metric'] = 'mlogloss'
            xgb_params['num_class'] = self.n_classes

        self.xgb_model = xgb.XGBClassifier(**xgb_params)

        xgb_eval_set = None
        if eval_set:
            xgb_eval_set = []
            for X_eval, y_eval in eval_set:
                if isinstance(X_eval, pd.DataFrame):
                    X_eval_enc = self._encode_dataframe(X_eval, batch_size=batch_size, exclude_cols=exclude)
                else:
                    X_eval_enc = X_eval
                y_eval_enc = self.label_encoder.transform(y_eval) if hasattr(y_eval, 'dtype') and y_eval.dtype == 'object' else y_eval
                xgb_eval_set.append((X_eval_enc, y_eval_enc))

        fit_kwargs = {}
        if xgb_eval_set:
            fit_kwargs['eval_set'] = xgb_eval_set
            fit_kwargs['early_stopping_rounds'] = 20
        self.xgb_model.fit(X_train, y_train, verbose=False, **fit_kwargs)
        self.training_time_ = time.time() - start_time

        y_pred = self.xgb_model.predict(X_train)
        y_prob = self.xgb_model.predict_proba(X_train)
        self.fit_metrics_ = {
            'accuracy': accuracy_score(y_train, y_pred),
            'f1': f1_score(y_train, y_pred, average='macro'),
        }
        if self.n_classes == 2:
            self.fit_metrics_['auc'] = roc_auc_score(y_train, y_prob[:, 1])
        else:
            self.fit_metrics_['auc'] = roc_auc_score(y_train, y_prob, multi_class='ovr', average='macro')

        if verbose:
            logger.info(f"  Train AUC: {self.fit_metrics_['auc']:.4f}, Acc: {self.fit_metrics_['accuracy']:.4f}")

        return self

    def predict(self, X: Union[pd.DataFrame, np.ndarray, List[Dict]], batch_size: int = 256) -> np.ndarray:
        """Predict class labels."""
        if self.xgb_model is None:
            raise RuntimeError("Not fitted")
        X_enc = self._prepare_input(X, batch_size)
        y_pred = self.xgb_model.predict(X_enc)
        return self.label_encoder.inverse_transform(y_pred)

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray, List[Dict]], batch_size: int = 256) -> np.ndarray:
        """Predict class probabilities."""
        if self.xgb_model is None:
            raise RuntimeError("Not fitted")
        X_enc = self._prepare_input(X, batch_size)
        return self.xgb_model.predict_proba(X_enc)

    def _prepare_input(self, X: Union[pd.DataFrame, np.ndarray, List[Dict]], batch_size: int = 256) -> np.ndarray:
        """Encode input if needed."""
        if isinstance(X, np.ndarray):
            if X.shape[1] == self.d_model:
                return X
            raise ValueError(f"Array has {X.shape[1]} features, expected {self.d_model}")
        if isinstance(X, list):
            X = pd.DataFrame(X)
        exclude = [self.target_col] if self.target_col else []
        return self._encode_dataframe(X, batch_size=batch_size, exclude_cols=exclude)

    def score(self, X, y, batch_size: int = 256) -> float:
        """Return accuracy."""
        return accuracy_score(y, self.predict(X, batch_size))

    def evaluate(self, X, y, batch_size: int = 256) -> Dict[str, float]:
        """Return accuracy, f1, auc."""
        y_pred = self.predict(X, batch_size)
        y_prob = self.predict_proba(X, batch_size)
        y_enc = y.astype(int) if hasattr(y, 'dtype') and y.dtype == 'bool' else y
        if hasattr(y_enc, 'dtype') and y_enc.dtype == 'object':
            y_enc = self.label_encoder.transform(y_enc)
        y_pred_enc = self.label_encoder.transform(y_pred)
        # Use explicit labels from training for consistent metrics
        all_labels = list(range(self.n_classes))
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'f1': f1_score(y_enc, y_pred_enc, labels=all_labels, average='macro', zero_division=0)
        }
        if self.n_classes == 2:
            metrics['auc'] = roc_auc_score(y_enc, y_prob[:, 1])
        else:
            metrics['auc'] = roc_auc_score(y_enc, y_prob, multi_class='ovr', average='macro')
        return metrics

    def save(self, filepath: Union[str, Path]) -> None:
        """Save classifier (not EmbeddingSpace)."""
        state = {
            'xgb_model': self.xgb_model, 'label_encoder': self.label_encoder,
            'target_col': self.target_col, 'n_classes': self.n_classes,
            'classes_': self.classes_, 'd_model': self.d_model,
            'xgb_params': self.xgb_params, 'name': self.name,
            'use_linear_booster': self.use_linear_booster,
            'training_time_': self.training_time_, 'encoding_time_': self.encoding_time_,
            'fit_metrics_': self.fit_metrics_,
        }
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)

    @classmethod
    def load(cls, filepath: Union[str, Path], embedding_space: EmbeddingSpace) -> 'FeatrixXGBoostClassifier':
        """Load classifier."""
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        if state['d_model'] != embedding_space.d_model:
            raise ValueError(f"d_model mismatch: {embedding_space.d_model} vs {state['d_model']}")
        use_linear = state.get('use_linear_booster', False)
        clf = cls(embedding_space, xgb_params=state['xgb_params'], name=state['name'], use_linear_booster=use_linear)
        for k in ['xgb_model', 'label_encoder', 'target_col', 'n_classes', 'classes_', 'training_time_', 'encoding_time_', 'fit_metrics_']:
            setattr(clf, k, state[k])
        return clf

    def __repr__(self) -> str:
        status = "fitted" if self.xgb_model else "not fitted"
        booster = "linear" if self.use_linear_booster else "tree"
        return f"FeatrixXGBoostClassifier(d_model={self.d_model}, booster={booster}, {status})"