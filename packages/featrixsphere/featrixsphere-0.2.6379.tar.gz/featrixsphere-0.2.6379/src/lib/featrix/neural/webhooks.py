# -*- coding: utf-8 -*-
"""
Webhooks module for Featrix Sphere.

Provides async webhook dispatching for training events, alerts, and notifications.
All webhook calls are non-blocking and include automatic retry on failure.
"""

import hmac
import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, Any, List

import requests

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """
    Supported webhook event types.

    These match the events documented in the FeatrixSphere API and can be
    configured per-predictor via configure_webhooks().
    """
    # Training lifecycle
    TRAINING_STARTED = "training_started"
    TRAINING_FINISHED = "training_finished"

    # Alerts
    ALERT_DRIFT = "alert_drift"
    ALERT_PERFORMANCE_DEGRADATION = "alert_performance_degradation"
    ALERT_ERROR_RATE = "alert_error_rate"
    ALERT_QUOTA_THRESHOLD = "alert_quota_threshold"

    # Runtime events
    PREDICTION_ERROR = "prediction_error"
    USAGE = "usage"


@dataclass
class WebhookConfig:
    """
    Webhook configuration for a session/predictor.

    Each field is an optional URL. When an event occurs, if the corresponding
    URL is set, a webhook will be dispatched to that URL.

    Example:
        config = WebhookConfig(
            training_finished="https://api.example.com/webhooks/training",
            alert_drift="https://api.example.com/webhooks/alerts",
            webhook_secret="my_secret_key"
        )
    """
    # Training lifecycle
    training_started: Optional[str] = None
    training_finished: Optional[str] = None

    # Alerts
    alert_drift: Optional[str] = None
    alert_performance_degradation: Optional[str] = None
    alert_error_rate: Optional[str] = None
    alert_quota_threshold: Optional[str] = None

    # Runtime events
    prediction_error: Optional[str] = None
    usage: Optional[str] = None

    # Authentication
    webhook_secret: Optional[str] = None

    def get_url(self, event_type: WebhookEventType) -> Optional[str]:
        """Get the URL configured for an event type."""
        return getattr(self, event_type.value, None)

    def has_webhook(self, event_type: WebhookEventType) -> bool:
        """Check if a webhook is configured for an event type."""
        return bool(self.get_url(event_type))

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary, excluding None values and secret."""
        result = {}
        for event_type in WebhookEventType:
            url = self.get_url(event_type)
            if url:
                result[event_type.value] = url
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookConfig':
        """Create WebhookConfig from dictionary."""
        return cls(
            training_started=data.get('training_started'),
            training_finished=data.get('training_finished'),
            alert_drift=data.get('alert_drift'),
            alert_performance_degradation=data.get('alert_performance_degradation'),
            alert_error_rate=data.get('alert_error_rate'),
            alert_quota_threshold=data.get('alert_quota_threshold'),
            prediction_error=data.get('prediction_error'),
            usage=data.get('usage'),
            webhook_secret=data.get('webhook_secret'),
        )


@dataclass
class WebhookPayload:
    """
    Standardized webhook payload structure.

    All webhooks send this JSON structure:
    {
        "event": "training_finished",
        "timestamp": "2025-01-13T10:30:00Z",
        "foundational_model_id": "abc123",
        "predictor_id": "pred_456",  // may be null
        "data": { ... event-specific data ... }
    }
    """
    event: str
    timestamp: str
    foundational_model_id: str
    data: Dict[str, Any]
    predictor_id: Optional[str] = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), separators=(',', ':'))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class WebhookDispatcher:
    """
    Async webhook dispatcher with HMAC signing and retry support.

    All sends are non-blocking - they spawn a background thread to make
    the HTTP request. Failed webhooks are logged for retry.

    Usage:
        dispatcher = WebhookDispatcher()
        dispatcher.send(
            event_type=WebhookEventType.TRAINING_FINISHED,
            foundational_model_id="abc123",
            predictor_id="pred_456",
            data={"accuracy": 0.94, "epochs": 150},
            config=webhook_config
        )
    """

    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout

    def send(
        self,
        event_type: WebhookEventType,
        foundational_model_id: str,
        data: Dict[str, Any],
        config: WebhookConfig,
        predictor_id: Optional[str] = None,
    ) -> bool:
        """
        Send a webhook asynchronously.

        Args:
            event_type: Type of event
            foundational_model_id: Foundational model ID
            data: Event-specific data payload
            config: Webhook configuration with URLs and secret
            predictor_id: Optional predictor ID

        Returns:
            True if webhook was dispatched (not necessarily delivered),
            False if no webhook URL configured for this event type
        """
        url = config.get_url(event_type)
        if not url:
            logger.debug(f"No webhook URL configured for {event_type.value}")
            return False

        # Build payload
        payload = WebhookPayload(
            event=event_type.value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            foundational_model_id=foundational_model_id,
            predictor_id=predictor_id,
            data=data,
        )

        # Dispatch in background thread
        thread = threading.Thread(
            target=self._send_webhook,
            args=(url, payload, config.webhook_secret, foundational_model_id),
            daemon=True
        )
        thread.start()

        logger.info(f"📤 Dispatched {event_type.value} webhook to {url}")
        return True

    def _send_webhook(
        self,
        url: str,
        payload: WebhookPayload,
        secret: Optional[str],
        foundational_model_id: str,
    ) -> None:
        """
        Actually send the webhook (runs in background thread).

        Handles:
        - HMAC signature if secret provided
        - Error logging
        - Retry queue registration on failure
        """
        payload_json = payload.to_json()
        payload_bytes = payload_json.encode('utf-8')

        # Build headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FeatrixSphere-Webhook/1.0",
        }

        # Add HMAC signature if secret provided
        if secret:
            signature = self._compute_signature(payload_bytes, secret)
            headers["X-Featrix-Signature"] = signature

        try:
            response = requests.post(
                url,
                data=payload_bytes,
                headers=headers,
                timeout=self.timeout,
            )

            if response.status_code == 401:
                logger.error(f"❌ Webhook auth failed (401) for {payload.event}: {url}")
                self._log_failure(url, payload, foundational_model_id, "401 Unauthorized")
                return

            if response.status_code == 403:
                logger.error(f"❌ Webhook forbidden (403) for {payload.event}: {url}")
                self._log_failure(url, payload, foundational_model_id, "403 Forbidden")
                return

            response.raise_for_status()

            logger.info(f"✅ Webhook {payload.event} delivered to {url}")
            self._log_success(url, payload, foundational_model_id, response.status_code)

        except requests.exceptions.Timeout:
            logger.error(f"❌ Webhook timeout for {payload.event}: {url}")
            self._log_failure(url, payload, foundational_model_id, "Timeout")
            self._queue_retry(url, payload, foundational_model_id, "Timeout")

        except requests.exceptions.RequestException as e:
            status = e.response.status_code if hasattr(e, 'response') and e.response else 'N/A'
            logger.error(f"❌ Webhook failed for {payload.event}: {url} (status={status})")
            self._log_failure(url, payload, foundational_model_id, str(e))
            self._queue_retry(url, payload, foundational_model_id, str(e))

        except Exception as e:
            logger.error(f"❌ Unexpected webhook error for {payload.event}: {e}")
            self._log_failure(url, payload, foundational_model_id, str(e))

    def _compute_signature(self, payload_bytes: bytes, secret: str) -> str:
        """
        Compute HMAC-SHA256 signature for webhook payload.

        The signature is returned as "sha256=<hex_digest>".
        Recipients can verify with:
            expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
            valid = hmac.compare_digest(f"sha256={expected}", signature_header)
        """
        digest = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={digest}"

    def _log_success(
        self,
        url: str,
        payload: WebhookPayload,
        session_id: str,
        status_code: int
    ) -> None:
        """Log successful webhook delivery to event log."""
        try:
            from event_log import log_webhook_event
            log_webhook_event(
                session_id=session_id,
                event_name="webhook_sent",
                webhook_url=url,
                additional_info={
                    "event_type": payload.event,
                    "predictor_id": payload.predictor_id,
                    "status_code": status_code,
                }
            )
        except Exception as e:
            logger.debug(f"Failed to log webhook success: {e}")

    def _log_failure(
        self,
        url: str,
        payload: WebhookPayload,
        session_id: str,
        error: str
    ) -> None:
        """Log failed webhook delivery to event log."""
        try:
            from event_log import log_webhook_event
            log_webhook_event(
                session_id=session_id,
                event_name="webhook_failed",
                webhook_url=url,
                additional_info={
                    "event_type": payload.event,
                    "predictor_id": payload.predictor_id,
                    "error": error,
                }
            )
        except Exception as e:
            logger.debug(f"Failed to log webhook failure: {e}")

    def _queue_retry(
        self,
        url: str,
        payload: WebhookPayload,
        session_id: str,
        error: str
    ) -> None:
        """Queue failed webhook for retry."""
        try:
            from lib.api_event_retry import get_retry_manager, EventType
            retry_manager = get_retry_manager()
            retry_manager.log_failed_event(
                event_type=EventType.WEBHOOK,
                url=url,
                method="POST",
                payload=payload.to_dict(),
                timeout=self.timeout,
                error=error,
                metadata={
                    "session_id": session_id,
                    "event_type": payload.event,
                    "predictor_id": payload.predictor_id,
                }
            )
        except Exception as e:
            logger.debug(f"Failed to queue webhook for retry: {e}")


# Global dispatcher instance
_dispatcher: Optional[WebhookDispatcher] = None


def get_dispatcher() -> WebhookDispatcher:
    """Get the global webhook dispatcher instance."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = WebhookDispatcher()
    return _dispatcher


