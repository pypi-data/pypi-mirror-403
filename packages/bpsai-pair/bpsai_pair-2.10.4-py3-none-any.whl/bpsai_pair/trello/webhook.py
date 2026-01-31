"""
Trello Webhook Server for PairCoder.

Listens for Trello webhook callbacks and triggers local actions
when cards are moved between lists.

Security: Webhooks are verified using Trello's HMAC-SHA1 signature
in the X-Trello-Webhook header (when TRELLO_API_SECRET is configured).
"""
import base64
import hashlib
import hmac
import json
import logging
import os
from dataclasses import dataclass
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Optional
from pathlib import Path

from ..core.constants import extract_task_id_from_card_name

logger = logging.getLogger(__name__)


def verify_trello_signature(
    request_body: bytes,
    signature: Optional[str],
    callback_url: str
) -> bool:
    """Verify Trello webhook signature.

    Trello creates signature by:
    1. Concatenating request body + callback URL
    2. Creating HMAC-SHA1 with API secret as key
    3. Base64 encoding the result

    Args:
        request_body: Raw request body bytes
        signature: X-Trello-Webhook header value
        callback_url: The registered webhook callback URL

    Returns:
        True if signature is valid, False otherwise.
        Returns True if TRELLO_API_SECRET is not set (graceful degradation for dev).
    """
    api_secret = os.environ.get("TRELLO_API_SECRET")

    if not api_secret:
        logger.warning(
            "TRELLO_API_SECRET not set, skipping signature verification. "
            "Set this environment variable in production for security."
        )
        return True  # Graceful degradation in dev

    if not signature:
        logger.warning("Missing X-Trello-Webhook signature header")
        return False

    try:
        content = request_body + callback_url.encode()
        expected = base64.b64encode(
            hmac.new(
                api_secret.encode(),
                content,
                hashlib.sha1
            ).digest()
        ).decode()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected)
    except Exception as e:
        logger.error(f"Error verifying Trello signature: {e}")
        return False


@dataclass
class CardMoveEvent:
    """Represents a card move event from Trello."""
    card_id: str
    card_name: str
    list_before: str
    list_after: str
    board_id: str

    @property
    def task_id(self) -> Optional[str]:
        """Extract task ID from card name like '[TASK-066] Title' or '[T18.1] Title'."""
        return extract_task_id_from_card_name(self.card_name)


# Default list-to-status mappings (fallback if board fetch fails)
# Uses flexible matching via get_status_for_list() function
DEFAULT_LIST_STATUS_MAP = {
    # Include both spaced and non-spaced variants for robustness
    "Intake/Backlog": "pending",
    "Intake / Backlog": "pending",
    "Planned/Ready": "pending",
    "Planned / Ready": "pending",
    "Backlog": "pending",
    "In Progress": "in_progress",
    "Review/Testing": "review",
    "Review / Testing": "review",
    "Deployed/Done": "done",
    "Deployed / Done": "done",
    "Done": "done",
    "Issues/Tech Debt": "blocked",
    "Issues / Tech Debt": "blocked",
    "Blocked": "blocked",
}


def get_status_for_list(list_name: str, list_status_map: dict = None) -> Optional[str]:
    """Get status for a list name with flexible matching.
    
    Args:
        list_name: Trello list name
        list_status_map: Optional custom mapping (uses DEFAULT if not provided)
        
    Returns:
        Status string or None if no match
    """
    if list_status_map is None:
        list_status_map = DEFAULT_LIST_STATUS_MAP
    
    # Try exact match first
    if list_name in list_status_map:
        return list_status_map[list_name]
    
    # Try normalized match (remove spaces around slashes)
    import re
    normalized = re.sub(r'\s*/\s*', '/', list_name).strip()
    if normalized in list_status_map:
        return list_status_map[normalized]
    
    # Try pattern matching on keywords
    list_lower = list_name.lower()
    if "done" in list_lower or "deployed" in list_lower:
        return "done"
    if "progress" in list_lower or "doing" in list_lower:
        return "in_progress"
    if "review" in list_lower or "testing" in list_lower:
        return "review"
    if "blocked" in list_lower or "issue" in list_lower:
        return "blocked"
    if "backlog" in list_lower or "intake" in list_lower or "ready" in list_lower:
        return "pending"
    
    return None


