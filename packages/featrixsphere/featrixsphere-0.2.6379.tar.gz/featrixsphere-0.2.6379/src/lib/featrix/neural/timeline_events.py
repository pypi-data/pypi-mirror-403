#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
Global timeline event posting for training diagnostics.

Any module can post events here. Events go directly to the training timeline.

Usage:
    from featrix.neural.timeline_events import post_timeline_event

    post_timeline_event({
        'epoch': 20,
        'event_type': 'strategy_prune',
        'column_name': 'revenue',
        'strategy_disabled': 'polynomial',
    })
"""
import logging

logger = logging.getLogger(__name__)

# Global reference to training timeline - set by embedded_space at training start
_TRAINING_TIMELINE = None


def set_training_timeline(timeline: list):
    """Set the global training timeline reference."""
    global _TRAINING_TIMELINE
    _TRAINING_TIMELINE = timeline


def post_timeline_event(event: dict):
    """Post an event directly to the training timeline."""
    if _TRAINING_TIMELINE is not None:
        _TRAINING_TIMELINE.append(event)
