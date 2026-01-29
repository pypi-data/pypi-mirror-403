"""
FeatrixSphere New API

A clean, object-oriented API for interacting with FeatrixSphere.

Usage:
    from featrixsphere.api import FeatrixSphere

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
"""

from .client import FeatrixSphere
from .foundational_model import FoundationalModel
from .predictor import Predictor
from .prediction_result import PredictionResult, PredictionFeedback
from .vector_database import VectorDatabase
from .reference_record import ReferenceRecord
from .api_endpoint import APIEndpoint
from .notebook_helper import FeatrixNotebookHelper

__all__ = [
    'FeatrixSphere',
    'FoundationalModel',
    'Predictor',
    'PredictionResult',
    'PredictionFeedback',
    'VectorDatabase',
    'ReferenceRecord',
    'APIEndpoint',
    'FeatrixNotebookHelper',
]
