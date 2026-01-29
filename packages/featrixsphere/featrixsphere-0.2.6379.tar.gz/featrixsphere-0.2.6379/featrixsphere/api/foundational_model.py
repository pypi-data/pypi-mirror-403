"""
FoundationalModel class for FeatrixSphere API.

Represents a trained embedding space (foundational model).
"""

import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .http_client import ClientContext
    import pandas as pd
    import numpy as np

from .predictor import Predictor
from .vector_database import VectorDatabase
from .reference_record import ReferenceRecord

logger = logging.getLogger(__name__)


@dataclass
class FoundationalModel:
    """
    Represents a foundational model (embedding space).

    Attributes:
        id: Session ID / FM ID
        name: Model name
        status: Training status ("training", "done", "error")
        dimensions: Embedding dimensions (d_model)
        epochs: Training epochs completed
        created_at: Creation timestamp

    Usage:
        # Create from client
        fm = featrix.create_foundational_model(
            name="customer_embeddings",
            csv_file="customers.csv"
        )

        # Wait for training
        fm.wait_for_training()

        # Create classifier
        predictor = fm.create_classifier(
            name="churn_predictor",
            target_column="churned"
        )

        # Create vector database
        vdb = fm.create_vector_database(
            name="customer_search",
            records=customer_records
        )

        # Encode records
        vectors = fm.encode([{"age": 35}, {"age": 42}])
    """

    id: str
    name: Optional[str] = None
    status: Optional[str] = None
    dimensions: Optional[int] = None
    epochs: Optional[int] = None
    final_loss: Optional[float] = None
    created_at: Optional[datetime] = None

    # Internal
    _ctx: Optional['ClientContext'] = field(default=None, repr=False)

    @classmethod
    def from_response(
        cls,
        response: Dict[str, Any],
        ctx: Optional['ClientContext'] = None
    ) -> 'FoundationalModel':
        """Create FoundationalModel from API response."""
        session_id = response.get('session_id', '')

        return cls(
            id=session_id,
            name=response.get('name'),
            status=response.get('status'),
            dimensions=response.get('d_model') or response.get('dimensions'),
            epochs=response.get('epochs') or response.get('final_epoch'),
            final_loss=response.get('final_loss'),
            created_at=datetime.now(),
            _ctx=ctx,
        )

    @classmethod
    def from_session_id(
        cls,
        session_id: str,
        ctx: 'ClientContext'
    ) -> 'FoundationalModel':
        """Load FoundationalModel from session ID."""
        # Get session info
        session_data = ctx.get_json(f"/compute/session/{session_id}")

        fm = cls(
            id=session_id,
            name=session_data.get('name'),
            status=session_data.get('status'),
            created_at=datetime.now(),
            _ctx=ctx,
        )

        # Try to get model info
        fm._update_from_session(session_data)

        return fm

    def create_classifier(
        self,
        target_column: str,
        name: Optional[str] = None,
        labels_file: Optional[str] = None,
        labels_df: Optional['pd.DataFrame'] = None,
        epochs: int = 0,
        rare_label_value: Optional[str] = None,
        class_imbalance: Optional[Dict[str, float]] = None,
        webhooks: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Predictor:
        """
        Create a classifier predictor from this foundational model.

        Args:
            target_column: Column name to predict
            name: Predictor name (optional)
            labels_file: Path to labels file (optional - use existing data if not provided)
            labels_df: DataFrame with labels (optional)
            epochs: Training epochs (0 = auto)
            rare_label_value: Rare class for metrics
            class_imbalance: Expected class distribution
            webhooks: Webhook URLs for events
            **kwargs: Additional training parameters

        Returns:
            Predictor object (training started)

        Example:
            predictor = fm.create_classifier(
                target_column="churned",
                name="churn_predictor"
            )
            predictor.wait_for_training()
        """
        return self._create_predictor(
            target_column=target_column,
            target_type="set",
            name=name,
            labels_file=labels_file,
            labels_df=labels_df,
            epochs=epochs,
            rare_label_value=rare_label_value,
            class_imbalance=class_imbalance,
            webhooks=webhooks,
            **kwargs
        )

    def create_regressor(
        self,
        target_column: str,
        name: Optional[str] = None,
        labels_file: Optional[str] = None,
        labels_df: Optional['pd.DataFrame'] = None,
        epochs: int = 0,
        webhooks: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Predictor:
        """
        Create a regressor predictor from this foundational model.

        Args:
            target_column: Column name to predict
            name: Predictor name (optional)
            labels_file: Path to labels file (optional)
            labels_df: DataFrame with labels (optional)
            epochs: Training epochs (0 = auto)
            webhooks: Webhook URLs for events
            **kwargs: Additional training parameters

        Returns:
            Predictor object (training started)
        """
        return self._create_predictor(
            target_column=target_column,
            target_type="numeric",
            name=name,
            labels_file=labels_file,
            labels_df=labels_df,
            epochs=epochs,
            webhooks=webhooks,
            **kwargs
        )

    def _create_predictor(
        self,
        target_column: str,
        target_type: str,
        name: Optional[str] = None,
        labels_file: Optional[str] = None,
        labels_df: Optional['pd.DataFrame'] = None,
        epochs: int = 0,
        rare_label_value: Optional[str] = None,
        class_imbalance: Optional[Dict[str, float]] = None,
        webhooks: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Predictor:
        """Internal method to create predictor."""
        if not self._ctx:
            raise ValueError("FoundationalModel not connected to client")

        # If labels file provided, use the file upload endpoint
        if labels_file or labels_df is not None:
            return self._create_predictor_with_labels(
                target_column=target_column,
                target_type=target_type,
                labels_file=labels_file,
                labels_df=labels_df,
                epochs=epochs,
                rare_label_value=rare_label_value,
                class_imbalance=class_imbalance,
                webhooks=webhooks,
                **kwargs
            )

        # Use simple endpoint (train on existing session data)
        data = {
            "target_column": target_column,
            "target_column_type": target_type,
            "epochs": epochs,
        }
        if rare_label_value:
            data["rare_label_value"] = rare_label_value
        if class_imbalance:
            data["class_imbalance"] = class_imbalance
        if webhooks:
            data["webhooks"] = webhooks
        data.update(kwargs)

        response = self._ctx.post_json(
            f"/compute/session/{self.id}/train_predictor",
            data=data
        )

        predictor = Predictor(
            id=response.get('predictor_id', ''),
            session_id=self.id,
            target_column=target_column,
            target_type=target_type,
            name=name,
            status="training",
            _ctx=self._ctx,
            _foundational_model=self,
        )

        return predictor

    def _create_predictor_with_labels(
        self,
        target_column: str,
        target_type: str,
        labels_file: Optional[str] = None,
        labels_df: Optional['pd.DataFrame'] = None,
        epochs: int = 0,
        rare_label_value: Optional[str] = None,
        class_imbalance: Optional[Dict[str, float]] = None,
        webhooks: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Predictor:
        """Create predictor with separate labels file."""
        import io
        import gzip

        # Prepare the labels data
        if labels_df is not None:
            # Convert DataFrame to CSV bytes
            csv_buffer = io.StringIO()
            labels_df.to_csv(csv_buffer, index=False)
            file_content = csv_buffer.getvalue().encode('utf-8')
            filename = "labels.csv"
        elif labels_file:
            with open(labels_file, 'rb') as f:
                file_content = f.read()
            filename = labels_file.split('/')[-1]
        else:
            raise ValueError("Either labels_file or labels_df must be provided")

        # Compress if large
        if len(file_content) > 100_000:
            compressed = gzip.compress(file_content)
            if len(compressed) < len(file_content):
                file_content = compressed
                filename = filename + '.gz'

        # Build form data
        form_data = {
            "target_column": target_column,
            "target_column_type": target_type,
            "epochs": str(epochs),
        }
        if rare_label_value:
            form_data["rare_label_value"] = rare_label_value
        if class_imbalance:
            import json
            form_data["class_imbalance"] = json.dumps(class_imbalance)
        if webhooks:
            import json
            form_data["webhooks"] = json.dumps(webhooks)

        files = {
            "file": (filename, file_content)
        }

        response = self._ctx.post_multipart(
            f"/compute/session/{self.id}/train_predictor",
            data=form_data,
            files=files
        )

        return Predictor(
            id=response.get('predictor_id', ''),
            session_id=self.id,
            target_column=target_column,
            target_type=target_type,
            status="training",
            _ctx=self._ctx,
            _foundational_model=self,
        )

    def create_vector_database(
        self,
        name: Optional[str] = None,
        records: Optional[Union[List[Dict[str, Any]], 'pd.DataFrame']] = None
    ) -> VectorDatabase:
        """
        Create a vector database from this foundational model.

        Args:
            name: Database name
            records: Initial records to add (optional)

        Returns:
            VectorDatabase object

        Example:
            vdb = fm.create_vector_database(
                name="customer_search",
                records=customer_records
            )
            similar = vdb.similarity_search({"age": 35}, k=5)
        """
        vdb = VectorDatabase.from_session(
            session_id=self.id,
            name=name,
            ctx=self._ctx,
            foundational_model=self,
        )

        # Add initial records if provided
        if records is not None:
            vdb.add_records(records)

        return vdb

    def create_reference_record(
        self,
        record: Dict[str, Any],
        name: Optional[str] = None
    ) -> ReferenceRecord:
        """
        Create a reference record from a specific record for similarity search.

        A reference record is a reference point in the embedding space that you can use
        to find similar records. Particularly useful when you only have a positive
        class but no negative class - just find more records like the positive example.

        Args:
            record: The record to create a reference from
            name: Optional name for the reference record

        Returns:
            ReferenceRecord object that can be used for similarity search

        Example:
            # Create a reference record from a high-value customer
            ref = fm.create_reference_record(
                record={"age": 35, "income": 100000, "plan": "premium"},
                name="high_value_customer"
            )

            # Find similar customers
            similar = ref.find_similar(k=10, vector_database=vdb)
        """
        if not self._ctx:
            raise ValueError("FoundationalModel not connected to client")

        return ReferenceRecord.from_record(
            record=record,
            session_id=self.id,
            name=name,
            ctx=self._ctx,
            foundational_model=self,
        )

    def wait_for_training(
        self,
        max_wait_time: int = 3600,
        poll_interval: int = 10,
        show_progress: bool = True
    ) -> 'FoundationalModel':
        """
        Wait for foundational model training to complete.

        Args:
            max_wait_time: Maximum wait time in seconds
            poll_interval: Polling interval in seconds
            show_progress: Print progress updates

        Returns:
            Self (updated with final status)

        Raises:
            TimeoutError: If training doesn't complete in time
            RuntimeError: If training fails
        """
        if not self._ctx:
            raise ValueError("FoundationalModel not connected to client")

        start_time = time.time()
        last_epoch = None
        last_status = None

        while time.time() - start_time < max_wait_time:
            # Get session status
            session_data = self._ctx.get_json(f"/compute/session/{self.id}")
            status = session_data.get('status', 'unknown')
            jobs = session_data.get('jobs', {})

            # Look for ES training job
            es_job = None
            for job_id, job in jobs.items():
                if job.get('job_type') in ('train_embedding_space', 'train_es', 'training'):
                    es_job = job
                    break

            # Get progress info
            current_epoch = None
            total_epochs = None
            if es_job:
                current_epoch = es_job.get('current_epoch') or es_job.get('epoch')
                total_epochs = es_job.get('total_epochs') or es_job.get('epochs')
                job_status = es_job.get('status', status)
            else:
                job_status = status

            # Progress update
            if show_progress:
                elapsed = int(time.time() - start_time)
                if current_epoch != last_epoch or job_status != last_status:
                    if current_epoch and total_epochs:
                        print(f"[{elapsed}s] Training: epoch {current_epoch}/{total_epochs} ({job_status})")
                    else:
                        print(f"[{elapsed}s] Training: {job_status}")
                    last_epoch = current_epoch
                    last_status = job_status

            # Check completion
            if job_status == 'done' or status == 'done':
                self.status = 'done'
                self._update_from_session(session_data)
                if show_progress:
                    print(f"Training complete!")
                    if self.dimensions:
                        print(f"  Dimensions: {self.dimensions}")
                    if self.epochs:
                        print(f"  Epochs: {self.epochs}")
                return self

            elif job_status == 'failed' or status == 'failed':
                error_msg = 'Unknown error'
                if es_job:
                    error_msg = es_job.get('error', error_msg)
                self.status = 'error'
                raise RuntimeError(f"Training failed: {error_msg}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Training did not complete within {max_wait_time}s")

    def encode(
        self,
        records: Union[Dict[str, Any], List[Dict[str, Any]], 'pd.DataFrame']
    ) -> List[List[float]]:
        """
        Encode records to embedding vectors.

        Args:
            records: Single record, list of records, or DataFrame

        Returns:
            List of embedding vectors (as lists of floats)

        Example:
            vectors = fm.encode([
                {"age": 35, "income": 50000},
                {"age": 42, "income": 75000}
            ])
        """
        if not self._ctx:
            raise ValueError("FoundationalModel not connected to client")

        # Normalize input
        if isinstance(records, dict):
            records = [records]
        elif hasattr(records, 'to_dict'):
            records = records.to_dict('records')

        # Clean records
        cleaned = [self._clean_record(r) for r in records]

        response = self._ctx.post_json(
            f"/session/{self.id}/encode_records",
            data={"records": cleaned}
        )

        return response.get('embeddings', [])

    def extend(
        self,
        new_data_file: Optional[str] = None,
        new_data_df: Optional['pd.DataFrame'] = None,
        epochs: Optional[int] = None,
        **kwargs
    ) -> 'FoundationalModel':
        """
        Extend this foundational model with new data.

        Args:
            new_data_file: Path to new data file
            new_data_df: DataFrame with new data
            epochs: Additional training epochs
            **kwargs: Additional parameters

        Returns:
            New FoundationalModel instance (training started)
        """
        if not self._ctx:
            raise ValueError("FoundationalModel not connected to client")

        # This creates a new session with extended data
        # Implementation depends on server API
        raise NotImplementedError("extend() not yet implemented - use create_foundational_model with new data")

    def get_projections(self) -> Dict[str, Any]:
        """Get 2D/3D projections for visualization."""
        if not self._ctx:
            raise ValueError("FoundationalModel not connected to client")

        return self._ctx.get_json(f"/session/{self.id}/projections")

    def get_training_metrics(self) -> Dict[str, Any]:
        """Get training metrics and history."""
        if not self._ctx:
            raise ValueError("FoundationalModel not connected to client")

        return self._ctx.get_json(f"/session/{self.id}/training_metrics")

    def get_model_card(self) -> Dict[str, Any]:
        """Get the model card for this foundational model."""
        if not self._ctx:
            raise ValueError("FoundationalModel not connected to client")

        return self._ctx.get_json(f"/session/{self.id}/model_card")

    def list_predictors(self) -> List[Predictor]:
        """List all predictors for this foundational model."""
        if not self._ctx:
            raise ValueError("FoundationalModel not connected to client")

        response = self._ctx.get_json(f"/session/{self.id}/predictor")
        predictors_data = response.get('predictors', {})

        predictors = []
        for pred_id, pred_info in predictors_data.items():
            pred = Predictor(
                id=pred_id,
                session_id=self.id,
                target_column=pred_info.get('target_column', ''),
                target_type=pred_info.get('target_type', 'set'),
                name=pred_info.get('name'),
                status=pred_info.get('status'),
                accuracy=pred_info.get('accuracy'),
                _ctx=self._ctx,
                _foundational_model=self,
            )
            predictors.append(pred)

        return predictors

    def _update_from_session(self, session_data: Dict[str, Any]) -> None:
        """Update fields from session data."""
        # Try to get model info from various places
        model_info = session_data.get('model_info', {})
        training_stats = session_data.get('training_stats', {})

        self.dimensions = (
            model_info.get('d_model') or
            model_info.get('embedding_dim') or
            session_data.get('d_model')
        )
        self.epochs = (
            training_stats.get('final_epoch') or
            training_stats.get('epochs_trained') or
            session_data.get('epochs')
        )
        self.final_loss = (
            training_stats.get('final_loss') or
            session_data.get('final_loss')
        )

    def _clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a record for API submission."""
        import math

        cleaned = {}
        for key, value in record.items():
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    value = None
            if hasattr(value, 'item'):
                value = value.item()
            cleaned[key] = value
        return cleaned

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'dimensions': self.dimensions,
            'epochs': self.epochs,
            'final_loss': self.final_loss,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        status_str = f", status='{self.status}'" if self.status else ""
        dims_str = f", dims={self.dimensions}" if self.dimensions else ""
        return f"FoundationalModel(id='{self.id}'{status_str}{dims_str})"
