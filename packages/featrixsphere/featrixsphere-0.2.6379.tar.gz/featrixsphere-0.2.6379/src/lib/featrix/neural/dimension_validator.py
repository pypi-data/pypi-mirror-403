#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
Comprehensive dimension validation for EmbeddingSpace.

This module validates that all encoder components have consistent dimensions
and crashes early with clear error messages if mismatches are detected.
"""

import logging
from typing import Optional, List, Dict, Any

import torch
import torch.nn as nn

from featrix.neural.featrix_token import create_token_batch

logger = logging.getLogger(__name__)


class DimensionMismatchError(Exception):
    """Raised when dimension mismatches are detected in the encoder hierarchy."""
    pass


def validate_embedding_space_dimensions(es, crash_on_mismatch: bool = True, test_with_dummy_batch: bool = False) -> List[str]:
    """
    Comprehensively validate all dimensions in an EmbeddingSpace.
    
    Args:
        es: EmbeddingSpace object to validate
        crash_on_mismatch: If True, raise DimensionMismatchError on first mismatch.
                          If False, collect all issues and return them.
        test_with_dummy_batch: If True, actually run a dummy batch through the encoder to test runtime.
                              If False (default), only validate config dimensions (much faster, no side effects).
    
    Returns:
        List of error messages (empty if all dimensions are consistent)
        
    Raises:
        DimensionMismatchError: If crash_on_mismatch=True and mismatches are found
    """
    errors = []
    
    # 1. Validate top-level d_model
    if not hasattr(es, 'd_model'):
        errors.append("❌ EmbeddingSpace missing 'd_model' attribute")
        if crash_on_mismatch:
            raise DimensionMismatchError(errors[0])
        return errors
    
    es_d_model = es.d_model
    logger.info(f"🔍 Validating EmbeddingSpace dimensions (expected d_model={es_d_model})...")
    
    # 2. Validate encoder exists
    if not hasattr(es, 'encoder') or es.encoder is None:
        errors.append("❌ EmbeddingSpace.encoder is None or missing")
        if crash_on_mismatch:
            raise DimensionMismatchError(errors[0])
        return errors
    
    encoder = es.encoder
    
    # 3. Validate encoder config d_model matches ES d_model
    # encoder.config.d_model is the authoritative source - it defines the column encoder
    # output dimension. joint_encoder may have a different internal dimension (with in_converters
    # bridging the gap), so we use encoder.config.d_model for es.d_model.
    actual_d_model = None

    # Prefer encoder.config.d_model as the source of truth (column encoder output dimension)
    if hasattr(encoder, 'config') and hasattr(encoder.config, 'd_model'):
        actual_d_model = encoder.config.d_model
    elif hasattr(encoder, 'joint_encoder') and hasattr(encoder.joint_encoder, 'config') and hasattr(encoder.joint_encoder.config, 'd_model'):
        # Fallback to joint_encoder if encoder.config.d_model is not available
        actual_d_model = encoder.joint_encoder.config.d_model

    if actual_d_model is not None and actual_d_model != es_d_model:
        # AUTO-FIX: The encoder architecture is the source of truth
        # This mismatch can happen if es.d_model was set from config.json defaults
        # during a previous load, but the encoder was trained with a different d_model
        logger.warning(f"⚠️  DIMENSION MISMATCH AUTO-FIX: EmbeddingSpace.d_model={es_d_model} but "
                      f"encoder.config.d_model={actual_d_model}")
        logger.warning(f"   Correcting es.d_model from {es_d_model} to {actual_d_model} (encoder is source of truth)")
        es.d_model = actual_d_model
        es_d_model = actual_d_model  # Update local variable for subsequent checks
    
    # 4. Validate column encoders (if they exist)
    if hasattr(encoder, 'column_encoder'):
        column_encoder = encoder.column_encoder
        
        if hasattr(column_encoder, 'encoders'):
            encoders_dict = column_encoder.encoders
            logger.info(f"   Validating {len(encoders_dict)} column encoders...")
            
            for col_name, col_encoder in encoders_dict.items():
                col_errors = _validate_column_encoder(col_name, col_encoder, es_d_model)
                errors.extend(col_errors)
                
                if crash_on_mismatch and col_errors:
                    raise DimensionMismatchError(col_errors[0])
    
    # 5. Validate joint encoder (transformer)
    if hasattr(encoder, 'joint_encoder'):
        joint_encoder = encoder.joint_encoder
        joint_errors = _validate_joint_encoder(joint_encoder, es_d_model)
        errors.extend(joint_errors)
        
        if crash_on_mismatch and joint_errors:
            raise DimensionMismatchError(joint_errors[0])
    
    # 6. Test encode() with dummy data to catch runtime dimension issues (OPTIONAL)
    # This is DISABLED by default because it's slow and can have side effects
    if test_with_dummy_batch:
        try:
            logger.info("   Testing encode() with dummy batch...")
            dummy_batch = _create_dummy_batch(es)
            if dummy_batch:
                # CRITICAL: Move dummy batch to same device as encoder to avoid device mismatch
                encoder_device = _get_encoder_device(encoder)
                if encoder_device is not None:
                    dummy_batch = _move_batch_to_device(dummy_batch, encoder_device)
                
                with torch.no_grad():
                    short_enc, full_enc = encoder.encode(dummy_batch)
                
                # Validate output dimensions
                if full_enc.shape[-1] != es_d_model:
                    error = (
                        f"❌ ENCODER OUTPUT MISMATCH: encoder.encode() returned "
                        f"dimension {full_enc.shape[-1]}, expected {es_d_model}"
                    )
                    errors.append(error)
                    if crash_on_mismatch:
                        raise DimensionMismatchError(error)
                
                logger.info(f"   ✅ Encoder produces correct output dimension: {full_enc.shape}")
        except Exception as e:
            error = f"❌ ENCODER RUNTIME ERROR during dummy encode: {type(e).__name__}: {e}"
            errors.append(error)
            if crash_on_mismatch:
                raise DimensionMismatchError(error) from e
    else:
        logger.info("   ⏭️  Skipping dummy batch test (test_with_dummy_batch=False)")
    
    if not errors:
        logger.info(f"✅ All dimensions validated successfully (d_model={es_d_model})")
    else:
        logger.error(f"❌ Found {len(errors)} dimension issues:")
        for error in errors:
            logger.error(f"   {error}")
    
    return errors


def _validate_column_encoder(col_name: str, encoder: nn.Module, expected_d_model: int) -> List[str]:
    """Validate a single column encoder's dimensions."""
    errors = []
    encoder_type = type(encoder).__name__

    # Check if encoder has config with d_out
    if hasattr(encoder, 'config'):
        config = encoder.config
        if hasattr(config, 'd_out'):
            if config.d_out != expected_d_model:
                # BACKWARD COMPATIBILITY: Old StringEncoder pickles saved config.d_out as the
                # internal MLP compression dimension (e.g., d_model//4=48 or d_model//2=96)
                # instead of the final output dimension (d_model=192).
                # The actual output is always d_model due to the final projection layers.
                # Fix: Patch config.d_out to match expected_d_model for StringEncoder.
                if encoder_type == 'StringEncoder' and hasattr(config, 'd_model'):
                    # Check if this looks like an old pickle: config.d_out is a fraction of expected
                    # (e.g., d_out=48 or 96 when expected=192)
                    if config.d_out < expected_d_model and expected_d_model % config.d_out == 0:
                        logger.warning(
                            f"⚠️  BACKWARD COMPAT: StringEncoder '{col_name}' has old config.d_out={config.d_out}, "
                            f"patching to {expected_d_model} (config.d_model={config.d_model})"
                        )
                        config.d_out = expected_d_model
                        # Don't add error - we fixed it
                    else:
                        errors.append(
                            f"❌ Column '{col_name}' ({encoder_type}): config.d_out={config.d_out}, "
                            f"expected {expected_d_model}"
                        )
                else:
                    errors.append(
                        f"❌ Column '{col_name}' ({encoder_type}): config.d_out={config.d_out}, "
                        f"expected {expected_d_model}"
                    )
        
        # For encoders with MLP layers, validate d_in
        if hasattr(config, 'd_in'):
            # Scalar encoders should have d_in=1
            if encoder_type == 'ScalarEncoder' and config.d_in != 1:
                errors.append(
                    f"❌ Column '{col_name}' (ScalarEncoder): config.d_in={config.d_in}, "
                    f"expected 1 (scalar columns should have 1 input feature)"
                )
            
            # AdaptiveScalarEncoder doesn't use SimpleMLPConfig, but internal MLPs should have d_in=1
            if encoder_type == 'AdaptiveScalarEncoder':
                _validate_adaptive_scalar_encoder(col_name, encoder, errors)
    
    # Check for mlp_encoder attribute (common in many encoders)
    if hasattr(encoder, 'mlp_encoder'):
        mlp = encoder.mlp_encoder
        _validate_mlp_layers(f"Column '{col_name}' mlp_encoder", mlp, expected_d_model, errors)
    
    return errors


