"""
List name resolution for Trello boards.

Provides flexible matching between status names and actual Trello list names,
fetching from the board to avoid hardcoded mismatches.
"""
import logging
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def normalize_list_name(name: str) -> str:
    """Normalize a list name for flexible matching.
    
    Removes spaces around slashes, lowercases, strips whitespace.
    "Deployed / Done" and "Deployed/Done" both become "deployed/done"
    
    Args:
        name: List name to normalize
        
    Returns:
        Normalized name for comparison
    """
    # Remove spaces around slashes
    normalized = re.sub(r'\s*/\s*', '/', name)
    # Lowercase and strip
    return normalized.lower().strip()


# Pattern matching for status -> list name
# Each status maps to patterns that might match actual list names
STATUS_LIST_PATTERNS = {
    "pending": ["intake", "backlog", "planned", "ready", "todo", "to do"],
    "in_progress": ["in progress", "doing", "working", "active"],
    "review": ["review", "testing", "qa", "verify"],
    "done": ["done", "deployed", "complete", "finished", "closed"],
    "blocked": ["blocked", "issues", "tech debt", "impediment", "stuck"],
}

# Reverse: list name patterns -> status
LIST_STATUS_PATTERNS = {
    "intake": "pending",
    "backlog": "pending",
    "planned": "pending",
    "ready": "pending",
    "todo": "pending",
    "in progress": "in_progress",
    "doing": "in_progress",
    "working": "in_progress",
    "review": "review",
    "testing": "review",
    "qa": "review",
    "done": "done",
    "deployed": "done",
    "complete": "done",
    "finished": "done",
    "blocked": "blocked",
    "issues": "blocked",
    "tech debt": "blocked",
}


class ListResolver:
    """Resolves status names to actual Trello list names/IDs.
    
    Fetches lists from the board once and caches them, then provides
    flexible matching to find the right list for each status.
    """
    
    def __init__(self, trello_service: Any):
        """Initialize with a TrelloService instance.
        
        Args:
            trello_service: TrelloService with board already set
        """
        self.service = trello_service
        self._lists_cache: Optional[List[Dict]] = None
        self._list_map: Optional[Dict[str, str]] = None  # normalized_name -> id
        self._list_names: Optional[Dict[str, str]] = None  # normalized_name -> actual_name
        
    def _fetch_lists(self) -> List[Dict]:
        """Fetch and cache lists from the board.
        
        Returns:
            List of dict with 'id' and 'name' keys
        """
        if self._lists_cache is not None:
            return self._lists_cache
            
        try:
            board = self.service.board
            lists = board.list_lists()
            self._lists_cache = [
                {"id": lst.id, "name": lst.name, "closed": getattr(lst, 'closed', False)}
                for lst in lists
                if not getattr(lst, 'closed', False)  # Skip archived lists
            ]
            
            # Build lookup maps
            self._list_map = {}
            self._list_names = {}
            for lst in self._lists_cache:
                normalized = normalize_list_name(lst["name"])
                self._list_map[normalized] = lst["id"]
                self._list_names[normalized] = lst["name"]
                
            logger.debug(f"Cached {len(self._lists_cache)} lists from board")
            return self._lists_cache
            
        except Exception as e:
            logger.error(f"Failed to fetch lists: {e}")
            return []
    
    def get_all_lists(self) -> List[Dict]:
        """Get all non-archived lists from the board.
        
        Returns:
            List of dicts with 'id' and 'name' keys
        """
        return self._fetch_lists()
    
    def find_list_for_status(self, status: str) -> Optional[Dict[str, str]]:
        """Find the actual list for a given status.
        
        Uses pattern matching to find a list that matches the status.
        
        Args:
            status: Status like "pending", "in_progress", "done", etc.
            
        Returns:
            Dict with 'id' and 'name' of matching list, or None
        """
        self._fetch_lists()
        
        if not self._list_map:
            return None
            
        patterns = STATUS_LIST_PATTERNS.get(status, [status])
        
        # Try each pattern against each list
        for pattern in patterns:
            pattern_normalized = normalize_list_name(pattern)
            
            for normalized_name, list_id in self._list_map.items():
                # Check if pattern is contained in list name
                if pattern_normalized in normalized_name:
                    return {
                        "id": list_id,
                        "name": self._list_names[normalized_name]
                    }
                    
        logger.warning(f"No list found for status: {status}")
        return None
    
    def get_status_for_list(self, list_name: str) -> Optional[str]:
        """Get the status for a given list name.
        
        Args:
            list_name: Actual Trello list name
            
        Returns:
            Status string like "pending", "in_progress", "done", etc.
        """
        normalized = normalize_list_name(list_name)
        
        # Check each pattern
        for pattern, status in LIST_STATUS_PATTERNS.items():
            if pattern in normalized:
                return status
                
        logger.debug(f"No status mapping for list: {list_name}")
        return None
    
    def get_list_id(self, list_name: str) -> Optional[str]:
        """Get the ID for a list by name (flexible matching).
        
        Args:
            list_name: List name (exact or approximate)
            
        Returns:
            List ID or None
        """
        self._fetch_lists()
        
        if not self._list_map:
            return None
            
        normalized = normalize_list_name(list_name)
        
        # Try exact match first
        if normalized in self._list_map:
            return self._list_map[normalized]
            
        # Try partial match
        for cached_name, list_id in self._list_map.items():
            if normalized in cached_name or cached_name in normalized:
                return list_id
                
        return None
    
    def get_list_name(self, list_name: str) -> Optional[str]:
        """Get the actual list name from an approximate name.
        
        Args:
            list_name: List name (exact or approximate)
            
        Returns:
            Actual list name from Trello, or None
        """
        self._fetch_lists()
        
        if not self._list_names:
            return None
            
        normalized = normalize_list_name(list_name)
        
        # Try exact match first
        if normalized in self._list_names:
            return self._list_names[normalized]
            
        # Try partial match
        for cached_name, actual_name in self._list_names.items():
            if normalized in cached_name or cached_name in normalized:
                return actual_name
                
        return None
    
    def clear_cache(self) -> None:
        """Clear the cached list data."""
        self._lists_cache = None
        self._list_map = None
        self._list_names = None


def create_list_status_map(trello_service: Any) -> Dict[str, str]:
    """Create a list name -> status mapping from actual board lists.
    
    This replaces hardcoded LIST_STATUS_MAP in webhook.py.
    
    Args:
        trello_service: TrelloService with board set
        
    Returns:
        Dict mapping actual list names to status strings
    """
    resolver = ListResolver(trello_service)
    lists = resolver.get_all_lists()
    
    result = {}
    for lst in lists:
        status = resolver.get_status_for_list(lst["name"])
        if status:
            result[lst["name"]] = status
            
    return result
