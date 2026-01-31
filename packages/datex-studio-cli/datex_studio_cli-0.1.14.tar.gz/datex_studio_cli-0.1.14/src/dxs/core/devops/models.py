"""Pydantic models for Azure DevOps API responses."""

import re
from typing import Any

from markdownify import markdownify as md
from pydantic import BaseModel, Field


def _html_to_markdown(html: str) -> str:
    """Convert HTML to clean markdown.

    Args:
        html: HTML string from Azure DevOps

    Returns:
        Clean markdown string
    """
    if not html:
        return ""

    # Convert HTML to markdown
    markdown = md(html, heading_style="ATX", strip=["script", "style"])

    # Clean up excessive whitespace
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)  # Max 2 newlines
    markdown = re.sub(r"[ \t]+\n", "\n", markdown)  # Trailing spaces
    markdown = markdown.strip()

    return markdown


class DevOpsWorkItemDto(BaseModel):
    """Azure DevOps work item information."""

    id: int
    rev: int = 1
    url: str | None = None
    fields: dict[str, Any] = Field(default_factory=dict)
    discussions: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"populate_by_name": True}

    @property
    def title(self) -> str:
        """Get work item title."""
        return str(self.fields.get("System.Title", ""))

    @property
    def work_item_type(self) -> str:
        """Get work item type (Bug, Task, User Story, etc.)."""
        return str(self.fields.get("System.WorkItemType", ""))

    @property
    def state(self) -> str:
        """Get work item state (New, Active, Resolved, Closed, etc.)."""
        return str(self.fields.get("System.State", ""))

    @property
    def description(self) -> str:
        """Get work item description (HTML)."""
        return str(self.fields.get("System.Description", ""))

    @property
    def assigned_to(self) -> str:
        """Get assigned user display name."""
        assigned = self.fields.get("System.AssignedTo", {})
        if isinstance(assigned, dict):
            return str(assigned.get("displayName", ""))
        return str(assigned) if assigned else ""

    @property
    def created_date(self) -> str:
        """Get created date."""
        return str(self.fields.get("System.CreatedDate", ""))

    @property
    def changed_date(self) -> str:
        """Get last changed date."""
        return str(self.fields.get("System.ChangedDate", ""))

    @property
    def tags(self) -> list[str]:
        """Get work item tags."""
        tags_str = self.fields.get("System.Tags", "")
        if tags_str:
            return [t.strip() for t in tags_str.split(";") if t.strip()]
        return []

    @property
    def area_path(self) -> str:
        """Get area path."""
        return str(self.fields.get("System.AreaPath", ""))

    @property
    def iteration_path(self) -> str:
        """Get iteration path."""
        return str(self.fields.get("System.IterationPath", ""))

    def to_summary(
        self, include_description: bool = False, include_discussions: bool = False
    ) -> dict[str, Any]:
        """Convert to a summary dict for CLI output.

        Args:
            include_description: Include description field (converted to markdown)
            include_discussions: Include discussions array
        """
        summary = {
            "id": self.id,
            "title": self.title,
            "type": self.work_item_type,
            "state": self.state,
            "assigned_to": self.assigned_to,
            "tags": self.tags,
            "area_path": self.area_path,
            "iteration_path": self.iteration_path,
            "created_date": self.created_date,
            "changed_date": self.changed_date,
            "url": self.url,
        }

        # Conditionally add description (converted from HTML to markdown)
        if include_description:
            summary["description"] = _html_to_markdown(self.description)

        # Conditionally add discussions (with HTML converted to markdown)
        if include_discussions:
            # Simplify discussion structure for CLI output
            summary["discussions"] = [
                {
                    "text": _html_to_markdown(d.get("text", "")),
                    "created_by": d.get("createdBy", {}).get("displayName", ""),
                    "created_date": d.get("createdDate", ""),
                }
                for d in self.discussions
            ]
            summary["discussion_count"] = len(self.discussions)

        return summary