# Keep old name for backwards compatibility
LIST_STATUS_MAP = DEFAULT_LIST_STATUS_MAP


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP handler for Trello webhooks.

    Security: Verifies X-Trello-Webhook signature when TRELLO_API_SECRET is set.
    """

    callback: Optional[Callable[[CardMoveEvent], None]] = None
    callback_url: Optional[str] = None  # Set by server for signature verification

    def log_message(self, format, *args):
        """Override to use logging instead of stderr."""
        logger.info(format % args)

    def do_HEAD(self):
        """Handle HEAD request - Trello uses this to verify webhook URL."""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Handle GET request - also for webhook verification."""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"PairCoder Trello Webhook Server")

    def do_POST(self):
        """Handle POST request - actual webhook callback.

        Verifies Trello webhook signature if TRELLO_API_SECRET is configured.
        Returns 401 if signature verification fails.
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # Verify signature
        signature = self.headers.get("X-Trello-Webhook")
        callback_url = getattr(self.server, "callback_url", None) or ""

        if not verify_trello_signature(body, signature, callback_url):
            logger.warning("Webhook signature verification failed")
            self.send_response(401)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Unauthorized: Invalid signature")
            return

        try:
            data = json.loads(body.decode("utf-8"))
            self._process_webhook(data)
            self.send_response(200)
            self.end_headers()
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            self.send_response(500)
            self.end_headers()

    def _process_webhook(self, data: dict) -> None:
        """Process webhook payload."""
        action = data.get("action", {})
        action_type = action.get("type")

        # We're interested in card updates
        if action_type != "updateCard":
            logger.debug(f"Ignoring action type: {action_type}")
            return

        # Check if it's a list change
        action_data = action.get("data", {})
        list_before = action_data.get("listBefore", {}).get("name")
        list_after = action_data.get("listAfter", {}).get("name")

        if not list_before or not list_after:
            logger.debug("Not a list change, ignoring")
            return

        # Extract card info
        card = action_data.get("card", {})
        board = action_data.get("board", {})

        event = CardMoveEvent(
            card_id=card.get("id", ""),
            card_name=card.get("name", ""),
            list_before=list_before,
            list_after=list_after,
            board_id=board.get("id", ""),
        )

        logger.info(f"Card move: '{event.card_name}' from '{list_before}' to '{list_after}'")

        if self.callback:
            self.callback(event)


class TrelloWebhookServer:
    """Trello webhook server with configurable handlers.

    Security: Set callback_url and TRELLO_API_SECRET environment variable
    to enable webhook signature verification.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        on_card_move: Optional[Callable[[CardMoveEvent], None]] = None,
        callback_url: Optional[str] = None,
    ):
        """Initialize webhook server.

        Args:
            host: Host to bind to
            port: Port to listen on
            on_card_move: Callback for card move events
            callback_url: The registered webhook callback URL (for signature verification)
        """
        self.host = host
        self.port = port
        self.on_card_move = on_card_move
        self.callback_url = callback_url
        self._server: Optional[HTTPServer] = None

    def start(self) -> None:
        """Start the webhook server (blocking)."""
        # Create handler class with callback
        handler = WebhookHandler
        handler.callback = self.on_card_move

        self._server = HTTPServer((self.host, self.port), handler)
        # Store callback_url on server for handler to access
        self._server.callback_url = self.callback_url

        if os.environ.get("TRELLO_API_SECRET"):
            logger.info(f"Webhook signature verification ENABLED")
        else:
            logger.warning(
                "TRELLO_API_SECRET not set - webhook signature verification DISABLED. "
                "Set this environment variable in production."
            )

        logger.info(f"Starting Trello webhook server on {self.host}:{self.port}")

        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down webhook server")
            self._server.shutdown()

    def stop(self) -> None:
        """Stop the webhook server."""
        if self._server:
            self._server.shutdown()


