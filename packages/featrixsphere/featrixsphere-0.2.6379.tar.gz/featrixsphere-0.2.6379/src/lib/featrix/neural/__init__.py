#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#

from .gpu_utils import get_device as device

# Webhooks
from .webhooks import (
    WebhookEventType,
    WebhookConfig,
    WebhookPayload,
    WebhookDispatcher,
    get_dispatcher,
    send_training_started,
    send_training_finished,
    send_drift_alert,
    send_performance_alert,
    send_error_rate_alert,
    send_quota_alert,
    send_prediction_error,
    send_usage_update,
)
