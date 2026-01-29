#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#

import logging
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.single_predictor import FeatrixSinglePredictor

logger = logging.getLogger(__name__)

class TrainingState(Enum):
    TRAIN = 100
    EVAL = 222


class PredictorTrainingContextManager:
    """
    Context manager for setting predictor, encoder, and codec training modes.

    This is the CANONICAL way to set training/eval modes for FeatrixSinglePredictor.
    All components (predictor, encoder, codecs) are set together and restored on exit.

    Usage:
        # For training:
        with PredictorTrainingContextManager(fsp, TrainingState.TRAIN, TrainingState.TRAIN):
            # training code here

        # For inference/validation:
        with PredictorEvalModeContextManager(fsp):
            # inference code here
    """

    def __init__(self,
                 fsp: "FeatrixSinglePredictor",
                 predictor_mode: TrainingState,
                 encoder_mode: TrainingState,
                 debugLabel=None):

        # Use predictor if available, otherwise fall back to predictor_base
        # This handles cases where predictor might be None (e.g., when loaded from pickle)
        predictor = getattr(fsp, 'predictor', None)
        if predictor is None:
            predictor = getattr(fsp, 'predictor_base', None)
            if predictor is None:
                raise AttributeError(
                    f"FeatrixSinglePredictor has neither 'predictor' nor 'predictor_base' attribute. "
                    f"The model may not be properly initialized. Did you call prep_for_training()?"
                )

        es_encoder = fsp.embedding_space.encoder
        assert es_encoder is not None

        self.predictor = predictor
        self.es_encoder = es_encoder
        self.fsp = fsp  # Keep reference for codec access

        self.predictor_mode = predictor_mode
        self.encoder_mode = encoder_mode

        self.was_training_predictor = None
        self.was_training_encoder = None
        self.was_training_codecs = {}  # Track codec states

        self._debugLabel = debugLabel or ""


    def __enter__(self):
        self.was_training_predictor = self.predictor.training
        self.was_training_encoder = self.es_encoder.training

        # Set encoder mode
        if self.encoder_mode == TrainingState.TRAIN:
            self.es_encoder.train()
        else:
            self.es_encoder.eval()

        # Set predictor mode
        if self.predictor_mode == TrainingState.TRAIN:
            self.predictor.train()
        else:
            self.predictor.eval()

        # CRITICAL: Also set codecs to the same mode as encoder
        # Codecs (ScalarCodec, StringCodec, SetCodec) have MLPs with dropout
        # that must be in eval mode for deterministic predictions
        col_codecs = getattr(self.fsp.embedding_space, 'col_codecs', None)
        if col_codecs:
            for col_name, codec in col_codecs.items():
                if codec is not None and hasattr(codec, 'training'):
                    self.was_training_codecs[col_name] = codec.training
                    if self.encoder_mode == TrainingState.TRAIN:
                        codec.train()
                    else:
                        codec.eval()

        # Verify modes were set correctly
        expected_predictor = (self.predictor_mode == TrainingState.TRAIN)
        expected_encoder = (self.encoder_mode == TrainingState.TRAIN)

        assert self.predictor.training == expected_predictor, \
            f"❌ {self._debugLabel}: predictor mode set failed! Expected training={expected_predictor}, got {self.predictor.training}"
        assert self.es_encoder.training == expected_encoder, \
            f"❌ {self._debugLabel}: encoder mode set failed! Expected training={expected_encoder}, got {self.es_encoder.training}"

        # Verify codec modes
        if col_codecs:
            for col_name, codec in col_codecs.items():
                if codec is not None and hasattr(codec, 'training'):
                    assert codec.training == expected_encoder, \
                        f"❌ {self._debugLabel}: codec '{col_name}' mode set failed! Expected training={expected_encoder}, got {codec.training}"

        return self


    def __exit__(self, exc_type, exc_value, traceback):
        assert self.was_training_predictor is not None
        assert self.was_training_encoder is not None

        # Restore predictor mode
        if self.was_training_predictor:
            self.predictor.train()
        else:
            self.predictor.eval()

        # Restore encoder mode
        if self.was_training_encoder:
            self.es_encoder.train()
        else:
            self.es_encoder.eval()

        # Restore codec states
        col_codecs = getattr(self.fsp.embedding_space, 'col_codecs', None)
        if col_codecs:
            for col_name, codec in col_codecs.items():
                if codec is not None and col_name in self.was_training_codecs:
                    if self.was_training_codecs[col_name]:
                        codec.train()
                    else:
                        codec.eval()

        # Verify modes were restored correctly
        assert self.predictor.training == self.was_training_predictor, \
            f"❌ {self._debugLabel}: predictor mode restore failed! Expected training={self.was_training_predictor}, got {self.predictor.training}"
        assert self.es_encoder.training == self.was_training_encoder, \
            f"❌ {self._debugLabel}: encoder mode restore failed! Expected training={self.was_training_encoder}, got {self.es_encoder.training}"

        # Verify codec modes restored
        if col_codecs:
            for col_name, codec in col_codecs.items():
                if codec is not None and col_name in self.was_training_codecs:
                    expected = self.was_training_codecs[col_name]
                    assert codec.training == expected, \
                        f"❌ {self._debugLabel}: codec '{col_name}' mode restore failed! Expected training={expected}, got {codec.training}"

        return False  # propagate exceptions


