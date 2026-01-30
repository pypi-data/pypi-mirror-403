"""Utility functions for aixtools compliance."""

from aixtools.compliance.private_data import PrivateData
from aixtools.context import SessionIdTuple
from aixtools.logging.logging_config import get_logger

logger = get_logger(__name__)


def mark_current_workspace_private(session_id_tuple: SessionIdTuple | None = None) -> PrivateData:
    """
    Mark the current workspace as containing private data.
    This is idempotent - calling it multiple times is safe and will only set the flag once.

    If `session_id_tuple` is None, the current FastMCP request HTTP headers are used
    to get the user and session IDs.

    Args:
        session_id_tuple: Tuple of (user_id, session_id) or None.

    Returns:
        PrivateData instance for the session.
    """
    private_data = PrivateData(session_id_tuple)

    if not private_data.has_private_data:
        private_data.has_private_data = True
        logger.info("Marked workspace as containing CP Portal private data")
    else:
        logger.debug("Workspace already marked as containing private data")

    return private_data


def has_conversation_private_data(session_id_tuple: SessionIdTuple | None = None) -> bool:
    """
    Check if a conversation has private data.

    If `session_id_tuple` is None, the current FastMCP request HTTP headers are used
    to get the user and session IDs.

    Args:
        session_id_tuple: Tuple of (user_id, session_id) or None.

    Returns:
        True if the conversation has private data, False otherwise.
    """
    try:
        private_data = PrivateData(session_id_tuple)
        return private_data.has_private_data
    except RuntimeError:
        # No active context found, return False
        logger.info("No active context found; ")
        return False
