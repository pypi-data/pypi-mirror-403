"""
VectorDatabase class for FeatrixSphere API.

Represents a vector database for similarity search operations.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .http_client import ClientContext
    from .foundational_model import FoundationalModel
    import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class VectorDatabase:
    """
    Represents a vector database for similarity search.

    Attributes:
        id: Vector database ID (same as session_id)
        name: Database name
        session_id: Parent session ID
        record_count: Number of records in database
        created_at: Creation timestamp

    Usage:
        # Create from foundational model
        vdb = fm.create_vector_database(
            name="customer_search",
            records=customer_records
        )

        # Similarity search
        similar = vdb.similarity_search(
            {"age": 35, "income": 50000},
            k=5
        )

        # Add more records
        vdb.add_records(new_customers)
    """

    id: str
    session_id: str
    name: Optional[str] = None
    record_count: int = 0
    created_at: Optional[datetime] = None

    # Internal
    _ctx: Optional['ClientContext'] = field(default=None, repr=False)
    _foundational_model: Optional['FoundationalModel'] = field(default=None, repr=False)

    @classmethod
    def from_session(
        cls,
        session_id: str,
        name: Optional[str] = None,
        ctx: Optional['ClientContext'] = None,
        foundational_model: Optional['FoundationalModel'] = None
    ) -> 'VectorDatabase':
        """Create VectorDatabase from session ID."""
        vdb = cls(
            id=session_id,
            session_id=session_id,
            name=name,
            created_at=datetime.now(),
            _ctx=ctx,
            _foundational_model=foundational_model,
        )

        # Try to get record count
        if ctx:
            try:
                size = ctx.get_json(f"/session/{session_id}/vectordb_size")
                vdb.record_count = size.get('size', 0)
            except Exception:
                pass

        return vdb

    @property
    def foundational_model(self) -> Optional['FoundationalModel']:
        """Get the parent foundational model."""
        return self._foundational_model

    def similarity_search(
        self,
        query_record: Dict[str, Any],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find k most similar records to the query.

        Args:
            query_record: Query record dictionary
            k: Number of similar records to return

        Returns:
            List of similar records with similarity scores

        Example:
            similar = vdb.similarity_search(
                {"age": 35, "income": 50000},
                k=5
            )
            for record in similar:
                print(f"Score: {record['similarity']}")
                print(f"Data: {record['record']}")
        """
        if not self._ctx:
            raise ValueError("VectorDatabase not connected to client")

        cleaned_query = self._clean_record(query_record)

        response = self._ctx.post_json(
            f"/session/{self.session_id}/similarity_search",
            data={
                "query_record": cleaned_query,
                "k": k
            }
        )

        return response.get('similar_records', response.get('results', []))

    def add_records(
        self,
        records: Union[List[Dict[str, Any]], 'pd.DataFrame'],
        batch_size: int = 500
    ) -> 'VectorDatabase':
        """
        Add records to the vector database.

        Args:
            records: List of record dictionaries or DataFrame
            batch_size: Batch size for adding records

        Returns:
            Self (updated record count)
        """
        if not self._ctx:
            raise ValueError("VectorDatabase not connected to client")

        # Convert DataFrame to list if needed
        if hasattr(records, 'to_dict'):
            records = records.to_dict('records')

        # Clean records
        cleaned_records = [self._clean_record(r) for r in records]

        # Add in batches
        total_added = 0
        for i in range(0, len(cleaned_records), batch_size):
            batch = cleaned_records[i:i + batch_size]

            response = self._ctx.post_json(
                f"/session/{self.session_id}/add_records",
                data={"records": batch}
            )

            added = response.get('added', len(batch))
            total_added += added

        self.record_count += total_added
        return self

    def remove_records(
        self,
        record_ids: List[str]
    ) -> 'VectorDatabase':
        """
        Remove records from the vector database by ID.

        Args:
            record_ids: List of record IDs to remove

        Returns:
            Self (updated record count)

        Note:
            This operation may not be supported by all backends.
        """
        if not self._ctx:
            raise ValueError("VectorDatabase not connected to client")

        # This endpoint may not exist yet - placeholder for future
        try:
            response = self._ctx.post_json(
                f"/session/{self.session_id}/remove_records",
                data={"record_ids": record_ids}
            )
            removed = response.get('removed', len(record_ids))
            self.record_count = max(0, self.record_count - removed)
        except Exception as e:
            logger.warning(f"remove_records not supported: {e}")

        return self

    def size(self) -> int:
        """Get the current number of records in the database."""
        if not self._ctx:
            raise ValueError("VectorDatabase not connected to client")

        response = self._ctx.get_json(f"/session/{self.session_id}/vectordb_size")
        self.record_count = response.get('size', 0)
        return self.record_count

    def encode(
        self,
        records: Union[Dict[str, Any], List[Dict[str, Any]], 'pd.DataFrame']
    ) -> List[List[float]]:
        """
        Encode records to embedding vectors.

        Args:
            records: Single record, list of records, or DataFrame

        Returns:
            List of embedding vectors
        """
        if not self._ctx:
            raise ValueError("VectorDatabase not connected to client")

        # Normalize input to list
        if isinstance(records, dict):
            records = [records]
        elif hasattr(records, 'to_dict'):
            records = records.to_dict('records')

        cleaned_records = [self._clean_record(r) for r in records]

        response = self._ctx.post_json(
            f"/session/{self.session_id}/encode_records",
            data={"records": cleaned_records}
        )

        return response.get('embeddings', [])

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
            'session_id': self.session_id,
            'name': self.name,
            'record_count': self.record_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"VectorDatabase(id='{self.id}', name='{self.name}', records={self.record_count})"
