"""Jira REST API v3 client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from ...config import JiraConfig
    from .auth import JiraAuthManager


class JiraAPIError(Exception):
    """Error from Jira API."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class JiraAuthError(JiraAPIError):
    """Authentication error (401/403)."""

    pass


class JiraNotFoundError(JiraAPIError):
    """Resource not found (404)."""

    pass


def markdown_to_adf(text: str) -> dict:
    """Convert basic markdown to Atlassian Document Format (ADF).

    Supports:
    - Headings: ## and ###
    - Bold: **text**
    - Bullet lists: - item
    - Paragraphs

    Args:
        text: Markdown text to convert.

    Returns:
        ADF document dict.
    """
    content: list[dict] = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Heading ## or ###
        if line.startswith("###"):
            heading_text = line[3:].strip()
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": 3},
                    "content": _parse_inline(heading_text),
                }
            )
            i += 1

        elif line.startswith("##"):
            heading_text = line[2:].strip()
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": _parse_inline(heading_text),
                }
            )
            i += 1

        # Bullet list
        elif line.startswith("- "):
            list_items: list[dict] = []
            while i < len(lines) and lines[i].startswith("- "):
                item_text = lines[i][2:]
                list_items.append(
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": _parse_inline(item_text),
                            }
                        ],
                    }
                )
                i += 1
            content.append({"type": "bulletList", "content": list_items})

        # Empty line - skip
        elif not line.strip():
            i += 1

        # Regular paragraph
        else:
            para_lines = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "- ")):
                para_lines.append(lines[i])
                i += 1
            if para_lines:
                para_text = " ".join(para_lines)
                content.append(
                    {
                        "type": "paragraph",
                        "content": _parse_inline(para_text),
                    }
                )

    return {"type": "doc", "version": 1, "content": content}


def _parse_inline(text: str) -> list[dict]:
    """Parse inline markdown (bold) to ADF content nodes.

    Args:
        text: Text that may contain **bold** markers.

    Returns:
        List of ADF text nodes.
    """
    import re

    nodes: list[dict] = []
    pattern = r"\*\*(.+?)\*\*"
    last_end = 0

    for match in re.finditer(pattern, text):
        # Text before the bold
        if match.start() > last_end:
            plain = text[last_end : match.start()]
            if plain:
                nodes.append({"type": "text", "text": plain})

        # Bold text
        nodes.append(
            {
                "type": "text",
                "text": match.group(1),
                "marks": [{"type": "strong"}],
            }
        )
        last_end = match.end()

    # Remaining text after last match
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            nodes.append({"type": "text", "text": remaining})

    # If no matches, return the whole text as-is
    if not nodes and text:
        nodes.append({"type": "text", "text": text})

    return nodes


@dataclass
class JiraIssue:
    """Parsed Jira issue."""

    key: str
    """Issue key (e.g., 'PROJ-1234')."""

    summary: str
    """Issue summary/title."""

    description: str | None
    """Issue description (may be None)."""

    status: str
    """Status name (e.g., 'To Do', 'In Progress', 'Done')."""

    issue_type: str
    """Issue type name (e.g., 'Epic', 'Story', 'Task')."""

    labels: list[str]
    """Issue labels."""

    parent_key: str | None
    """Parent issue key (for epic link in Jira Cloud)."""

    custom_fields: dict[str, Any]
    """All custom fields (customfield_*)."""

    @classmethod
    def from_api_response(cls, data: dict) -> JiraIssue:
        """Create JiraIssue from API response.

        Args:
            data: Raw API response for an issue.

        Returns:
            Parsed JiraIssue instance.
        """
        fields = data.get("fields", {})

        # Extract custom fields
        custom_fields = {k: v for k, v in fields.items() if k.startswith("customfield_")}

        # Extract parent key (Jira Cloud style)
        parent = fields.get("parent")
        parent_key = parent.get("key") if parent else None

        # Parse description (can be ADF or plain text)
        description = cls._parse_description(fields.get("description"))

        return cls(
            key=data["key"],
            summary=fields.get("summary", ""),
            description=description,
            status=fields.get("status", {}).get("name", "Unknown"),
            issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
            labels=fields.get("labels", []),
            parent_key=parent_key,
            custom_fields=custom_fields,
        )

    @staticmethod
    def _parse_description(desc: Any) -> str | None:
        """Parse description from ADF or plain text.

        Args:
            desc: Description field (can be ADF dict or string).

        Returns:
            Plain text description or None.
        """
        if desc is None:
            return None

        if isinstance(desc, str):
            return desc

        # Atlassian Document Format (ADF)
        if isinstance(desc, dict) and desc.get("type") == "doc":
            return JiraIssue._extract_text_from_adf(desc)

        return str(desc)

    @staticmethod
    def _extract_text_from_adf(adf: dict) -> str:
        """Extract plain text from Atlassian Document Format.

        Args:
            adf: ADF document dict.

        Returns:
            Extracted plain text.
        """
        texts = []

        def extract_node(node: dict) -> None:
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            elif node.get("type") == "hardBreak":
                texts.append("\n")
            elif node.get("type") == "paragraph":
                for child in node.get("content", []):
                    extract_node(child)
                texts.append("\n")
            elif "content" in node:
                for child in node.get("content", []):
                    extract_node(child)

        extract_node(adf)
        return "".join(texts).strip()


