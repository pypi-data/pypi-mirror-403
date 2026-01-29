"""
Model card repair - finds model files on disk and generates missing model cards.
"""
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Where to look for model files - LOCAL directories (node-specific)
OUTPUT_DIRS = [
    Path("/featrix-output"),
    Path("/sphere/app/featrix_output"),
]

# Backplane directories - shared NFS storage where models from all nodes are synced
BACKPLANE_BASE = Path("/backplane/backplane1/sphere")


def find_session_dir(session_id: str) -> Path | None:
    """
    Find session directory on disk by session ID.

    Checks in order:
    1. Local output directories (/featrix-output, /sphere/app/featrix_output)
    2. Backplane directories from all hosts (/backplane/backplane1/sphere/host-*)
    """
    # First check local directories
    for output_dir in OUTPUT_DIRS:
        if not output_dir.exists():
            continue
        session_dir = output_dir / session_id
        if session_dir.exists() and session_dir.is_dir():
            return session_dir

    # Check backplane - shared storage from all nodes
    if BACKPLANE_BASE.exists():
        # Check each host's backup directory on the backplane
        for host_dir in BACKPLANE_BASE.glob("host-*"):
            if not host_dir.is_dir():
                continue
            # Sessions are synced from /sphere/app/featrix_output to backplane
            session_dir = host_dir / "app" / "featrix_output" / session_id
            if session_dir.exists() and session_dir.is_dir():
                logger.info(f"📦 Found session {session_id} on backplane: {session_dir}")
                return session_dir

    return None


def find_model_card(session_id: str) -> Path | None:
    """Find existing model card for session."""
    session_dir = find_session_dir(session_id)
    if not session_dir:
        return None
    
    model_card_path = session_dir / "best_model_package" / "model_card.json"
    if model_card_path.exists():
        return model_card_path
    return None


def find_predictor_pickle(session_id: str) -> Path | None:
    """
    Find the best available single predictor pickle for a session.

    Priority order:
    1. best_single_predictor.pickle (symlink to best checkpoint)
    2. *_best_single_predictor_*.pickle (best checkpoint files)
    3. *_latest.pickle (most recent checkpoint during training)
    4. Any .pickle file (fallback)

    Returns None if no predictor found (use get_predictor_status for details).
    """
    session_dir = find_session_dir(session_id)
    if not session_dir:
        return None

    # Look for train_single_predictor_* directories
    for subdir in session_dir.iterdir():
        if subdir.is_dir() and subdir.name.startswith("train_single_predictor"):
            # Priority 1: best_single_predictor.pickle (symlink to best)
            best_symlink = subdir / "best_single_predictor.pickle"
            if best_symlink.exists():
                return best_symlink

            # Priority 2: Best checkpoint files (by ROC-AUC, PR-AUC, or val loss)
            best_checkpoints = list(subdir.glob("*_best_single_predictor_*.pickle"))
            if best_checkpoints:
                # Prefer auc_roc > auc_pr > valloss
                for pattern in ["auc_roc", "auc_pr", "valloss"]:
                    for cp in best_checkpoints:
                        if pattern in cp.name:
                            return cp
                # Fallback to any best checkpoint
                return best_checkpoints[0]

            # Priority 3: Latest checkpoint (training in progress)
            latest_pickles = list(subdir.glob("*_latest.pickle"))
            if latest_pickles:
                return latest_pickles[0]

            # Priority 4: Any pickle file (fallback)
            all_pickles = list(subdir.glob("*.pickle"))
            if all_pickles:
                return sorted(all_pickles)[-1]

    return None


def get_predictor_status(session_id: str) -> dict:
    """
    Get detailed status of predictor for a session.
    Returns a dict with clear information about what's available or what's wrong.

    Use this when find_predictor_pickle returns None to get a clear explanation.
    """
    result = {
        "session_id": session_id,
        "has_predictor": False,
        "predictor_path": None,
        "status": "unknown",
        "message": "",
        "training_info": None,
    }

    session_dir = find_session_dir(session_id)
    if not session_dir:
        result["status"] = "session_not_found"
        result["message"] = (
            f"Session directory not found for '{session_id}'. "
            f"Checked local storage and backplane. The session may not exist, "
            f"or it may not have been synced to the backplane yet."
        )
        return result

    result["session_dir"] = str(session_dir)

    # Look for train_single_predictor_* directories
    training_dirs = [d for d in session_dir.iterdir()
                     if d.is_dir() and d.name.startswith("train_single_predictor")]

    if not training_dirs:
        result["status"] = "no_training_started"
        result["message"] = f"Session exists but no predictor training has been started yet. No 'train_single_predictor_*' directory found in {session_dir}."
        return result

    # Check each training directory
    for subdir in training_dirs:
        result["training_dir"] = str(subdir)

        # Check for training status JSON
        status_files = list(subdir.glob("*_training_status.json"))
        if status_files:
            try:
                import json
                with open(status_files[0]) as f:
                    training_status = json.load(f)
                result["training_info"] = {
                    "epoch": training_status.get("epoch", 0),
                    "total_epochs": training_status.get("total_epochs", 0),
                    "progress_percent": training_status.get("progress_percent", 0),
                    "is_training": training_status.get("is_training", False),
                    "checkpoint_path": training_status.get("checkpoint_path"),
                }
            except Exception as e:
                logger.warning(f"Could not read training status: {e}")

        # Check what pickle files exist
        all_pickles = list(subdir.glob("*.pickle"))

        if not all_pickles:
            # No pickles at all - training just started
            if result.get("training_info", {}).get("is_training"):
                result["status"] = "training_in_progress_no_checkpoint"
                result["message"] = f"Training is in progress but no checkpoint has been saved yet. Checkpoints are saved every 5 epochs. Current progress: epoch {result['training_info'].get('epoch', 0)}/{result['training_info'].get('total_epochs', '?')}."
            else:
                result["status"] = "training_not_started"
                result["message"] = f"Training directory exists but no model files found. Training may not have started yet or may have failed immediately."
            return result

        # We have pickles - find_predictor_pickle should have found them
        # This case shouldn't happen if called after find_predictor_pickle returns None
        predictor = find_predictor_pickle(session_id)
        if predictor:
            result["has_predictor"] = True
            result["predictor_path"] = str(predictor)
            result["status"] = "ready"
            result["message"] = f"Predictor is ready at {predictor}."
            return result

    # Shouldn't reach here, but just in case
    result["status"] = "unknown_error"
    result["message"] = "Could not determine predictor status. Please check server logs."
    return result