# Lists that trigger agent assignment (include both spacing variants)
READY_LISTS = ["Planned / Ready", "Planned/Ready", "Ready"]


def create_task_updater(paircoder_dir: Path) -> Callable[[CardMoveEvent], None]:
    """Create a callback that updates task status based on card moves.

    Args:
        paircoder_dir: Path to .paircoder directory

    Returns:
        Callback function for card move events
    """
    from ..planning.parser import TaskParser

    def update_task(event: CardMoveEvent) -> None:
        """Update local task status based on card move."""
        task_id = event.task_id
        if not task_id:
            logger.warning(f"Could not extract task ID from card: {event.card_name}")
            return

        # Determine new status from list name using flexible matching
        new_status = get_status_for_list(event.list_after)
        if not new_status:
            logger.info(f"No status mapping for list: {event.list_after}")
            return

        # Load and update task
        try:
            parser = TaskParser(paircoder_dir / "tasks")
            task = parser.get_task_by_id(task_id)

            if not task:
                logger.warning(f"Task not found: {task_id}")
                return

            old_status = task.status.value if hasattr(task.status, 'value') else str(task.status)

            if old_status == new_status:
                logger.debug(f"Task {task_id} already has status: {new_status}")
                return

            # Update task status
            from ..planning.models import TaskStatus
            task.status = TaskStatus(new_status)
            parser.save(task)

            logger.info(f"Updated {task_id}: {old_status} -> {new_status}")

        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")

    return update_task


