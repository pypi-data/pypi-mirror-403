"""
PredictionResult and PredictionFeedback classes.

These classes represent prediction results and the feedback mechanism
for improving model accuracy.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .http_client import ClientContext


@dataclass
class PredictionResult:
    """
    Represents a prediction result with full metadata.

    Attributes:
        prediction_uuid: Unique identifier for this prediction (use for feedback)
        prediction: Raw prediction result (class probabilities or numeric value)
        predicted_class: Predicted class name (for classification)
        confidence: Confidence score (for classification)
        query_record: Original input record
        predictor_id: ID of predictor that made this prediction
        session_id: Session ID (internal)
        timestamp: When prediction was made
        target_column: Target column name

    Usage:
        result = predictor.predict({"age": 35, "income": 50000})
        print(result.predicted_class)  # "churned"
        print(result.confidence)       # 0.87
        print(result.prediction_uuid)  # UUID for feedback

        # Send feedback if prediction was wrong
        if result.predicted_class != actual_label:
            feedback = result.send_feedback(ground_truth=actual_label)
            feedback.send()
    """

    prediction_uuid: Optional[str] = None
    prediction: Optional[Union[Dict[str, float], float]] = None
    predicted_class: Optional[str] = None
    confidence: Optional[float] = None
    query_record: Optional[Dict[str, Any]] = None
    predictor_id: Optional[str] = None
    session_id: Optional[str] = None
    target_column: Optional[str] = None
    timestamp: Optional[datetime] = None
    model_version: Optional[str] = None

    # Internal: client context for sending feedback
    _ctx: Optional['ClientContext'] = field(default=None, repr=False)

    @classmethod
    def from_response(
        cls,
        response: Dict[str, Any],
        query_record: Dict[str, Any],
        ctx: Optional['ClientContext'] = None
    ) -> 'PredictionResult':
        """
        Create PredictionResult from API response.

        Args:
            response: API response dictionary
            query_record: Original query record
            ctx: Client context for feedback

        Returns:
            PredictionResult instance
        """
        # Extract prediction data
        prediction = response.get('prediction')
        predicted_class = None
        confidence = None

        # For classification, extract class and confidence
        if isinstance(prediction, dict):
            # Find the class with highest probability
            if prediction:
                predicted_class = max(prediction.keys(), key=lambda k: prediction[k])
                confidence = prediction[predicted_class]

        return cls(
            prediction_uuid=response.get('prediction_uuid') or response.get('prediction_id'),
            prediction=prediction,
            predicted_class=predicted_class,
            confidence=confidence,
            query_record=query_record,
            predictor_id=response.get('predictor_id'),
            session_id=response.get('session_id'),
            target_column=response.get('target_column'),
            timestamp=datetime.now(),
            model_version=response.get('model_version'),
            _ctx=ctx,
        )

    def send_feedback(self, ground_truth: Union[str, float]) -> 'PredictionFeedback':
        """
        Create a feedback object for this prediction.

        Args:
            ground_truth: The correct label/value

        Returns:
            PredictionFeedback object (call .send() to submit)

        Raises:
            ValueError: If prediction_uuid is not available
        """
        if not self.prediction_uuid:
            raise ValueError(
                "Cannot send feedback: prediction_uuid not available. "
                "The server may not have returned a prediction_uuid for this prediction."
            )

        return PredictionFeedback(
            prediction_uuid=self.prediction_uuid,
            ground_truth=ground_truth,
            _ctx=self._ctx,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'prediction_uuid': self.prediction_uuid,
            'prediction': self.prediction,
            'predicted_class': self.predicted_class,
            'confidence': self.confidence,
            'query_record': self.query_record,
            'predictor_id': self.predictor_id,
            'session_id': self.session_id,
            'target_column': self.target_column,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'model_version': self.model_version,
        }


@dataclass
class PredictionFeedback:
    """
    Represents feedback (ground truth) for a prediction.

    Usage:
        # Method 1: From PredictionResult
        result = predictor.predict(record)
        feedback = result.send_feedback(ground_truth="correct_label")
        feedback.send()

        # Method 2: Create directly
        feedback = PredictionFeedback(
            prediction_uuid="123e4567-e89b-12d3-a456-426614174000",
            ground_truth="correct_label"
        )
        feedback.send()

        # Method 3: Create and send in one call
        PredictionFeedback.create_and_send(
            ctx=client_context,
            prediction_uuid="123e4567-...",
            ground_truth="correct_label"
        )
    """

    prediction_uuid: str
    ground_truth: Union[str, float]
    feedback_timestamp: Optional[datetime] = None

    # Internal: client context for sending
    _ctx: Optional['ClientContext'] = field(default=None, repr=False)

    def send(self) -> Dict[str, Any]:
        """
        Submit feedback to the server.

        Returns:
            Server response

        Raises:
            ValueError: If no client context available
        """
        if not self._ctx:
            raise ValueError(
                "Cannot send feedback: no client context. "
                "Create feedback from a PredictionResult or use create_and_send()."
            )

        self.feedback_timestamp = datetime.now()

        response = self._ctx.post_json(
            f"/compute/prediction/{self.prediction_uuid}/update_label",
            data={"user_label": str(self.ground_truth)}
        )
        return response

    @classmethod
    def create_and_send(
        cls,
        ctx: 'ClientContext',
        prediction_uuid: str,
        ground_truth: Union[str, float]
    ) -> Dict[str, Any]:
        """
        Create and send feedback in one call.

        Args:
            ctx: Client context
            prediction_uuid: UUID of the prediction
            ground_truth: Correct label/value

        Returns:
            Server response
        """
        feedback = cls(
            prediction_uuid=prediction_uuid,
            ground_truth=ground_truth,
            _ctx=ctx,
        )
        return feedback.send()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'prediction_uuid': self.prediction_uuid,
            'ground_truth': self.ground_truth,
            'feedback_timestamp': self.feedback_timestamp.isoformat() if self.feedback_timestamp else None,
        }