def find_embedding_space(session_id: str) -> Path | None:
    """Find the embedding space pickle for a session."""
    session_dir = find_session_dir(session_id)
    if not session_dir:
        return None
    
    # Check for foundation_embedding_space.pickle at session level
    es_path = session_dir / "foundation_embedding_space.pickle"
    if es_path.exists():
        return es_path
    
    # Look in train_es_* directories
    for subdir in session_dir.iterdir():
        if subdir.is_dir() and subdir.name.startswith("train_es"):
            es_path = subdir / "embedding_space.pickle"
            if es_path.exists():
                return es_path
    return None


def trigger_model_card_generation(session_id: str) -> bool:
    """
    Trigger model card generation via prediction server.
    The prediction server already knows how to load models correctly.
    Returns True if generation was started, False if not possible.
    """
    import requests
    
    session_dir = find_session_dir(session_id)
    if not session_dir:
        logger.warning(f"Cannot generate model card - session dir not found: {session_id}")
        return False
    
    predictor_path = find_predictor_pickle(session_id)
    if not predictor_path:
        logger.warning(f"Cannot generate model card - no predictor found: {session_id}")
        return False
    
    # Call prediction server to generate model card
    # The prediction server loads the model (knows how to do it with GPU)
    # and can generate the model card as a side effect
    try:
        # Tell prediction server to generate model card for this session
        response = requests.post(
            "http://localhost:8765/generate_model_card",
            json={
                "session_id": session_id,
                "predictor_path": str(predictor_path),
                "output_dir": str(session_dir / "best_model_package"),
            },
            timeout=5,  # Don't wait long - it runs in background
        )
        if response.status_code in [200, 202]:
            logger.info(f"Prediction server started model card generation for {session_id}")
            return True
        else:
            logger.warning(f"Prediction server returned {response.status_code}: {response.text}")
            return False
    except requests.exceptions.Timeout:
        # Timeout is OK - generation continues in background
        logger.info(f"Prediction server accepted model card request (timeout OK) for {session_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to call prediction server: {e}")
        return False


def get_or_generate_model_card(session_id: str) -> tuple[dict | None, bool]:
    """
    Get model card if exists, or trigger generation.
    
    Returns:
        (model_card_dict, is_generating)
        - (dict, False) if card exists
        - (None, True) if generation was started
        - (None, False) if no model files found
    """
    # Check if card already exists
    card_path = find_model_card(session_id)
    if card_path:
        with open(card_path) as f:
            return json.load(f), False
    
    # Try to trigger generation
    started = trigger_model_card_generation(session_id)
    return None, started


def check_model_card_availability(session_id: str, embedding_space_path: str = None) -> dict:
    """Check if model card exists for a session. Returns dict with availability info."""
    try:
        # First check using our find functions
        card_path = find_model_card(session_id)
        if card_path:
            return {
                "available": True,
                "path": str(card_path),
                "endpoint": f"/session/{session_id}/model_card",
            }
        
        # Check if session dir exists (means we could generate one)
        session_dir = find_session_dir(session_id)
        if session_dir:
            # Check for model files
            predictor = find_predictor_pickle(session_id)
            es = find_embedding_space(session_id)
            if predictor or es:
                return {
                    "available": False,
                    "can_generate": True,
                    "endpoint": f"/session/{session_id}/model_card",
                }
        
        return {"available": False, "endpoint": f"/session/{session_id}/model_card"}
    except Exception as e:
        logger.warning(f"Failed to check model card availability: {e}")
        return {"available": False, "endpoint": f"/session/{session_id}/model_card", "error": str(e)}