def _validate_adaptive_scalar_encoder(col_name: str, encoder: nn.Module, errors: List[str]):
    """Validate AdaptiveScalarEncoder internal MLPs."""
    # Check each strategy MLP
    mlp_names = [
        'linear_mlp', 'log_mlp', 'robust_mlp', 'rank_mlp', 'periodic_mlp',
        'zscore_mlp', 'minmax_mlp', 'quantile_mlp', 'yeojohnson_mlp',
        'winsor_mlp', 'sigmoid_mlp', 'inverse_mlp', 'polynomial_mlp',
        'frequency_mlp', 'clipped_log_mlp'
    ]
    
    for mlp_name in mlp_names:
        if hasattr(encoder, mlp_name):
            mlp = getattr(encoder, mlp_name)
            if isinstance(mlp, nn.Sequential):
                # First layer should be Linear with d_in=1 (or 2 for periodic/polynomial)
                first_layer = mlp[0]
                if isinstance(first_layer, nn.Linear):
                    expected_d_in = 2 if mlp_name in ['periodic_mlp', 'polynomial_mlp'] else 1
                    if first_layer.in_features != expected_d_in:
                        errors.append(
                            f"❌ Column '{col_name}' AdaptiveScalarEncoder.{mlp_name}[0]: "
                            f"in_features={first_layer.in_features}, expected {expected_d_in}"
                        )


