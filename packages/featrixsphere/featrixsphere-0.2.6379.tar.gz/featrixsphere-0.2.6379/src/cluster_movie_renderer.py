#!/usr/bin/env python3
"""
Cluster Movie Renderer

Watches /backplane for training jobs from other nodes and generates movie frames
(3D projection JSONs) as new epoch checkpoints appear.

This daemon:
1. Scans /backplane/backplane1/sphere/host-*/app/featrix_output/ for train_es jobs
2. Monitors each job for new checkpoint files:
   - checkpoint_inference_e-{epoch}.pt (lightweight inference checkpoints)
   - embedding_space_epoch_{epoch}.pickle (full embedding space pickles)
3. Generates projections using generate_movie_frame_on_cpu()
4. Writes projections back to the job's epoch_projections/ directory
5. Writes diagnostic files: <checkpoint>_reloaded_status.json with load stats,
   encoder health, codec info, and timing. Creates FIRST_ERROR symlink on failures.

Enable on a node by setting in /sphere/node_config.json:
{
    "enable_movie_renderer": true
}
"""

import argparse
import json
import logging
import os
import pickle
import signal
import socket
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import torch

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-8s] %(name)-45s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add src to path for imports
src_path = Path(__file__).parent
if str(src_path.resolve()) not in sys.path:
    sys.path.insert(0, str(src_path.resolve()))

# Add lib to path
lib_path = src_path / "lib"
if str(lib_path.resolve()) not in sys.path:
    sys.path.insert(0, str(lib_path.resolve()))


# =============================================================================
# Configuration
# =============================================================================

NODE_CONFIG_PATH = Path("/sphere/node_config.json")
BACKPLANE_ROOT = Path("/backplane/backplane1/sphere")
DEFAULT_SCAN_INTERVAL = 60  # seconds between scans for new jobs
DEFAULT_WATCH_INTERVAL = 10  # seconds between checking watched jobs for new epochs