# =============================================================================
# Convenience functions for each event type
# =============================================================================

def send_training_started(
    foundational_model_id: str,
    config: WebhookConfig,
    predictor_id: Optional[str] = None,
    target_column: Optional[str] = None,
    target_type: Optional[str] = None,
    epochs: Optional[int] = None,
) -> bool:
    """
    Send training_started webhook.

    Args:
        foundational_model_id: Foundational model ID
        config: Webhook configuration
        predictor_id: Predictor ID (if training a predictor)
        target_column: Target column being predicted
        target_type: Type of prediction (set, numeric, binary)
        epochs: Planned number of epochs

    Returns:
        True if webhook was dispatched
    """
    data = {}
    if target_column:
        data["target_column"] = target_column
    if target_type:
        data["target_type"] = target_type
    if epochs:
        data["epochs"] = epochs

    return get_dispatcher().send(
        event_type=WebhookEventType.TRAINING_STARTED,
        foundational_model_id=foundational_model_id,
        predictor_id=predictor_id,
        data=data,
        config=config,
    )


def send_training_finished(
    foundational_model_id: str,
    config: WebhookConfig,
    predictor_id: Optional[str] = None,
    status: str = "succeeded",
    metrics: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> bool:
    """
    Send training_finished webhook.

    Args:
        foundational_model_id: Foundational model ID
        config: Webhook configuration
        predictor_id: Predictor ID (if training a predictor)
        status: "succeeded" or "failed"
        metrics: Training metrics (accuracy, auc, f1, epochs, etc.)
        error: Error message if status is "failed"

    Returns:
        True if webhook was dispatched
    """
    data = {"status": status}
    if metrics:
        data["metrics"] = metrics
    if error:
        data["error"] = error

    return get_dispatcher().send(
        event_type=WebhookEventType.TRAINING_FINISHED,
        foundational_model_id=foundational_model_id,
        predictor_id=predictor_id,
        data=data,
        config=config,
    )


def send_drift_alert(
    foundational_model_id: str,
    config: WebhookConfig,
    predictor_id: str,
    drift_score: float,
    threshold: float,
    feature_drifts: Optional[Dict[str, float]] = None,
    sample_size: Optional[int] = None,
) -> bool:
    """
    Send alert_drift webhook when data drift is detected.

    Args:
        foundational_model_id: Foundational model ID
        config: Webhook configuration
        predictor_id: Predictor ID
        drift_score: Overall drift score (0-1)
        threshold: Threshold that was exceeded
        feature_drifts: Per-feature drift scores
        sample_size: Number of predictions in sample

    Returns:
        True if webhook was dispatched
    """
    data = {
        "drift_score": drift_score,
        "threshold": threshold,
        "alert_type": "drift",
    }
    if feature_drifts:
        data["feature_drifts"] = feature_drifts
    if sample_size:
        data["sample_size"] = sample_size

    return get_dispatcher().send(
        event_type=WebhookEventType.ALERT_DRIFT,
        foundational_model_id=foundational_model_id,
        predictor_id=predictor_id,
        data=data,
        config=config,
    )


def send_performance_alert(
    foundational_model_id: str,
    config: WebhookConfig,
    predictor_id: str,
    metric_name: str,
    current_value: float,
    baseline_value: float,
    threshold: float,
) -> bool:
    """
    Send alert_performance_degradation webhook.

    Args:
        foundational_model_id: Foundational model ID
        config: Webhook configuration
        predictor_id: Predictor ID
        metric_name: Name of degraded metric (accuracy, auc, etc.)
        current_value: Current metric value
        baseline_value: Original/baseline metric value
        threshold: Degradation threshold

    Returns:
        True if webhook was dispatched
    """
    data = {
        "metric_name": metric_name,
        "current_value": current_value,
        "baseline_value": baseline_value,
        "degradation": baseline_value - current_value,
        "threshold": threshold,
        "alert_type": "performance_degradation",
    }

    return get_dispatcher().send(
        event_type=WebhookEventType.ALERT_PERFORMANCE_DEGRADATION,
        foundational_model_id=foundational_model_id,
        predictor_id=predictor_id,
        data=data,
        config=config,
    )


def send_error_rate_alert(
    foundational_model_id: str,
    config: WebhookConfig,
    predictor_id: str,
    error_rate: float,
    threshold: float,
    error_count: int,
    total_count: int,
    window_minutes: int = 60,
) -> bool:
    """
    Send alert_error_rate webhook when error rate exceeds threshold.

    Args:
        foundational_model_id: Foundational model ID
        config: Webhook configuration
        predictor_id: Predictor ID
        error_rate: Current error rate (0-1)
        threshold: Threshold that was exceeded
        error_count: Number of errors in window
        total_count: Total predictions in window
        window_minutes: Time window in minutes

    Returns:
        True if webhook was dispatched
    """
    data = {
        "error_rate": error_rate,
        "threshold": threshold,
        "error_count": error_count,
        "total_count": total_count,
        "window_minutes": window_minutes,
        "alert_type": "error_rate",
    }

    return get_dispatcher().send(
        event_type=WebhookEventType.ALERT_ERROR_RATE,
        foundational_model_id=foundational_model_id,
        predictor_id=predictor_id,
        data=data,
        config=config,
    )


def send_quota_alert(
    foundational_model_id: str,
    config: WebhookConfig,
    current_usage: int,
    quota_limit: int,
    usage_percent: float,
    threshold_percent: float = 80.0,
    predictor_id: Optional[str] = None,
) -> bool:
    """
    Send alert_quota_threshold webhook when approaching quota limit.

    Args:
        foundational_model_id: Foundational model ID
        config: Webhook configuration
        current_usage: Current usage count
        quota_limit: Total quota limit
        usage_percent: Current usage as percentage
        threshold_percent: Threshold percentage that triggered alert
        predictor_id: Optional predictor ID

    Returns:
        True if webhook was dispatched
    """
    data = {
        "current_usage": current_usage,
        "quota_limit": quota_limit,
        "usage_percent": usage_percent,
        "threshold_percent": threshold_percent,
        "alert_type": "quota_threshold",
    }

    return get_dispatcher().send(
        event_type=WebhookEventType.ALERT_QUOTA_THRESHOLD,
        foundational_model_id=foundational_model_id,
        predictor_id=predictor_id,
        data=data,
        config=config,
    )


def send_prediction_error(
    foundational_model_id: str,
    config: WebhookConfig,
    predictor_id: str,
    error_type: str,
    error_message: str,
    query_record: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send prediction_error webhook when a prediction fails.

    Args:
        foundational_model_id: Foundational model ID
        config: Webhook configuration
        predictor_id: Predictor ID
        error_type: Type of error (e.g., "ValueError", "TimeoutError")
        error_message: Error message
        query_record: The input that caused the error (sanitized)

    Returns:
        True if webhook was dispatched
    """
    data = {
        "error_type": error_type,
        "error_message": error_message,
    }
    if query_record:
        # Sanitize - don't send full record, just column names
        data["query_columns"] = list(query_record.keys())

    return get_dispatcher().send(
        event_type=WebhookEventType.PREDICTION_ERROR,
        foundational_model_id=foundational_model_id,
        predictor_id=predictor_id,
        data=data,
        config=config,
    )


def send_usage_update(
    foundational_model_id: str,
    config: WebhookConfig,
    predictor_id: str,
    prediction_count: int,
    period: str = "hourly",
    period_start: Optional[str] = None,
) -> bool:
    """
    Send usage webhook with prediction statistics.

    Note: This can be high-frequency. Use sparingly.

    Args:
        foundational_model_id: Foundational model ID
        config: Webhook configuration
        predictor_id: Predictor ID
        prediction_count: Number of predictions in period
        period: Period type ("hourly", "daily", etc.)
        period_start: ISO timestamp of period start

    Returns:
        True if webhook was dispatched
    """
    data = {
        "prediction_count": prediction_count,
        "period": period,
    }
    if period_start:
        data["period_start"] = period_start

    return get_dispatcher().send(
        event_type=WebhookEventType.USAGE,
        foundational_model_id=foundational_model_id,
        predictor_id=predictor_id,
        data=data,
        config=config,
    )