def _validate_mlp_layers(prefix: str, mlp: nn.Module, expected_d_out: int, errors: List[str]):
    """Validate MLP layer dimensions."""
    if hasattr(mlp, 'config'):
        config = mlp.config
        
        # Check d_out matches expected
        if hasattr(config, 'd_out') and config.d_out != expected_d_out:
            errors.append(
                f"❌ {prefix}: config.d_out={config.d_out}, expected {expected_d_out}"
            )
        
        # Check linear_in and linear_out layers exist and have correct dimensions
        if hasattr(mlp, 'linear_in') and isinstance(mlp.linear_in, nn.Linear):
            if hasattr(config, 'd_in') and mlp.linear_in.in_features != config.d_in:
                errors.append(
                    f"❌ {prefix}.linear_in: in_features={mlp.linear_in.in_features}, "
                    f"config.d_in={config.d_in}"
                )
            if hasattr(config, 'd_hidden') and mlp.linear_in.out_features != config.d_hidden:
                errors.append(
                    f"❌ {prefix}.linear_in: out_features={mlp.linear_in.out_features}, "
                    f"config.d_hidden={config.d_hidden}"
                )
        
        if hasattr(mlp, 'linear_out') and isinstance(mlp.linear_out, nn.Linear):
            if hasattr(config, 'd_hidden') and mlp.linear_out.in_features != config.d_hidden:
                errors.append(
                    f"❌ {prefix}.linear_out: in_features={mlp.linear_out.in_features}, "
                    f"config.d_hidden={config.d_hidden}"
                )
            if mlp.linear_out.out_features != expected_d_out:
                errors.append(
                    f"❌ {prefix}.linear_out: out_features={mlp.linear_out.out_features}, "
                    f"expected {expected_d_out}"
                )


def _validate_joint_encoder(joint_encoder: nn.Module, expected_d_model: int) -> List[str]:
    """Validate joint encoder (transformer) dimensions.

    NOTE: joint_encoder.config.d_model may differ from expected_d_model when the architecture
    uses in_converters to bridge different dimensions. For example:
    - Column encoders output 192
    - in_converters transform 192 → 256
    - Transformer operates at 256

    This is a valid architecture, so we only validate that in_converters exist when dimensions differ.
    """
    errors = []

    if hasattr(joint_encoder, 'config') and hasattr(joint_encoder.config, 'd_model'):
        config_d_model = joint_encoder.config.d_model
        if config_d_model != expected_d_model:
            # Check if in_converters exist to bridge the gap
            has_in_converters = hasattr(joint_encoder, 'in_converters') and joint_encoder.in_converters
            if has_in_converters:
                # Valid architecture - in_converters bridge the dimension gap
                # Optionally verify in_converter dimensions match
                pass  # Architecture is valid, no error
            else:
                # No in_converters to bridge the gap - this is a real mismatch
                errors.append(
                    f"❌ joint_encoder: config.d_model={config_d_model}, expected {expected_d_model} "
                    f"(no in_converters to bridge the gap)"
                )

    return errors


def _create_dummy_batch(es) -> Optional[Dict[str, Any]]:
    """Create a dummy batch for testing encoder."""
    if not hasattr(es, 'col_codecs') or not es.col_codecs:
        return None
    
    dummy_batch = {}
    for col_name, codec in es.col_codecs.items():
        # Get a NOT_PRESENT token from each codec
        if hasattr(codec, 'get_not_present_token'):
            token = codec.get_not_present_token()
            # Create a batch of 1 token
            dummy_batch[col_name] = create_token_batch([token])
    
    return dummy_batch if dummy_batch else None


def _get_encoder_device(encoder: nn.Module):
    """Get the device of the encoder's parameters."""
    try:
        return next(encoder.parameters()).device
    except (StopIteration, AttributeError):
        return None


def _move_batch_to_device(batch: Dict[str, Any], device) -> Dict[str, Any]:
    """Move all tensors in a batch dictionary to the specified device."""
    moved_batch = {}
    for key, token_batch in batch.items():
        # TokenBatch is a list of Token objects (dicts)
        moved_tokens = []
        for token in token_batch:
            moved_token = {}
            for token_key, token_value in token.items():
                if isinstance(token_value, torch.Tensor):
                    moved_token[token_key] = token_value.to(device)
                else:
                    moved_token[token_key] = token_value
            moved_tokens.append(moved_token)
        moved_batch[key] = moved_tokens
    return moved_batch
