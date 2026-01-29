"""
Featrix Sphere API Client

Transform any CSV into a production-ready ML model in minutes, not months.

The Featrix Sphere API automatically builds neural embedding spaces from your data
and trains high-accuracy predictors without requiring any ML expertise.
Just upload your data, specify what you want to predict, and get a production API endpoint.

TWO API OPTIONS:
----------------

1. NEW Object-Oriented API (recommended for new projects):

    >>> from featrixsphere.api import FeatrixSphere
    >>>
    >>> featrix = FeatrixSphere("http://your-server.com")
    >>>
    >>> # Create foundational model
    >>> fm = featrix.create_foundational_model(
    ...     name="my_model",
    ...     csv_file="data.csv"
    ... )
    >>> fm.wait_for_training()
    >>>
    >>> # Create predictor
    >>> predictor = fm.create_classifier(
    ...     target_column="target",
    ...     name="my_predictor"
    ... )
    >>> predictor.wait_for_training()
    >>>
    >>> # Make predictions
    >>> result = predictor.predict({"feature": "value"})
    >>> print(result.predicted_class)
    >>> print(result.confidence)

2. Classic API (for existing code):

    >>> from featrixsphere import FeatrixSphereClient
    >>> import pandas as pd
    >>>
    >>> client = FeatrixSphereClient("http://your-server.com")
    >>>
    >>> # Upload DataFrame directly
    >>> df = pd.read_csv("data.csv")
    >>> session = client.upload_df_and_create_session(df=df)
    >>>
    >>> # Or upload CSV file directly (with automatic gzip compression)
    >>> session = client.upload_df_and_create_session(file_path="data.csv")
    >>>
    >>> # Train a predictor
    >>> client.train_single_predictor(session.session_id, "target_column", "set")
    >>>
    >>> # Make predictions
    >>> result = client.predict(session.session_id, {"feature": "value"})
    >>> print(result['prediction'])
"""

__version__ = "0.2.6379"
__author__ = "Featrix"
__email__ = "support@featrix.com"
__license__ = "MIT"

from .client import FeatrixSphereClient, SessionInfo, PredictionBatch, PredictionGrid

__all__ = [
    "FeatrixSphereClient",
    "SessionInfo", 
    "PredictionBatch",
    "PredictionGrid",
    "__version__",
] 