def create_agent_assigner(
    api_key: str,
    token: str,
    agent_name: str = "claude",
    auto_start: bool = True,
    paircoder_dir: Optional[Path] = None,
) -> Callable[[CardMoveEvent], None]:
    """Create a callback that assigns agents when cards move to Ready.

    When a card moves to "Planned / Ready", this callback will:
    1. Add an "Agent: <name>" label to the card
    2. Add a comment indicating assignment
    3. Optionally move the card to "In Progress" and start the task

    Args:
        api_key: Trello API key
        token: Trello API token
        agent_name: Name of the agent (default: "claude")
        auto_start: If True, automatically move card to In Progress
        paircoder_dir: Path to .paircoder directory (for task updates)

    Returns:
        Callback function for card move events
    """
    import requests
    from datetime import datetime

    def is_ready_list(list_name: str) -> bool:
        """Check if list matches ready patterns with flexible matching."""
        import re
        normalized = re.sub(r'\s*/\s*', '/', list_name).strip()
        for ready in READY_LISTS:
            ready_normalized = re.sub(r'\s*/\s*', '/', ready).strip()
            if normalized == ready_normalized:
                return True
        # Also check for keyword
        return "ready" in list_name.lower()

    def assign_agent(event: CardMoveEvent) -> None:
        """Assign agent to card when it moves to Ready."""
        # Only trigger on moves TO a Ready list
        if not is_ready_list(event.list_after):
            return

        task_id = event.task_id
        card_id = event.card_id

        logger.info(f"Agent assignment triggered for {task_id or event.card_name}")

        # Add comment to card
        comment = f"🤖 Agent '{agent_name}' assigned at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        comment_url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
        try:
            response = requests.post(
                comment_url,
                params={"key": api_key, "token": token, "text": comment}
            )
            if response.status_code == 200:
                logger.info(f"Added assignment comment to card {card_id}")
            else:
                logger.warning(f"Failed to add comment: {response.status_code}")
        except Exception as e:
            logger.error(f"Error adding comment: {e}")

        # Get or create agent label
        try:
            # Get board labels
            board_url = f"https://api.trello.com/1/boards/{event.board_id}/labels"
            response = requests.get(
                board_url,
                params={"key": api_key, "token": token}
            )
            labels = response.json() if response.status_code == 200 else []

            # Find or create agent label
            agent_label_name = f"Agent: {agent_name}"
            agent_label = None
            for label in labels:
                if label.get("name") == agent_label_name:
                    agent_label = label
                    break

            if not agent_label:
                # Create label (purple for AI)
                create_label_url = f"https://api.trello.com/1/boards/{event.board_id}/labels"
                response = requests.post(
                    create_label_url,
                    params={
                        "key": api_key,
                        "token": token,
                        "name": agent_label_name,
                        "color": "purple"
                    }
                )
                if response.status_code == 200:
                    agent_label = response.json()
                    logger.info(f"Created agent label: {agent_label_name}")

            # Add label to card
            if agent_label:
                add_label_url = f"https://api.trello.com/1/cards/{card_id}/idLabels"
                response = requests.post(
                    add_label_url,
                    params={
                        "key": api_key,
                        "token": token,
                        "value": agent_label["id"]
                    }
                )
                if response.status_code == 200:
                    logger.info(f"Added agent label to card {card_id}")

        except Exception as e:
            logger.error(f"Error managing labels: {e}")

        # Auto-start: move to In Progress
        if auto_start:
            try:
                # Get board lists
                lists_url = f"https://api.trello.com/1/boards/{event.board_id}/lists"
                response = requests.get(
                    lists_url,
                    params={"key": api_key, "token": token}
                )
                if response.status_code == 200:
                    lists = response.json()
                    in_progress_list = None
                    for lst in lists:
                        if lst.get("name") == "In Progress":
                            in_progress_list = lst
                            break

                    if in_progress_list:
                        # Move card
                        move_url = f"https://api.trello.com/1/cards/{card_id}"
                        response = requests.put(
                            move_url,
                            params={
                                "key": api_key,
                                "token": token,
                                "idList": in_progress_list["id"]
                            }
                        )
                        if response.status_code == 200:
                            logger.info("Moved card to In Progress")

                            # Update local task status
                            if paircoder_dir and task_id:
                                from ..planning.parser import TaskParser
                                from ..planning.models import TaskStatus

                                parser = TaskParser(paircoder_dir / "tasks")
                                task = parser.get_task_by_id(task_id)
                                if task:
                                    task.status = TaskStatus.IN_PROGRESS
                                    parser.save(task)
                                    logger.info(f"Updated local task {task_id} to in_progress")

            except Exception as e:
                logger.error(f"Error auto-starting task: {e}")

    return assign_agent


def create_combined_handler(
    paircoder_dir: Path,
    api_key: Optional[str] = None,
    token: Optional[str] = None,
    agent_name: str = "claude",
    auto_assign: bool = True,
) -> Callable[[CardMoveEvent], None]:
    """Create a combined handler for status updates and agent assignment.

    Args:
        paircoder_dir: Path to .paircoder directory
        api_key: Trello API key (required for agent assignment)
        token: Trello API token (required for agent assignment)
        agent_name: Name of the agent
        auto_assign: Enable automatic agent assignment

    Returns:
        Combined callback function
    """
    # Always create status updater
    status_updater = create_task_updater(paircoder_dir)

    # Optionally create agent assigner
    agent_assigner = None
    if auto_assign and api_key and token:
        agent_assigner = create_agent_assigner(
            api_key=api_key,
            token=token,
            agent_name=agent_name,
            auto_start=True,
            paircoder_dir=paircoder_dir,
        )

    def combined_handler(event: CardMoveEvent) -> None:
        """Handle card move with both status update and agent assignment."""
        # Update local task status
        status_updater(event)

        # Assign agent if enabled and moving to Ready
        if agent_assigner:
            agent_assigner(event)

    return combined_handler