class PredictorEvalModeContextManager(PredictorTrainingContextManager):
    """
    Context manager for setting all model components to eval mode.

    Use this for:
    - Predictions (predict, predict_batch)
    - Validation during training
    - Computing metrics
    - Any inference operation
    """
    def __init__(self, fsp: "FeatrixSinglePredictor", debugLabel=None):
        super().__init__(
            fsp=fsp,
            predictor_mode=TrainingState.EVAL,
            encoder_mode=TrainingState.EVAL,
            debugLabel=debugLabel
        )


def set_training_modes(fsp: "FeatrixSinglePredictor", predictor_train: bool, encoder_train: bool, debugLabel: str = ""):
    """
    Set predictor, encoder, and codec training modes permanently (no restore on exit).

    Use this for:
    - Initial setup before training
    - Warmup phase transitions (e.g., unfreezing encoder after warmup)

    For temporary mode changes (validation, inference), use the context managers instead.

    Args:
        fsp: FeatrixSinglePredictor instance
        predictor_train: True for train mode, False for eval mode
        encoder_train: True for train mode, False for eval mode
        debugLabel: Label for assertion error messages
    """
    # Get predictor (handle both predictor and predictor_base)
    predictor = getattr(fsp, 'predictor', None)
    if predictor is None:
        predictor = getattr(fsp, 'predictor_base', None)
        if predictor is None:
            raise AttributeError(
                f"FeatrixSinglePredictor has neither 'predictor' nor 'predictor_base' attribute."
            )

    encoder = fsp.embedding_space.encoder
    assert encoder is not None

    # Set predictor mode
    if predictor_train:
        predictor.train()
    else:
        predictor.eval()
    assert predictor.training == predictor_train, \
        f"❌ {debugLabel}: predictor mode set failed! Expected training={predictor_train}, got {predictor.training}"

    # Set encoder mode
    if encoder_train:
        encoder.train()
    else:
        encoder.eval()
    assert encoder.training == encoder_train, \
        f"❌ {debugLabel}: encoder mode set failed! Expected training={encoder_train}, got {encoder.training}"

    # Set codec modes (same as encoder)
    col_codecs = getattr(fsp.embedding_space, 'col_codecs', None)
    if col_codecs:
        for col_name, codec in col_codecs.items():
            if codec is not None and hasattr(codec, 'training'):
                if encoder_train:
                    codec.train()
                else:
                    codec.eval()
                assert codec.training == encoder_train, \
                    f"❌ {debugLabel}: codec '{col_name}' mode set failed! Expected training={encoder_train}, got {codec.training}"

    logger.info(f"✅ {debugLabel}: Training modes set - predictor={predictor_train}, encoder={encoder_train}")


class EncoderEvalMode:
    """
    Context manager for temporarily setting an encoder to eval mode.

    This is the CANONICAL way to temporarily switch an encoder to eval mode
    for inference operations during training. The encoder's training state
    is automatically restored on exit (even if an exception occurs).

    Usage:
        with EncoderEvalMode(encoder):
            # encoder is in eval mode here
            embeddings = encoder.encode(...)
        # encoder is restored to previous mode here

    Works with any nn.Module that has .training, .eval(), and .train() attributes.
    """

    def __init__(self, encoder):
        self.encoder = encoder
        self.was_training = None

    def __enter__(self):
        self.was_training = self.encoder.training
        if self.was_training:
            self.encoder.eval()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.was_training:
            self.encoder.train()
        return False  # propagate exceptions
