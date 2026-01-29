"""
Predictor class for FeatrixSphere API.

Represents a trained predictor (classifier or regressor).
"""

import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .http_client import ClientContext
    from .foundational_model import FoundationalModel
    import pandas as pd

from .prediction_result import PredictionResult
from .api_endpoint import APIEndpoint

logger = logging.getLogger(__name__)


@dataclass
class Predictor:
    """
    Represents a trained predictor (classifier or regressor).

    Attributes:
        id: Predictor ID
        name: Predictor name
        target_column: Target column name
        target_type: Target type ("set", "numeric", "binary")
        status: Training status ("training", "done", "error")
        session_id: Parent session ID
        accuracy: Training accuracy (if available)
        created_at: Creation timestamp

    Usage:
        # Create from foundational model
        predictor = fm.create_classifier(
            name="churn_predictor",
            target_column="churned"
        )

        # Wait for training
        predictor.wait_for_training()

        # Make prediction
        result = predictor.predict({"age": 35, "income": 50000})
        print(result.predicted_class)
        print(result.confidence)

        # Batch predictions
        results = predictor.batch_predict([
            {"age": 35, "income": 50000},
            {"age": 42, "income": 75000}
        ])
    """

    id: str
    session_id: str
    target_column: str
    target_type: str = "set"
    name: Optional[str] = None
    status: Optional[str] = None
    accuracy: Optional[float] = None
    auc: Optional[float] = None
    f1: Optional[float] = None
    created_at: Optional[datetime] = None

    # Internal
    _ctx: Optional['ClientContext'] = field(default=None, repr=False)
    _foundational_model: Optional['FoundationalModel'] = field(default=None, repr=False)

    @classmethod
    def from_response(
        cls,
        response: Dict[str, Any],
        session_id: str,
        ctx: Optional['ClientContext'] = None,
        foundational_model: Optional['FoundationalModel'] = None
    ) -> 'Predictor':
        """Create Predictor from API response."""
        return cls(
            id=response.get('predictor_id') or response.get('id', ''),
            session_id=session_id,
            target_column=response.get('target_column', ''),
            target_type=response.get('target_type') or response.get('target_column_type', 'set'),
            name=response.get('name'),
            status=response.get('status'),
            accuracy=response.get('accuracy'),
            auc=response.get('auc') or response.get('roc_auc'),
            f1=response.get('f1') or response.get('f1_score'),
            created_at=datetime.now(),
            _ctx=ctx,
            _foundational_model=foundational_model,
        )

    @property
    def foundational_model(self) -> Optional['FoundationalModel']:
        """Get the parent foundational model."""
        return self._foundational_model

    def predict(
        self,
        record: Dict[str, Any],
        best_metric_preference: Optional[str] = None
    ) -> PredictionResult:
        """
        Make a single prediction.

        Args:
            record: Input record dictionary
            best_metric_preference: Metric checkpoint to use ("roc_auc", "pr_auc", or None)

        Returns:
            PredictionResult with prediction, confidence, and prediction_uuid

        Example:
            result = predictor.predict({"age": 35, "income": 50000})
            print(result.predicted_class)  # "churned"
            print(result.confidence)       # 0.87
            print(result.prediction_uuid)  # UUID for feedback
        """
        if not self._ctx:
            raise ValueError("Predictor not connected to client")

        # Clean the record
        cleaned_record = self._clean_record(record)

        # Build request
        request_payload = {
            "query_record": cleaned_record,
            "predictor_id": self.id,
        }
        if best_metric_preference:
            request_payload["best_metric_preference"] = best_metric_preference

        # Make request
        response = self._ctx.post_json(
            f"/session/{self.session_id}/predict",
            data=request_payload
        )

        return PredictionResult.from_response(response, cleaned_record, self._ctx)

    def batch_predict(
        self,
        records: Union[List[Dict[str, Any]], 'pd.DataFrame'],
        show_progress: bool = True,
        best_metric_preference: Optional[str] = None
    ) -> List[PredictionResult]:
        """
        Make batch predictions.

        Args:
            records: List of record dictionaries or DataFrame
            show_progress: Show progress bar
            best_metric_preference: Metric checkpoint to use

        Returns:
            List of PredictionResult objects
        """
        if not self._ctx:
            raise ValueError("Predictor not connected to client")

        # Convert DataFrame to list of dicts if needed
        if hasattr(records, 'to_dict'):
            records = records.to_dict('records')

        # Clean records
        cleaned_records = [self._clean_record(r) for r in records]

        # Build request
        request_payload = {
            "records": cleaned_records,
            "predictor_id": self.id,
        }
        if best_metric_preference:
            request_payload["best_metric_preference"] = best_metric_preference

        # Make request using predict_table endpoint
        response = self._ctx.post_json(
            f"/session/{self.session_id}/predict_table",
            data={"table": {"rows": cleaned_records}, "predictor_id": self.id}
        )

        # Parse results
        results = []
        predictions = response.get('predictions', [])

        for i, pred in enumerate(predictions):
            record = cleaned_records[i] if i < len(cleaned_records) else {}
            results.append(PredictionResult.from_response(pred, record, self._ctx))

        return results

    def explain(
        self,
        record: Dict[str, Any],
        class_idx: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Explain a prediction using gradient attribution.

        Args:
            record: Input record to explain
            class_idx: Class index to explain (for multi-class)

        Returns:
            Explanation dictionary with feature attributions
        """
        if not self._ctx:
            raise ValueError("Predictor not connected to client")

        cleaned_record = self._clean_record(record)

        request_payload = {
            "query_record": cleaned_record,
            "predictor_id": self.id,
        }
        if class_idx is not None:
            request_payload["class_idx"] = class_idx

        return self._ctx.post_json(
            f"/session/{self.session_id}/explain",
            data=request_payload
        )

    def wait_for_training(
        self,
        max_wait_time: int = 3600,
        poll_interval: int = 10,
        show_progress: bool = True
    ) -> 'Predictor':
        """
        Wait for predictor training to complete.

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
            raise ValueError("Predictor not connected to client")

        start_time = time.time()
        last_status = None

        while time.time() - start_time < max_wait_time:
            # Get session status
            session_data = self._ctx.get_json(f"/compute/session/{self.session_id}")
            jobs = session_data.get('jobs', {})

            # Find our predictor's job
            predictor_job = None
            for job_id, job in jobs.items():
                if job.get('job_type') == 'train_single_predictor':
                    job_target = job.get('target_column')
                    if job_target == self.target_column:
                        predictor_job = job
                        break

            if predictor_job:
                status = predictor_job.get('status', 'unknown')

                if status != last_status and show_progress:
                    elapsed = int(time.time() - start_time)
                    print(f"[{elapsed}s] Predictor training: {status}")
                    last_status = status

                if status == 'done':
                    self.status = 'done'
                    # Try to get metrics
                    self._update_metrics()
                    if show_progress:
                        print(f"Predictor training complete!")
                        if self.accuracy:
                            print(f"  Accuracy: {self.accuracy:.4f}")
                        if self.auc:
                            print(f"  AUC: {self.auc:.4f}")
                    return self

                elif status == 'failed':
                    error_msg = predictor_job.get('error', 'Unknown error')
                    self.status = 'error'
                    raise RuntimeError(f"Predictor training failed: {error_msg}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Predictor training did not complete within {max_wait_time}s")

    def train_more(
        self,
        epochs: int = 50,
        **kwargs
    ) -> 'Predictor':
        """
        Continue training the predictor.

        Args:
            epochs: Additional epochs to train
            **kwargs: Additional training parameters

        Returns:
            Self (training started)
        """
        if not self._ctx:
            raise ValueError("Predictor not connected to client")

        data = {
            "epochs": epochs,
            "target_column": self.target_column,
            **kwargs
        }

        self._ctx.post_json(
            f"/compute/session/{self.session_id}/train_predictor_more",
            data=data
        )

        self.status = "training"
        return self

    def create_api_endpoint(
        self,
        name: str,
        api_key: Optional[str] = None,
        description: Optional[str] = None
    ) -> APIEndpoint:
        """
        Create a named API endpoint for this predictor.

        Args:
            name: Endpoint name
            api_key: API key (if None, auto-generate)
            description: Endpoint description

        Returns:
            APIEndpoint object

        Example:
            endpoint = predictor.create_api_endpoint(
                name="production_api",
                description="Production endpoint"
            )
            print(f"API Key: {endpoint.api_key}")
        """
        if not self._ctx:
            raise ValueError("Predictor not connected to client")

        data = {
            "name": name,
            "predictor_id": self.id,
        }
        if api_key:
            data["api_key"] = api_key
        if description:
            data["description"] = description

        response = self._ctx.post_json(
            f"/session/{self.session_id}/create_endpoint",
            data=data
        )

        return APIEndpoint.from_response(
            response=response,
            predictor_id=self.id,
            session_id=self.session_id,
            ctx=self._ctx,
            predictor=self,
        )

    def configure_webhooks(
        self,
        training_finished: Optional[str] = None,
        training_started: Optional[str] = None,
        alert_drift: Optional[str] = None,
        alert_performance_degradation: Optional[str] = None,
        alert_error_rate: Optional[str] = None,
        alert_quota_threshold: Optional[str] = None,
        prediction_error: Optional[str] = None,
        usage: Optional[str] = None,
        batch_job_completed: Optional[str] = None,
        webhook_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configure webhooks for various predictor events.

        Args:
            training_finished: URL for training completion webhook
            training_started: URL for training start webhook
            alert_drift: URL for data drift alerts
            alert_performance_degradation: URL for performance alerts
            alert_error_rate: URL for error rate alerts
            alert_quota_threshold: URL for quota threshold alerts
            prediction_error: URL for prediction error webhook
            usage: URL for usage statistics (can be spammy!)
            batch_job_completed: URL for batch job completion
            webhook_secret: Secret for webhook verification

        Returns:
            Current webhook configuration

        Example:
            predictor.configure_webhooks(
                training_finished="https://api.example.com/webhooks/training",
                alert_drift="https://api.example.com/webhooks/drift",
                webhook_secret="my_secret_key"
            )
        """
        if not self._ctx:
            raise ValueError("Predictor not connected to client")

        webhooks = {}
        if training_finished:
            webhooks["training_finished"] = training_finished
        if training_started:
            webhooks["training_started"] = training_started
        if alert_drift:
            webhooks["alert_drift"] = alert_drift
        if alert_performance_degradation:
            webhooks["alert_performance_degradation"] = alert_performance_degradation
        if alert_error_rate:
            webhooks["alert_error_rate"] = alert_error_rate
        if alert_quota_threshold:
            webhooks["alert_quota_threshold"] = alert_quota_threshold
        if prediction_error:
            webhooks["prediction_error"] = prediction_error
        if usage:
            webhooks["usage"] = usage
        if batch_job_completed:
            webhooks["batch_job_completed"] = batch_job_completed
        if webhook_secret:
            webhooks["webhook_secret"] = webhook_secret

        response = self._ctx.post_json(
            f"/session/{self.session_id}/configure_webhooks",
            data={"webhooks": webhooks, "predictor_id": self.id}
        )

        return response.get('webhooks', webhooks)

    def get_webhooks(self) -> Dict[str, str]:
        """
        Get current webhook configuration.

        Returns:
            Dictionary of webhook event types to URLs
        """
        if not self._ctx:
            raise ValueError("Predictor not connected to client")

        response = self._ctx.get_json(
            f"/session/{self.session_id}/webhooks"
        )

        return response.get('webhooks', {})

    def disable_webhook(self, event_type: str) -> None:
        """
        Disable a specific webhook event.

        Args:
            event_type: Webhook event type to disable
        """
        if not self._ctx:
            raise ValueError("Predictor not connected to client")

        self._ctx.post_json(
            f"/session/{self.session_id}/disable_webhook",
            data={"event_type": event_type, "predictor_id": self.id}
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get training metrics for this predictor."""
        if not self._ctx:
            raise ValueError("Predictor not connected to client")

        return self._ctx.get_json(f"/session/{self.session_id}/training_metrics")

    def _update_metrics(self) -> None:
        """Update metrics from server."""
        try:
            metrics = self.get_metrics()
            # Look for our predictor's metrics
            sp_metrics = metrics.get('single_predictor', {})
            if sp_metrics:
                self.accuracy = sp_metrics.get('accuracy')
                self.auc = sp_metrics.get('roc_auc') or sp_metrics.get('auc')
                self.f1 = sp_metrics.get('f1') or sp_metrics.get('f1_score')
        except Exception:
            pass  # Metrics may not be available yet

    def _clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a record for API submission."""
        import math

        cleaned = {}
        for key, value in record.items():
            # Handle NaN/Inf
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    value = None
            # Handle numpy types
            if hasattr(value, 'item'):
                value = value.item()
            cleaned[key] = value
        return cleaned

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'target_column': self.target_column,
            'target_type': self.target_type,
            'name': self.name,
            'status': self.status,
            'accuracy': self.accuracy,
            'auc': self.auc,
            'f1': self.f1,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        status_str = f", status='{self.status}'" if self.status else ""
        acc_str = f", accuracy={self.accuracy:.4f}" if self.accuracy else ""
        return f"Predictor(id='{self.id}', target='{self.target_column}'{status_str}{acc_str})"
