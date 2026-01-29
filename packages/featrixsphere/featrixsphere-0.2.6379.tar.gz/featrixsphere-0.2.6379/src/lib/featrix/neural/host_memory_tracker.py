#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
HostMemoryTracker: Per-host GPU memory learning for adaptive pair limits.

Tracks the max safe number of relationship pairs we've successfully used on each
host (burrito, churro, taco). This learns from experience and uses it as guidance
for future runs, avoiding OOM errors while maximizing GPU utilization.

Usage:
    tracker = HostMemoryTracker.get_instance()
    
    # Get learned max pairs for this host
    learned_max = tracker.get_learned_max_pairs()
    
    # Record success after computation completes
    tracker.record_success(num_pairs)
    
    # Record failure on OOM
    tracker.record_oom_failure()
"""
import json
import logging
import socket
import threading
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class HostMemoryTracker:
    """
    Singleton class that tracks max safe GPU pair counts per host.
    
    Stores history in a JSON file and learns from successful runs to
    progressively increase limits, while reducing on OOM failures.
    """
    
    _instance: Optional['HostMemoryTracker'] = None
    _lock = threading.Lock()
    
    # Default storage location
    DEFAULT_HISTORY_FILE = "/sphere/app/data/max_pairs_history.json"
    
    # Minimum pairs we'll ever use (safety floor)
    MIN_PAIRS = 100
    
    # How much to reduce on OOM (80% = reduce by 20%)
    OOM_REDUCTION_FACTOR = 0.8
    
    def __init__(self, history_file: Optional[str] = None):
        """
        Initialize the tracker.
        
        Args:
            history_file: Path to store the history JSON. Defaults to DEFAULT_HISTORY_FILE.
        """
        self._history_file = Path(history_file or self.DEFAULT_HISTORY_FILE)
        self._cache: Optional[Dict[str, int]] = None
        self._hostname: Optional[str] = None
        self._file_lock = threading.Lock()
    
    @classmethod
    def get_instance(cls, history_file: Optional[str] = None) -> 'HostMemoryTracker':
        """Get the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(history_file)
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (mainly for testing)."""
        with cls._lock:
            cls._instance = None
    
    @property
    def hostname(self) -> str:
        """Get the short hostname (e.g., 'burrito', 'churro', 'taco')."""
        if self._hostname is None:
            full_hostname = socket.gethostname()
            # Strip domain if present
            self._hostname = full_hostname.split('.')[0].lower()
        return self._hostname
    
    def _load_history(self) -> Dict[str, int]:
        """Load the history from disk (cached after first load)."""
        if self._cache is not None:
            return self._cache
        
        with self._file_lock:
            if self._cache is not None:
                return self._cache
            
            try:
                if self._history_file.exists():
                    with open(self._history_file, 'r') as f:
                        self._cache = json.load(f)
                        logger.debug(f"📊 Loaded pair history: {self._cache}")
                else:
                    self._cache = {}
            except Exception as e:
                logger.debug(f"Could not load pair history from {self._history_file}: {e}")
                self._cache = {}
            
            return self._cache
    
    def _save_history(self) -> None:
        """Save the current history to disk."""
        if self._cache is None:
            return
        
        with self._file_lock:
            try:
                self._history_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self._history_file, 'w') as f:
                    json.dump(self._cache, f, indent=2)
                logger.debug(f"📊 Saved pair history: {self._cache}")
            except Exception as e:
                logger.debug(f"Could not save pair history to {self._history_file}: {e}")
    
    def get_learned_max_pairs(self) -> Optional[int]:
        """
        Get the learned max pairs for this host.
        
        Returns:
            The max pairs we've successfully used on this host, or None if no history.
        """
        history = self._load_history()
        return history.get(self.hostname)
    
    def get_all_history(self) -> Dict[str, int]:
        """
        Get the pair history for all hosts.
        
        Returns:
            Dict mapping hostname to max safe pairs.
        """
        return self._load_history().copy()
    
    def record_success(self, num_pairs: int) -> None:
        """
        Record a successful computation with the given number of pairs.
        
        If this is higher than our known safe limit, update it.
        
        Args:
            num_pairs: Number of pairs that completed successfully.
        """
        if num_pairs <= 0:
            return
        
        history = self._load_history()
        current_max = history.get(self.hostname, 0)
        
        if num_pairs > current_max:
            history[self.hostname] = num_pairs
            self._cache = history
            logger.info(f"📊 Updated max safe pairs for {self.hostname}: {current_max} → {num_pairs}")
            self._save_history()
    
    def record_failure(self, num_pairs: Optional[int] = None) -> None:
        """
        Record a failure (OOM) during computation.
        
        Reduces the known safe limit for this host.
        
        Args:
            num_pairs: Number of pairs that caused the failure (optional).
        """
        history = self._load_history()
        current_max = history.get(self.hostname, 0)
        
        if current_max > self.MIN_PAIRS:
            new_max = max(self.MIN_PAIRS, int(current_max * self.OOM_REDUCTION_FACTOR))
            history[self.hostname] = new_max
            self._cache = history
            logger.warning(f"📊 OOM detected - reducing max safe pairs for {self.hostname}: {current_max} → {new_max}")
            self._save_history()
        else:
            logger.warning(f"📊 OOM detected but {self.hostname} already at minimum pairs ({current_max})")
    
    def record_oom_failure(self) -> None:
        """Alias for record_failure() for backwards compatibility."""
        self.record_failure()
    
    def set_max_pairs(self, num_pairs: int) -> None:
        """
        Manually set the max pairs for this host.
        
        Useful for manual tuning or resetting after hardware changes.
        
        Args:
            num_pairs: New max pairs value.
        """
        if num_pairs < self.MIN_PAIRS:
            logger.warning(f"Cannot set max pairs below minimum ({self.MIN_PAIRS})")
            num_pairs = self.MIN_PAIRS
        
        history = self._load_history()
        old_value = history.get(self.hostname, 0)
        history[self.hostname] = num_pairs
        self._cache = history
        logger.info(f"📊 Manually set max pairs for {self.hostname}: {old_value} → {num_pairs}")
        self._save_history()
    
    def clear_host(self) -> None:
        """Clear the history for this host (will re-learn from scratch)."""
        history = self._load_history()
        if self.hostname in history:
            del history[self.hostname]
            self._cache = history
            logger.info(f"📊 Cleared pair history for {self.hostname}")
            self._save_history()
    
    def clear_all(self) -> None:
        """Clear all history (all hosts will re-learn from scratch)."""
        self._cache = {}
        logger.info("📊 Cleared all pair history")
        self._save_history()


# ============================================================================
# Convenience functions for backwards compatibility
# ============================================================================

def get_host_memory_tracker() -> HostMemoryTracker:
    """Get the singleton HostMemoryTracker instance."""
    return HostMemoryTracker.get_instance()


def get_learned_max_pairs() -> Optional[int]:
    """Get the learned max pairs for this host."""
    return HostMemoryTracker.get_instance().get_learned_max_pairs()


def record_success(num_pairs: int) -> None:
    """Record a successful computation with the given number of pairs."""
    HostMemoryTracker.get_instance().record_success(num_pairs)


def record_oom_failure() -> None:
    """Record an OOM failure for this host."""
    HostMemoryTracker.get_instance().record_failure()


def get_pair_history() -> Dict[str, int]:
    """Get the pair history for all hosts."""
    return HostMemoryTracker.get_instance().get_all_history()

