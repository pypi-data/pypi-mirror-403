"""
APIEndpoint class for FeatrixSphere API.

Represents a named API endpoint for a predictor with optional API key authentication.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .http_client import ClientContext
    from .predictor import Predictor
    from .prediction_result import PredictionResult

logger = logging.getLogger(__name__)


@dataclass
class APIEndpoint:
    """
    Represents a named API endpoint for a predictor.

    API endpoints allow you to create named, versioned access points for
    predictions with optional API key authentication.

    Attributes:
        id: Endpoint ID
        name: Endpoint name
        predictor_id: Associated predictor ID
        session_id: Parent session ID
        api_key: API key (if configured)
        api_key_created_at: When API key was created
        description: Endpoint description
        url: Full endpoint URL
        created_at: Creation timestamp
        last_used_at: Last usage timestamp
        usage_count: Number of predictions made via this endpoint

    Usage:
        # Create from predictor
        endpoint = predictor.create_api_endpoint(
            name="production_api",
            description="Production endpoint"
        )
        print(f"API Key: {endpoint.api_key}")

        # Make predictions via endpoint
        result = endpoint.predict({"age": 35, "income": 50000})
    """

    id: str
    name: str
    predictor_id: str
    session_id: str
    api_key: Optional[str] = None
    api_key_created_at: Optional[datetime] = None
    description: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0

    # Internal
    _ctx: Optional['ClientContext'] = field(default=None, repr=False)
    _predictor: Optional['Predictor'] = field(default=None, repr=False)

    @classmethod
    def from_response(
        cls,
        response: Dict[str, Any],
        predictor_id: str,
        session_id: str,
        ctx: Optional['ClientContext'] = None,
        predictor: Optional['Predictor'] = None
    ) -> 'APIEndpoint':
        """Create APIEndpoint from API response."""
        return cls(
            id=response.get('endpoint_id') or response.get('id', ''),
            name=response.get('name', ''),
            predictor_id=predictor_id,
            session_id=session_id,
            api_key=response.get('api_key'),
            api_key_created_at=datetime.fromisoformat(response['api_key_created_at'])
                if response.get('api_key_created_at') else None,
            description=response.get('description'),
            url=response.get('url') or response.get('endpoint_url'),
            created_at=datetime.fromisoformat(response['created_at'])
                if response.get('created_at') else datetime.now(),
            last_used_at=datetime.fromisoformat(response['last_used_at'])
                if response.get('last_used_at') else None,
            usage_count=response.get('usage_count', 0),
            _ctx=ctx,
            _predictor=predictor,
        )

    @property
    def predictor(self) -> Optional['Predictor']:
        """Get the associated predictor."""
        return self._predictor

    def predict(
        self,
        record: Dict[str, Any],
        api_key: Optional[str] = None
    ) -> 'PredictionResult':
        """
        Make a prediction via this endpoint.

        Args:
            record: Input record dictionary
            api_key: Override endpoint API key

        Returns:
            PredictionResult with prediction, confidence, and prediction_uuid

        Example:
            result = endpoint.predict(
                {"age": 35, "income": 50000},
                api_key="sk_live_abc123"  # Optional if endpoint has key
            )
            print(result.predicted_class)
        """
        if not self._ctx:
            raise ValueError("APIEndpoint not connected to client")

        from .prediction_result import PredictionResult

        # Clean the record
        cleaned_record = self._clean_record(record)

        # Build request with API key if provided
        headers = {}
        key_to_use = api_key or self.api_key
        if key_to_use:
            headers['X-API-Key'] = key_to_use

        # Make request to endpoint
        request_payload = {
            "query_record": cleaned_record,
            "predictor_id": self.predictor_id,
            "endpoint_id": self.id,
        }

        response = self._ctx.post_json(
            f"/session/{self.session_id}/predict",
            data=request_payload,
            headers=headers
        )

        # Update usage stats
        self.usage_count += 1
        self.last_used_at = datetime.now()

        return PredictionResult.from_response(response, cleaned_record, self._ctx)

    def regenerate_api_key(self) -> str:
        """
        Regenerate the API key for this endpoint.

        Returns:
            The new API key

        Example:
            new_key = endpoint.regenerate_api_key()
            print(f"New API Key: {new_key}")
        """
        if not self._ctx:
            raise ValueError("APIEndpoint not connected to client")

        response = self._ctx.post_json(
            f"/session/{self.session_id}/endpoint/{self.id}/regenerate_key",
            data={}
        )

        self.api_key = response.get('api_key')
        self.api_key_created_at = datetime.now()

        return self.api_key or ""

    def revoke_api_key(self) -> None:
        """
        Revoke/remove the API key (endpoint becomes public).

        Example:
            endpoint.revoke_api_key()  # Endpoint now allows unauthenticated access
        """
        if not self._ctx:
            raise ValueError("APIEndpoint not connected to client")

        self._ctx.post_json(
            f"/session/{self.session_id}/endpoint/{self.id}/revoke_key",
            data={}
        )

        self.api_key = None
        self.api_key_created_at = None

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for this endpoint.

        Returns:
            Dictionary with usage statistics

        Example:
            stats = endpoint.get_usage_stats()
            print(f"Total predictions: {stats['usage_count']}")
            print(f"Last used: {stats['last_used_at']}")
        """
        if not self._ctx:
            raise ValueError("APIEndpoint not connected to client")

        try:
            response = self._ctx.get_json(
                f"/session/{self.session_id}/endpoint/{self.id}/stats"
            )

            self.usage_count = response.get('usage_count', self.usage_count)
            if response.get('last_used_at'):
                self.last_used_at = datetime.fromisoformat(response['last_used_at'])

            return response
        except Exception:
            # Return cached values if endpoint doesn't exist yet
            return {
                'endpoint_id': self.id,
                'usage_count': self.usage_count,
                'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            }

    def delete(self) -> None:
        """
        Delete this endpoint.

        Example:
            endpoint.delete()  # Endpoint is now deleted
        """
        if not self._ctx:
            raise ValueError("APIEndpoint not connected to client")

        self._ctx.delete_json(
            f"/session/{self.session_id}/endpoint/{self.id}"
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
            'predictor_id': self.predictor_id,
            'session_id': self.session_id,
            'api_key': self.api_key,
            'api_key_created_at': self.api_key_created_at.isoformat()
                if self.api_key_created_at else None,
            'description': self.description,
            'url': self.url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'usage_count': self.usage_count,
        }

    def __repr__(self) -> str:
        key_str = ", has_key=True" if self.api_key else ""
        return f"APIEndpoint(id='{self.id}', name='{self.name}'{key_str})"
