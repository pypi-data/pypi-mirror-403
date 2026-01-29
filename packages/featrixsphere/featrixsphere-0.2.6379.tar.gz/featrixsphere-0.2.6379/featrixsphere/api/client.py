"""
FeatrixSphere main client class.

This is the entry point for the new FeatrixSphere API.
"""

import io
import gzip
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

from .http_client import HTTPClientMixin, ClientContext
from .foundational_model import FoundationalModel
from .predictor import Predictor
from .vector_database import VectorDatabase
from .prediction_result import PredictionFeedback
from .api_endpoint import APIEndpoint
from .notebook_helper import FeatrixNotebookHelper

logger = logging.getLogger(__name__)


class FeatrixSphere(HTTPClientMixin):
    """
    Main client for interacting with FeatrixSphere.

    This is the entry point for the new object-oriented API.

    Usage:
        from featrixsphere.api import FeatrixSphere

        # Connect to FeatrixSphere
        featrix = FeatrixSphere("https://sphere-api.featrix.com")

        # Create foundational model
        fm = featrix.create_foundational_model(
            name="my_model",
            csv_file="data.csv"
        )
        fm.wait_for_training()

        # Create predictor
        predictor = fm.create_classifier(
            name="my_classifier",
            target_column="target"
        )
        predictor.wait_for_training()

        # Make predictions
        result = predictor.predict({"feature1": "value1"})
        print(result.predicted_class)
        print(result.confidence)

    On-Premises Deployment:
        Featrix offers on-premises data processing with qualified NVIDIA
        hardware configurations. The API works exactly the same - just
        point your client to your on-premises endpoint:

        featrix = FeatrixSphere("https://your-on-premises-server.com")
    """

    def __init__(
        self,
        base_url: str = "https://sphere-api.featrix.com",
        compute_cluster: Optional[str] = None,
        default_max_retries: int = 5,
        default_timeout: int = 30,
        retry_base_delay: float = 2.0,
        retry_max_delay: float = 60.0,
    ):
        """
        Initialize the FeatrixSphere client.

        Args:
            base_url: API server URL
            compute_cluster: Compute cluster name (e.g., "burrito", "churro")
            default_max_retries: Default retry count for failed requests
            default_timeout: Default request timeout in seconds
            retry_base_delay: Base delay for exponential backoff
            retry_max_delay: Maximum delay for exponential backoff
        """
        self._base_url = base_url.rstrip('/')
        self._session = requests.Session()
        self._session.timeout = default_timeout

        # Set User-Agent
        try:
            from featrixsphere import __version__
            self._session.headers.update({'User-Agent': f'FeatrixSphere {__version__}'})
        except ImportError:
            self._session.headers.update({'User-Agent': 'FeatrixSphere'})

        # Compute cluster
        self._compute_cluster = compute_cluster
        if compute_cluster:
            self._session.headers.update({'X-Featrix-Node': compute_cluster})

        # Retry config
        self._default_max_retries = default_max_retries
        self._retry_base_delay = retry_base_delay
        self._retry_max_delay = retry_max_delay

        # Client context for resource classes
        self._ctx = ClientContext(self)

    def set_compute_cluster(self, cluster: Optional[str]) -> None:
        """
        Set the compute cluster for all subsequent requests.

        Args:
            cluster: Cluster name or None for default
        """
        self._compute_cluster = cluster
        if cluster:
            self._session.headers.update({'X-Featrix-Node': cluster})
        else:
            self._session.headers.pop('X-Featrix-Node', None)

    def create_foundational_model(
        self,
        name: Optional[str] = None,
        csv_file: Optional[str] = None,
        df: Optional['pd.DataFrame'] = None,
        ignore_columns: Optional[List[str]] = None,
        epochs: Optional[int] = None,
        webhooks: Optional[Dict[str, str]] = None,
        user_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> FoundationalModel:
        """
        Create a foundational model (embedding space).

        Args:
            name: Model name
            csv_file: Path to CSV file with training data
            df: DataFrame with training data (alternative to csv_file)
            ignore_columns: Columns to ignore during training
            epochs: Number of training epochs (None = auto)
            webhooks: Webhook URLs for events
            user_metadata: Custom metadata (max 32KB)
            **kwargs: Additional parameters

        Returns:
            FoundationalModel object (training started)

        Example:
            fm = featrix.create_foundational_model(
                name="customer_embeddings",
                csv_file="customers.csv",
                ignore_columns=["id", "timestamp"]
            )
            fm.wait_for_training()
        """
        # Prepare file content
        if df is not None:
            file_content, filename = self._dataframe_to_file(df)
        elif csv_file:
            file_content, filename = self._read_file(csv_file)
        else:
            raise ValueError("Either csv_file or df must be provided")

        # Build form data
        form_data = {}
        if name:
            form_data['name'] = name
        if ignore_columns:
            import json
            form_data['ignore_columns'] = json.dumps(ignore_columns)
        if epochs is not None:
            form_data['epochs'] = str(epochs)
        if webhooks:
            import json
            form_data['webhooks'] = json.dumps(webhooks)
        if user_metadata:
            import json
            form_data['user_metadata'] = json.dumps(user_metadata)

        # Add any extra kwargs
        for key, value in kwargs.items():
            if value is not None:
                if isinstance(value, (dict, list)):
                    import json
                    form_data[key] = json.dumps(value)
                else:
                    form_data[key] = str(value)

        # Upload file and create session
        files = {'file': (filename, file_content)}

        response = self._post_multipart(
            "/compute/upload_with_new_session/",
            data=form_data,
            files=files
        )

        session_id = response.get('session_id', '')

        # Handle warnings
        warnings = response.get('warnings', [])
        if warnings:
            for warning in warnings:
                logger.warning(f"Upload warning: {warning}")

        return FoundationalModel(
            id=session_id,
            name=name,
            status="training",
            created_at=None,
            _ctx=self._ctx,
        )

    def foundational_model(self, fm_id: str) -> FoundationalModel:
        """
        Get an existing foundational model by ID.

        Args:
            fm_id: Foundational model (session) ID

        Returns:
            FoundationalModel object

        Example:
            fm = featrix.foundational_model("abc123")
            print(fm.status)
        """
        return FoundationalModel.from_session_id(fm_id, self._ctx)

    def predictor(self, predictor_id: str, session_id: Optional[str] = None) -> Predictor:
        """
        Get an existing predictor by ID.

        Args:
            predictor_id: Predictor ID
            session_id: Session ID (required if predictor_id alone is not unique)

        Returns:
            Predictor object

        Note:
            In most cases, you should access predictors through the
            FoundationalModel: fm.list_predictors()
        """
        if not session_id:
            # Try to find session from predictor ID
            # This may not work for all cases
            raise ValueError("session_id is required to load a predictor")

        # Get predictor info from session
        response = self._get_json(f"/session/{session_id}/predictor")
        predictors_data = response.get('predictors', {})

        if predictor_id not in predictors_data:
            raise ValueError(f"Predictor {predictor_id} not found in session {session_id}")

        pred_info = predictors_data[predictor_id]

        return Predictor(
            id=predictor_id,
            session_id=session_id,
            target_column=pred_info.get('target_column', ''),
            target_type=pred_info.get('target_type', 'set'),
            name=pred_info.get('name'),
            status=pred_info.get('status'),
            accuracy=pred_info.get('accuracy'),
            _ctx=self._ctx,
        )

    def vector_database(self, vdb_id: str) -> VectorDatabase:
        """
        Get an existing vector database by ID.

        Args:
            vdb_id: Vector database (session) ID

        Returns:
            VectorDatabase object
        """
        return VectorDatabase.from_session(vdb_id, ctx=self._ctx)

    def api_endpoint(self, endpoint_id: str, session_id: str) -> APIEndpoint:
        """
        Get an existing API endpoint by ID.

        Args:
            endpoint_id: API endpoint ID
            session_id: Session ID

        Returns:
            APIEndpoint object
        """
        response = self._get_json(f"/session/{session_id}/endpoint/{endpoint_id}")

        return APIEndpoint.from_response(
            response=response,
            predictor_id=response.get('predictor_id', ''),
            session_id=session_id,
            ctx=self._ctx,
        )

    def get_notebook(self) -> FeatrixNotebookHelper:
        """
        Get the Jupyter notebook visualization helper.

        Returns a helper object with methods for visualizing training,
        embedding spaces, and model analysis in Jupyter notebooks.

        Returns:
            FeatrixNotebookHelper instance

        Example:
            notebook = featrix.get_notebook()
            fig = notebook.training_loss(fm)
            fig.show()
        """
        return FeatrixNotebookHelper(ctx=self._ctx)

    def prediction_feedback(
        self,
        prediction_uuid: str,
        ground_truth: Union[str, float]
    ) -> Dict[str, Any]:
        """
        Send feedback for a prediction.

        Convenience method that creates and sends feedback in one call.

        Args:
            prediction_uuid: UUID from PredictionResult.prediction_uuid
            ground_truth: The correct label/value

        Returns:
            Server response
        """
        return PredictionFeedback.create_and_send(
            ctx=self._ctx,
            prediction_uuid=prediction_uuid,
            ground_truth=ground_truth
        )

    def health_check(self) -> Dict[str, Any]:
        """
        Check if the API server is healthy.

        Returns:
            Health status dictionary
        """
        return self._get_json("/health")

    def _dataframe_to_file(self, df: 'pd.DataFrame') -> tuple:
        """Convert DataFrame to file content and filename."""
        # Try parquet first (more efficient)
        try:
            import pyarrow
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False)
            return buffer.getvalue(), "data.parquet"
        except ImportError:
            pass

        # Fall back to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        content = csv_buffer.getvalue().encode('utf-8')

        # Compress if large
        if len(content) > 100_000:
            compressed = gzip.compress(content)
            if len(compressed) < len(content):
                return compressed, "data.csv.gz"

        return content, "data.csv"

    def _read_file(self, file_path: str) -> tuple:
        """Read file content and return with filename."""
        path = Path(file_path)
        filename = path.name

        with open(path, 'rb') as f:
            content = f.read()

        # Compress if large and not already compressed
        if len(content) > 100_000 and not filename.endswith('.gz'):
            compressed = gzip.compress(content)
            if len(compressed) < len(content):
                return compressed, filename + '.gz'

        return content, filename

    def __repr__(self) -> str:
        cluster_str = f", cluster='{self._compute_cluster}'" if self._compute_cluster else ""
        return f"FeatrixSphere(url='{self._base_url}'{cluster_str})"