def load_node_config() -> dict:
    """Load node configuration from /sphere/node_config.json."""
    if not NODE_CONFIG_PATH.exists():
        return {}

    try:
        with open(NODE_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load node config from {NODE_CONFIG_PATH}: {e}")
        return {}


def is_movie_renderer_enabled() -> bool:
    """Check if movie renderer is enabled on this node."""
    config = load_node_config()
    return config.get('enable_movie_renderer', False)


# =============================================================================
# Job Discovery and Tracking
# =============================================================================

class TrainingJob:
    """Represents a training job being watched for movie frame generation."""

    def __init__(self, job_dir: Path, source_node: str):
        self.job_dir = job_dir
        self.source_node = source_node
        self.session_id = job_dir.parent.name
        self.job_id = job_dir.name  # e.g., "train_es_abc123"
        self.last_processed_epoch = -1
        self.is_complete = False
        self.first_seen = datetime.now()
        self.last_activity = datetime.now()

        # Paths
        self.data_snapshot_path = job_dir / "movie_data_snapshot.json"
        self.epoch_projections_dir = job_dir / "epoch_projections"

    def __repr__(self):
        return f"TrainingJob({self.source_node}/{self.session_id}/{self.job_id}, epoch={self.last_processed_epoch})"

    def has_data_snapshot(self) -> bool:
        """Check if the job has a movie data snapshot (required for rendering)."""
        return self.data_snapshot_path.exists()

    def is_job_complete(self) -> bool:
        """Check if the training job has completed."""
        # Check for completion markers
        finished_file = self.job_dir / "FINISHED"
        pickle_file = self.job_dir / "embedding_space.pickle"

        if finished_file.exists() or pickle_file.exists():
            return True

        return False

    def get_available_checkpoints(self) -> List[Tuple[int, Path]]:
        """Get list of (epoch, checkpoint_path) for available inference checkpoints.

        Supports both formats:
        - checkpoint_inference_e-{epoch}.pt (lightweight inference checkpoints)
        - embedding_space_epoch_{epoch}.pickle (full embedding space pickles)
        """
        checkpoints = []
        seen_epochs = set()  # Track epochs to avoid duplicates

        # Pattern 1: checkpoint_inference_e-{epoch}.pt
        for checkpoint_file in self.job_dir.glob("checkpoint_inference_e-*.pt"):
            try:
                name = checkpoint_file.name
                # checkpoint_inference_e-5.pt -> 5
                epoch_str = name.replace("checkpoint_inference_e-", "").replace(".pt", "")
                epoch = int(epoch_str)
                if epoch not in seen_epochs:
                    checkpoints.append((epoch, checkpoint_file))
                    seen_epochs.add(epoch)
            except (ValueError, IndexError):
                continue

        # Pattern 2: embedding_space_epoch_{epoch}.pickle
        for checkpoint_file in self.job_dir.glob("embedding_space_epoch_*.pickle"):
            try:
                name = checkpoint_file.name
                # embedding_space_epoch_5.pickle -> 5
                epoch_str = name.replace("embedding_space_epoch_", "").replace(".pickle", "")
                epoch = int(epoch_str)
                if epoch not in seen_epochs:
                    checkpoints.append((epoch, checkpoint_file))
                    seen_epochs.add(epoch)
            except (ValueError, IndexError):
                continue

        # Sort by epoch
        checkpoints.sort(key=lambda x: x[0])
        return checkpoints

    def has_inline_movie_writer(self) -> bool:
        """Check if this job is using inline movie generation (subsample_meta.json exists).

        When inline mode is used, projections are generated during training and we
        should skip re-rendering those epochs.
        """
        subsample_meta = self.epoch_projections_dir / "subsample_meta.json"
        return subsample_meta.exists()

    def get_unprocessed_epochs(self) -> List[Tuple[int, Path]]:
        """Get epochs that haven't been processed yet.

        Excludes epochs that already have projection files (from inline generation).
        """
        checkpoints = self.get_available_checkpoints()
        existing_projections = self.get_existing_projections()

        # Filter out epochs we've already processed AND epochs with existing projections
        unprocessed = [
            (epoch, path) for epoch, path in checkpoints
            if epoch > self.last_processed_epoch and epoch not in existing_projections
        ]

        # If inline mode is active and projections exist, log that we're skipping
        if self.has_inline_movie_writer() and existing_projections:
            if unprocessed:
                logger.debug(f"{self.job_id}: Inline mode detected, {len(existing_projections)} projections already exist")

        return unprocessed

    def get_existing_projections(self) -> Set[int]:
        """Get set of epochs that already have projection files."""
        existing = set()
        if self.epoch_projections_dir.exists():
            for proj_file in self.epoch_projections_dir.glob("projections_epoch_*.json"):
                try:
                    # projections_epoch_005.json -> 5
                    name = proj_file.name
                    epoch_str = name.replace("projections_epoch_", "").replace(".json", "")
                    epoch = int(epoch_str)
                    existing.add(epoch)
                except (ValueError, IndexError):
                    continue
        return existing


def discover_training_jobs(backplane_root: Path) -> List[TrainingJob]:
    """
    Scan backplane for training jobs with movie data snapshots.

    Looks in: /backplane/backplane1/sphere/host-*/app/featrix_output/*/train_es_*
    """
    jobs = []

    # Find all host directories
    host_pattern = backplane_root / "host-*"

    for host_dir in Path("/").glob(str(host_pattern).lstrip("/")):
        if not host_dir.is_dir():
            continue

        # Extract node name from host-{node}
        source_node = host_dir.name.replace("host-", "")

        # Skip our own node
        hostname = socket.gethostname().lower()
        if source_node.lower() in hostname or hostname in source_node.lower():
            continue

        # Look for featrix_output directory
        output_dir = host_dir / "app" / "featrix_output"
        if not output_dir.exists():
            continue

        # Scan session directories
        for session_dir in output_dir.iterdir():
            if not session_dir.is_dir():
                continue

            # Find train_es_* job directories
            for job_dir in session_dir.glob("train_es_*"):
                if not job_dir.is_dir():
                    continue

                job = TrainingJob(job_dir, source_node)

                # Include jobs that have a data snapshot (for async rendering)
                # Skip jobs using inline mode - they generate their own projections
                if job.has_inline_movie_writer():
                    # Job uses inline mode - no need to render frames
                    logger.debug(f"Skipping {job.job_id}: uses inline movie generation")
                    continue

                if job.has_data_snapshot():
                    jobs.append(job)

    return jobs


# =============================================================================
# Movie Frame Generation
# =============================================================================

def collect_encoder_diagnostics(encoder) -> dict:
    """Collect diagnostic information about the encoder model."""
    diagnostics = {
        "encoder_type": type(encoder).__name__,
        "is_training_mode": encoder.training,
        "device": str(next(encoder.parameters()).device) if list(encoder.parameters()) else "no_params",
    }

    # Parameter counts
    try:
        if hasattr(encoder, 'count_model_parameters'):
            diagnostics["param_counts"] = encoder.count_model_parameters()
        else:
            total_params = sum(p.numel() for p in encoder.parameters())
            trainable_params = sum(p.numel() for p in encoder.parameters() if p.requires_grad)
            diagnostics["param_counts"] = {
                "total_params": total_params,
                "trainable_params": trainable_params,
            }
    except Exception as e:
        diagnostics["param_counts_error"] = str(e)

    # Check for NaN/Inf in weights
    try:
        nan_count = 0
        inf_count = 0
        total_tensors = 0
        weight_stats = {}

        for name, param in encoder.named_parameters():
            total_tensors += 1
            param_data = param.data

            # Count NaN and Inf
            nan_in_param = torch.isnan(param_data).sum().item()
            inf_in_param = torch.isinf(param_data).sum().item()
            nan_count += nan_in_param
            inf_count += inf_in_param

            # Collect stats for key layers (first 5 and last 5)
            if total_tensors <= 5 or "output" in name.lower() or "final" in name.lower():
                weight_stats[name] = {
                    "shape": list(param_data.shape),
                    "mean": param_data.mean().item(),
                    "std": param_data.std().item(),
                    "min": param_data.min().item(),
                    "max": param_data.max().item(),
                    "nan_count": nan_in_param,
                    "inf_count": inf_in_param,
                }

        diagnostics["weight_health"] = {
            "total_tensors": total_tensors,
            "total_nan_values": nan_count,
            "total_inf_values": inf_count,
            "has_nan": nan_count > 0,
            "has_inf": inf_count > 0,
            "is_healthy": nan_count == 0 and inf_count == 0,
        }
        diagnostics["weight_samples"] = weight_stats

    except Exception as e:
        diagnostics["weight_health_error"] = str(e)

    # Check encoder subcomponents
    try:
        subcomponents = {}
        if hasattr(encoder, 'column_encoder'):
            subcomponents["column_encoder"] = {
                "type": type(encoder.column_encoder).__name__,
                "num_encoders": len(encoder.column_encoder.encoders) if hasattr(encoder.column_encoder, 'encoders') else "unknown",
            }
        if hasattr(encoder, 'joint_encoder'):
            subcomponents["joint_encoder"] = {
                "type": type(encoder.joint_encoder).__name__,
                "has_relationship_extractor": hasattr(encoder.joint_encoder, 'relationship_extractor') and encoder.joint_encoder.relationship_extractor is not None,
            }
        diagnostics["subcomponents"] = subcomponents
    except Exception as e:
        diagnostics["subcomponents_error"] = str(e)

    return diagnostics


def collect_codec_diagnostics(col_codecs: dict) -> dict:
    """Collect diagnostic information about column codecs."""
    diagnostics = {
        "num_codecs": len(col_codecs),
        "codec_types": {},
        "codec_details": {},
    }

    for col_name, codec in col_codecs.items():
        codec_type = type(codec).__name__
        diagnostics["codec_types"][col_name] = codec_type

        # Get codec details
        details = {"type": codec_type}
        if hasattr(codec, 'in_dim'):
            details["in_dim"] = codec.in_dim
        if hasattr(codec, 'out_dim'):
            details["out_dim"] = codec.out_dim
        if hasattr(codec, 'vocab_size'):
            details["vocab_size"] = codec.vocab_size

        diagnostics["codec_details"][col_name] = details

    return diagnostics


def write_diagnostic_json(checkpoint_path: Path, diagnostics: dict, success: bool):
    """Write diagnostic JSON file next to the checkpoint.

    Creates:
    - <checkpoint>_reloaded_status.json - always written with full diagnostics
    - FIRST_ERROR symlink - created on first error, points to the failing status file
    """
    diag_path = checkpoint_path.parent / f"{checkpoint_path.stem}_reloaded_status.json"

    try:
        with open(diag_path, 'w') as f:
            json.dump(diagnostics, f, indent=2, default=str)
        logger.info(f"   📋 Wrote diagnostics to {diag_path}")

        # On error, create FIRST_ERROR symlink if it doesn't exist yet
        if not success:
            error_link = checkpoint_path.parent / "FIRST_ERROR"
            if not error_link.exists():
                try:
                    # Create relative symlink to the status file
                    error_link.symlink_to(diag_path.name)
                    logger.warning(f"   🔗 Created FIRST_ERROR symlink -> {diag_path.name}")
                except Exception as link_err:
                    logger.warning(f"   ⚠️  Failed to create FIRST_ERROR symlink: {link_err}")

    except Exception as e:
        logger.warning(f"   ⚠️  Failed to write diagnostics: {e}")


def generate_frame_for_epoch(job: TrainingJob, epoch: int, checkpoint_path: Path) -> bool:
    """
    Generate a movie frame for a specific epoch.

    Returns True if successful, False otherwise.
    Writes a _reloaded_status.json diagnostic file next to the checkpoint.
    """
    start_time = time.time()
    diagnostics = {
        "epoch": epoch,
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_type": checkpoint_path.suffix,
        "checkpoint_size_mb": checkpoint_path.stat().st_size / (1024 * 1024) if checkpoint_path.exists() else 0,
        "started_at": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "source_node": job.source_node,
        "session_id": job.session_id,
        "job_id": job.job_id,
    }

    try:
        logger.info(f"🎬 Generating frame for {job.source_node}/{job.session_id} epoch {epoch}")
        logger.info(f"   Checkpoint: {checkpoint_path.name} ({diagnostics['checkpoint_size_mb']:.1f} MB)")

        # Load checkpoint based on file type
        load_start = time.time()

        if checkpoint_path.suffix == '.pickle':
            # Load pickle file (full embedding space)
            logger.info(f"   Loading pickle checkpoint...")
            with open(checkpoint_path, 'rb') as f:
                embedding_space = pickle.load(f)
            diagnostics["load_method"] = "pickle"

            # Extract encoder and codecs from embedding space
            encoder = embedding_space.encoder
            col_codecs = embedding_space.col_codecs if hasattr(embedding_space, 'col_codecs') else {}

        else:
            # Load .pt file (lightweight checkpoint)
            logger.info(f"   Loading torch checkpoint...")
            checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
            diagnostics["load_method"] = "torch"
            diagnostics["checkpoint_keys"] = list(checkpoint.keys())

            encoder = checkpoint.get("encoder")
            if encoder is None:
                raise ValueError("Checkpoint missing 'encoder' key")
            col_codecs = checkpoint.get("col_codecs", {})

        load_time = time.time() - load_start
        diagnostics["load_time_seconds"] = load_time
        logger.info(f"   ✅ Loaded in {load_time:.1f}s")

        # Collect encoder diagnostics
        diagnostics["encoder"] = collect_encoder_diagnostics(encoder)

        # Collect codec diagnostics
        diagnostics["codecs"] = collect_codec_diagnostics(col_codecs)

        # Move to CPU and eval mode
        encoder.cpu()
        encoder.eval()

        # Now generate the actual frame using the movie frame task
        from featrix.neural.movie_frame_task import generate_movie_frame_on_cpu

        frame_start = time.time()
        result = generate_movie_frame_on_cpu(
            checkpoint_path=str(checkpoint_path),
            data_snapshot_path=str(job.data_snapshot_path),
            epoch=epoch,
            output_dir=str(job.job_dir),
            session_id=job.session_id
        )
        frame_time = time.time() - frame_start

        total_time = time.time() - start_time
        diagnostics["frame_generation_time_seconds"] = frame_time
        diagnostics["total_time_seconds"] = total_time
        diagnostics["completed_at"] = datetime.now().isoformat()

        if result:
            diagnostics["success"] = True
            diagnostics["output_path"] = result
            diagnostics["frame_generated"] = True
            logger.info(f"✅ Frame generated: {result} (total: {total_time:.1f}s)")
            write_diagnostic_json(checkpoint_path, diagnostics, success=True)
            return True
        else:
            diagnostics["success"] = False
            diagnostics["frame_generated"] = False
            diagnostics["error"] = "generate_movie_frame_on_cpu returned None"
            logger.warning(f"⚠️  Frame generation returned None for epoch {epoch}")
            write_diagnostic_json(checkpoint_path, diagnostics, success=False)
            return False

    except Exception as e:
        total_time = time.time() - start_time
        diagnostics["success"] = False
        diagnostics["frame_generated"] = False
        diagnostics["error"] = str(e)
        diagnostics["error_type"] = type(e).__name__
        diagnostics["total_time_seconds"] = total_time
        diagnostics["completed_at"] = datetime.now().isoformat()

        logger.error(f"❌ Failed to generate frame for epoch {epoch}: {e}")
        import traceback
        traceback.print_exc()
        diagnostics["traceback"] = traceback.format_exc()

        write_diagnostic_json(checkpoint_path, diagnostics, success=False)
        return False


# =============================================================================
# Main Daemon
# =============================================================================

class ClusterMovieRenderer:
    """Main daemon that watches backplane and renders movie frames."""

    def __init__(
        self,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
        watch_interval: int = DEFAULT_WATCH_INTERVAL,
        backplane_root: Path = BACKPLANE_ROOT
    ):
        self.scan_interval = scan_interval
        self.watch_interval = watch_interval
        self.backplane_root = backplane_root
        self.running = True

        # Track watched jobs: job_key -> TrainingJob
        # job_key = f"{source_node}/{session_id}/{job_id}"
        self.watched_jobs: Dict[str, TrainingJob] = {}

        # Track completed jobs to avoid re-scanning
        self.completed_jobs: Set[str] = set()

        # Current job being processed - stick with one model until done
        # This avoids loading/unloading different models repeatedly
        self.current_job_key: Optional[str] = None

        # Stats
        self.frames_generated = 0
        self.jobs_discovered = 0
        self.last_scan_time = 0.0

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info(f"ClusterMovieRenderer initialized")
        logger.info(f"  Scan interval: {scan_interval}s")
        logger.info(f"  Watch interval: {watch_interval}s")
        logger.info(f"  Backplane root: {backplane_root}")

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _job_key(self, job: TrainingJob) -> str:
        """Generate unique key for a job."""
        return f"{job.source_node}/{job.session_id}/{job.job_id}"

    def scan_for_new_jobs(self):
        """Scan backplane for new training jobs."""
        logger.debug("Scanning backplane for new training jobs...")

        try:
            jobs = discover_training_jobs(self.backplane_root)

            new_count = 0
            for job in jobs:
                key = self._job_key(job)

                # Skip already watched or completed jobs
                if key in self.watched_jobs or key in self.completed_jobs:
                    continue

                # Check what projections already exist
                existing = job.get_existing_projections()
                if existing:
                    job.last_processed_epoch = max(existing)
                    logger.info(f"📽️  Found existing projections up to epoch {job.last_processed_epoch}")

                # Add to watched jobs
                self.watched_jobs[key] = job
                self.jobs_discovered += 1
                new_count += 1

                logger.info(f"🆕 Discovered job: {key}")

            if new_count > 0:
                logger.info(f"Found {new_count} new job(s) to watch")

        except Exception as e:
            logger.error(f"Error scanning for jobs: {e}")
            import traceback
            traceback.print_exc()

    def process_watched_jobs(self):
        """Check watched jobs for new epochs and generate frames.

        IMPORTANT: Processes ONE FRAME AT A TIME to avoid overwhelming the system.
        Sticks with ONE MODEL until all its frames are done before moving to another.
        This avoids repeatedly loading/unloading different models.
        """
        jobs_to_remove = []

        # First, clean up completed jobs
        for key, job in list(self.watched_jobs.items()):
            if job.is_job_complete():
                logger.info(f"✅ Job complete: {key}")
                self.completed_jobs.add(key)
                jobs_to_remove.append(key)
                if self.current_job_key == key:
                    self.current_job_key = None

        for key in jobs_to_remove:
            del self.watched_jobs[key]

        # If we have a current job, stick with it until done
        if self.current_job_key and self.current_job_key in self.watched_jobs:
            job = self.watched_jobs[self.current_job_key]
            unprocessed = job.get_unprocessed_epochs()

            if unprocessed:
                # Continue with current model
                epoch, checkpoint_path = unprocessed[0]
                logger.info(f"📊 {self.current_job_key}: processing epoch {epoch} ({len(unprocessed)} remaining)")

                if not self.running:
                    return

                success = generate_frame_for_epoch(job, epoch, checkpoint_path)

                if success:
                    job.last_processed_epoch = epoch
                    job.last_activity = datetime.now()
                    self.frames_generated += 1

                # Done for this cycle - will continue this model next cycle
                return
            else:
                # Current model has no more frames, clear it to pick a new one
                logger.info(f"📊 {self.current_job_key}: all frames done, moving to next model")
                self.current_job_key = None

        # No current job or current job is done - find a new one
        for key, job in self.watched_jobs.items():
            try:
                unprocessed = job.get_unprocessed_epochs()

                if not unprocessed:
                    continue

                # Found a job with work to do - make it the current job
                self.current_job_key = key
                epoch, checkpoint_path = unprocessed[0]
                logger.info(f"🎬 Starting new model: {key} ({len(unprocessed)} frames to process)")

                if not self.running:
                    return

                success = generate_frame_for_epoch(job, epoch, checkpoint_path)

                if success:
                    job.last_processed_epoch = epoch
                    job.last_activity = datetime.now()
                    self.frames_generated += 1

                # Done for this cycle
                return

            except Exception as e:
                logger.error(f"Error processing job {key}: {e}")
                import traceback
                traceback.print_exc()

    def run(self):
        """Main daemon loop."""
        logger.info("=" * 80)
        logger.info("🎬 CLUSTER MOVIE RENDERER STARTING")
        logger.info("=" * 80)

        # Check if enabled
        if not is_movie_renderer_enabled():
            logger.info("Movie renderer is NOT enabled on this node.")
            logger.info(f"To enable, create {NODE_CONFIG_PATH} with:")
            logger.info('  {"enable_movie_renderer": true}')
            logger.info("Sleeping indefinitely (to avoid supervisor FATAL state)...")
            # Sleep forever instead of exiting - avoids supervisor marking as FATAL
            while self.running:
                time.sleep(86400)  # Sleep 24 hours at a time
            return 0

        logger.info("Movie renderer is ENABLED on this node")

        # Check backplane exists
        if not self.backplane_root.exists():
            logger.error(f"Backplane root does not exist: {self.backplane_root}")
            logger.error("Is the backplane mounted?")
            return 1

        last_scan = 0
        last_watch = 0

        while self.running:
            now = time.time()

            # Scan for new jobs periodically
            if now - last_scan >= self.scan_interval:
                self.scan_for_new_jobs()
                last_scan = now

            # Process watched jobs more frequently
            if now - last_watch >= self.watch_interval:
                self.process_watched_jobs()
                last_watch = now

            # Status log every 5 minutes
            if int(now) % 300 == 0:
                logger.info(
                    f"📊 Status: watching {len(self.watched_jobs)} job(s), "
                    f"{self.frames_generated} frames generated, "
                    f"{len(self.completed_jobs)} completed"
                )

            # Sleep a bit
            time.sleep(1)

        logger.info("=" * 80)
        logger.info("🎬 CLUSTER MOVIE RENDERER STOPPED")
        logger.info(f"   Total frames generated: {self.frames_generated}")
        logger.info(f"   Total jobs discovered: {self.jobs_discovered}")
        logger.info("=" * 80)

        return 0


# =============================================================================
# Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Cluster Movie Renderer - generates movie frames from backplane training jobs"
    )
    parser.add_argument(
        "--scan-interval",
        type=int,
        default=DEFAULT_SCAN_INTERVAL,
        help=f"Seconds between scans for new jobs (default: {DEFAULT_SCAN_INTERVAL})"
    )
    parser.add_argument(
        "--watch-interval",
        type=int,
        default=DEFAULT_WATCH_INTERVAL,
        help=f"Seconds between checking watched jobs (default: {DEFAULT_WATCH_INTERVAL})"
    )
    parser.add_argument(
        "--backplane-root",
        type=str,
        default=str(BACKPLANE_ROOT),
        help=f"Backplane root path (default: {BACKPLANE_ROOT})"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for testing)"
    )

    args = parser.parse_args()

    renderer = ClusterMovieRenderer(
        scan_interval=args.scan_interval,
        watch_interval=args.watch_interval,
        backplane_root=Path(args.backplane_root)
    )

    if args.once:
        # Single pass for testing
        if not is_movie_renderer_enabled():
            logger.info("Movie renderer not enabled, exiting")
            return 0
        renderer.scan_for_new_jobs()
        renderer.process_watched_jobs()
        return 0

    return renderer.run()


if __name__ == "__main__":
    sys.exit(main())
