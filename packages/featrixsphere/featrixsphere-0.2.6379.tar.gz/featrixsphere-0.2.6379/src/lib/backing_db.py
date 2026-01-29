"""
Backing Database Module - Supabase Integration

Provides centralized session ownership tracking across all compute nodes.
sphere-api uses this to route requests without querying every node.

Usage:
    from lib.backing_db import register_session_owner, get_session_owner, delete_session_owner
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from config import config

logger = logging.getLogger(__name__)

# Supabase client (lazy initialized)
_supabase_client = None
_supabase_init_attempted = False


def _get_supabase_client():
    """
    Get or create Supabase client.
    Returns None if credentials not configured or supabase package not installed.
    """
    global _supabase_client, _supabase_init_attempted
    
    if _supabase_init_attempted:
        return _supabase_client
    
    _supabase_init_attempted = True
    
    # Load from config (which reads from .env)
    supabase_url = config.supabase_url
    supabase_key = config.supabase_key
    
    if not supabase_url or not supabase_key:
        logger.warning("⚠️  Supabase not configured - SUPABASE_URL and SUPABASE_KEY required in .env")
        return None
    
    try:
        from supabase import create_client
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info(f"✅ Supabase client initialized: {supabase_url}")
        return _supabase_client
    except ImportError:
        logger.warning("⚠️  supabase-py not installed. Install with: pip install supabase")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase client: {e}")
        return None


def register_session_owner(session_id: str, node_name: str, session_type: str = None) -> bool:
    """
    Register or update session ownership in Supabase.
    
    Args:
        session_id: The session UUID
        node_name: The compute node that owns this session (e.g., 'taco', 'churro', 'burrito')
        session_type: Optional session type (e.g., 'embedding_space', 'predictor')
    
    Returns:
        True if successful, False otherwise
    """
    client = _get_supabase_client()
    if not client:
        return False
    
    try:
        data = {
            'session_id': session_id,
            'node_name': node_name,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        if session_type:
            data['session_type'] = session_type
        
        # Upsert: insert or update if exists
        result = client.table('session_ownership').upsert(
            data,
            on_conflict='session_id'
        ).execute()
        
        logger.debug(f"📝 Registered session owner: {session_id[:12]}... -> {node_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register session owner in Supabase: {e}")
        return False


def get_session_owner(session_id: str) -> Optional[str]:
    """
    Look up which node owns a session.
    
    Args:
        session_id: The session UUID to look up
    
    Returns:
        Node name (e.g., 'taco') or None if not found
    """
    client = _get_supabase_client()
    if not client:
        return None
    
    try:
        result = client.table('session_ownership').select('node_name').eq('session_id', session_id).execute()
        
        if result.data and len(result.data) > 0:
            node_name = result.data[0]['node_name']
            logger.debug(f"🔍 Found session owner: {session_id[:12]}... -> {node_name}")
            return node_name
        
        logger.debug(f"🔍 Session {session_id[:12]}... not found in Supabase")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to look up session owner in Supabase: {e}")
        return None


def delete_session_owner(session_id: str) -> bool:
    """
    Remove session ownership record (when session is deleted).
    
    Args:
        session_id: The session UUID to remove
    
    Returns:
        True if successful, False otherwise
    """
    client = _get_supabase_client()
    if not client:
        return False
    
    try:
        client.table('session_ownership').delete().eq('session_id', session_id).execute()
        logger.debug(f"🗑️  Deleted session owner record: {session_id[:12]}...")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete session owner from Supabase: {e}")
        return False


def list_sessions_on_node(node_name: str) -> list:
    """
    List all sessions owned by a specific node.
    
    Args:
        node_name: The compute node name (e.g., 'taco')
    
    Returns:
        List of session_ids owned by this node
    """
    client = _get_supabase_client()
    if not client:
        return []
    
    try:
        result = client.table('session_ownership').select('session_id').eq('node_name', node_name).execute()
        
        if result.data:
            return [row['session_id'] for row in result.data]
        return []
    except Exception as e:
        logger.error(f"❌ Failed to list sessions for node {node_name}: {e}")
        return []


def is_supabase_available() -> bool:
    """Check if Supabase is configured and available."""
    return _get_supabase_client() is not None

