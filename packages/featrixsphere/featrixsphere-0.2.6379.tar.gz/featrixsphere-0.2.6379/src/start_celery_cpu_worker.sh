#!/bin/bash
# Start Celery CPU worker

set -e

echo "=================================================================================="
echo "🚀 CELERY CPU WORKER STARTING - $(date -Iseconds)"
echo "=================================================================================="

# Source virtual environment
source /sphere/.venv/bin/activate

# Start Celery worker with priority support
# CRITICAL: Redis priorities require prefetch-multiplier=1 to work correctly
exec celery -A celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=cpu_worker \
    --hostname=celery-cpu_worker@$(hostname -s) \
    --prefetch-multiplier=1 \
    --without-gossip \
    --without-mingle