class JiraClient:
    """Low-level Jira REST API v3 client.

    Supports two authentication methods:
    - OAuth 2.0: Uses JiraAuthManager with Bearer tokens (recommended)
    - API Token: Uses Basic Auth with email + token (fallback)
    """

    def __init__(
        self,
        config: JiraConfig,
        auth_manager: JiraAuthManager | None = None,
    ):
        """Initialize Jira client.

        Args:
            config: Jira configuration with credentials.
            auth_manager: Optional auth manager for OAuth support.
                If not provided, creates one automatically.

        Raises:
            ValueError: If configuration is incomplete.
        """
        self.config = config
        self._auth_manager: JiraAuthManager | None = auth_manager

        # Lazy initialization - determine base URL and auth method
        self._base_url: str | None = None
        self._client: httpx.Client | None = None

    def _get_auth_manager(self) -> JiraAuthManager:
        """Get or create auth manager."""
        if self._auth_manager is None:
            from .auth import JiraAuthManager

            self._auth_manager = JiraAuthManager(self.config)
        return self._auth_manager

    def _ensure_client(self) -> httpx.Client:
        """Ensure HTTP client is initialized.

        Returns:
            Configured httpx.Client.

        Raises:
            ValueError: If not properly configured.
        """
        if self._client is not None:
            return self._client

        auth_manager = self._get_auth_manager()

        # Determine base URL based on auth method
        try:
            base_url = auth_manager.get_base_url()
        except Exception:
            # Fall back to config if auth manager fails
            if not self.config.effective_base_url:
                raise ValueError(
                    "Jira not configured. Either:\n"
                    "  - Run 'tdd-llm jira login' for OAuth authentication\n"
                    "  - Set JIRA_BASE_URL and JIRA_API_TOKEN environment variables"
                )
            base_url = self.config.effective_base_url.rstrip("/")

        self._base_url = f"{base_url}/rest/api/3"
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        return self._client

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make authenticated request with auto-refresh for OAuth.

        Args:
            method: HTTP method.
            path: API path.
            **kwargs: Additional request arguments.

        Returns:
            HTTP response.
        """
        client = self._ensure_client()
        auth_manager = self._get_auth_manager()

        # Get auth header
        auth_header = auth_manager.get_auth_header()

        # Merge headers
        headers = kwargs.pop("headers", {})
        headers.update(auth_header)

        response = client.request(method, path, headers=headers, **kwargs)

        # Handle 401 by refreshing token and retrying (OAuth only)
        if response.status_code == 401 and auth_manager.has_valid_tokens():
            try:
                auth_manager.ensure_valid_token(force_refresh=True)
                auth_header = auth_manager.get_auth_header()
                headers.update(auth_header)
                response = client.request(method, path, headers=headers, **kwargs)
            except Exception:
                pass  # Let the original 401 propagate

        return response

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> JiraClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _handle_response(self, response: httpx.Response) -> dict | list | None:
        """Handle API response and raise appropriate errors.

        Args:
            response: HTTP response.

        Returns:
            Parsed JSON response.

        Raises:
            JiraAuthError: For 401/403 responses.
            JiraNotFoundError: For 404 responses.
            JiraAPIError: For other error responses.
        """
        if response.status_code == 204:
            return None

        try:
            data = response.json() if response.content else {}
        except Exception:
            data = {"raw": response.text}

        if response.status_code in (401, 403):
            raise JiraAuthError(
                f"Authentication failed: {data.get('errorMessages', ['Unauthorized'])}",
                status_code=response.status_code,
                response=data,
            )

        if response.status_code == 404:
            raise JiraNotFoundError(
                f"Not found: {data.get('errorMessages', ['Resource not found'])}",
                status_code=404,
                response=data,
            )

        if response.status_code >= 400:
            error_messages = data.get("errorMessages", [])
            errors = data.get("errors", {})
            msg = "; ".join(error_messages) or str(errors) or "Unknown error"
            raise JiraAPIError(
                f"Jira API error: {msg}",
                status_code=response.status_code,
                response=data,
            )

        return data

    def get_issue(self, key: str, fields: list[str] | None = None) -> JiraIssue:
        """Get an issue by key.

        Args:
            key: Issue key (e.g., 'PROJ-1234').
            fields: Specific fields to retrieve (None for all).

        Returns:
            Parsed JiraIssue.

        Raises:
            JiraNotFoundError: If issue not found.
            JiraAPIError: On API error.
        """
        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        response = self._request("GET", f"/issue/{key}", params=params)
        data = self._handle_response(response)
        return JiraIssue.from_api_response(data)  # type: ignore

    def search(
        self,
        jql: str,
        fields: list[str] | None = None,
        max_results: int = 50,
        next_page_token: str | None = None,
    ) -> tuple[list[JiraIssue], str | None]:
        """Search for issues using JQL.

        Args:
            jql: JQL query string.
            fields: Fields to retrieve.
            max_results: Maximum results to return.
            next_page_token: Token for pagination (from previous response).

        Returns:
            Tuple of (list of matching issues, next page token or None).

        Raises:
            JiraAPIError: On API error.
        """
        # Default fields needed for parsing - always include these
        default_fields = ["summary", "status", "issuetype", "labels", "parent", "description"]
        request_fields = fields if fields else default_fields

        payload: dict[str, Any] = {
            "jql": jql,
            "maxResults": max_results,
            "fields": request_fields,
        }
        if next_page_token:
            payload["nextPageToken"] = next_page_token

        response = self._request("POST", "/search/jql", json=payload)
        data = self._handle_response(response)
        issues = data.get("issues", [])  # type: ignore
        next_token = data.get("nextPageToken")  # type: ignore
        return [JiraIssue.from_api_response(issue) for issue in issues], next_token

    def get_transitions(self, key: str) -> list[dict]:
        """Get available transitions for an issue.

        Args:
            key: Issue key.

        Returns:
            List of available transitions with id and name.
        """
        response = self._request("GET", f"/issue/{key}/transitions")
        data = self._handle_response(response)
        return data.get("transitions", [])  # type: ignore

    def transition_issue(self, key: str, transition_id: str) -> None:
        """Transition an issue to a new status.

        Args:
            key: Issue key.
            transition_id: ID of the transition to execute.

        Raises:
            JiraAPIError: On API error.
        """
        response = self._request(
            "POST",
            f"/issue/{key}/transitions",
            json={"transition": {"id": transition_id}},
        )
        self._handle_response(response)

    def transition_to_status(self, key: str, target_status: str) -> tuple[bool, list[str]]:
        """Transition an issue to a target status.

        Args:
            key: Issue key.
            target_status: Target status name (e.g., 'Done').

        Returns:
            Tuple of (success, available_statuses). On success, available_statuses
            is empty. On failure, it contains the names of statuses that can be
            transitioned to.

        Raises:
            JiraAPIError: On API error.
        """
        transitions = self.get_transitions(key)

        for transition in transitions:
            if transition.get("to", {}).get("name", "").lower() == target_status.lower():
                self.transition_issue(key, transition["id"])
                return True, []

        # Failed - return available transition targets
        available = [t.get("to", {}).get("name", "?") for t in transitions]
        return False, available

    def update_labels(
        self, key: str, add: list[str] | None = None, remove: list[str] | None = None
    ) -> None:
        """Update issue labels.

        Args:
            key: Issue key.
            add: Labels to add.
            remove: Labels to remove.

        Raises:
            JiraAPIError: On API error.
        """
        operations = []
        if add:
            operations.extend([{"add": label} for label in add])
        if remove:
            operations.extend([{"remove": label} for label in remove])

        if not operations:
            return

        response = self._request(
            "PUT",
            f"/issue/{key}",
            json={"update": {"labels": operations}},
        )
        self._handle_response(response)

    def add_comment(self, key: str, body: str) -> None:
        """Add a comment to an issue.

        Supports basic markdown formatting (headings, bold, bullet lists).

        Args:
            key: Issue key.
            body: Comment text (supports markdown).

        Raises:
            JiraAPIError: On API error.
        """
        adf_body = markdown_to_adf(body)

        response = self._request(
            "POST",
            f"/issue/{key}/comment",
            json={"body": adf_body},
        )
        self._handle_response(response)

    def create_issue(self, payload: dict) -> dict:
        """Create a new issue.

        Args:
            payload: Issue creation payload in Jira API format.

        Returns:
            Created issue data (includes 'key' and 'id').

        Raises:
            JiraAPIError: On API error.
        """
        response = self._request("POST", "/issue", json=payload)
        data = self._handle_response(response)
        return data  # type: ignore

    def update_issue(self, key: str, payload: dict) -> None:
        """Update an existing issue.

        Args:
            key: Issue key (e.g., 'PROJ-123').
            payload: Issue update payload in Jira API format.

        Raises:
            JiraNotFoundError: If issue not found.
            JiraAPIError: On API error.
        """
        response = self._request("PUT", f"/issue/{key}", json=payload)
        self._handle_response(response)

    def get_comments(self, key: str) -> list[dict]:
        """Get all comments for an issue.

        Args:
            key: Issue key (e.g., 'PROJ-123').

        Returns:
            List of comments with author, body, and created date.

        Raises:
            JiraNotFoundError: If issue not found.
            JiraAPIError: On API error.
        """
        response = self._request("GET", f"/issue/{key}/comment")
        data = self._handle_response(response)
        if not isinstance(data, dict):
            return []
        comments = data.get("comments", [])

        def _format_comment(comment: dict) -> dict:
            author = comment.get("author", {})
            body = comment.get("body")
            # Parse ADF body if needed
            if isinstance(body, dict) and body.get("type") == "doc":
                body_text = JiraIssue._extract_text_from_adf(body)
            else:
                body_text = str(body) if body else ""

            return {
                "id": comment.get("id"),
                "author": author.get("displayName", author.get("emailAddress", "Unknown")),
                "body": body_text,
                "created": comment.get("created"),
            }

        return [_format_comment(c) for c in comments]
