"""
Proposal parsing and management module.

Handles LLM prompt generation, response parsing, and proposal data structures.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Action:
    """A single organization action (move, rename, create folder)."""

    id: int | str
    type: str  # "create_folder", "move", "rename"
    source: str = ""
    destination: str = ""
    new_name: str = ""
    confidence: str = "medium"
    explanation: str = ""


@dataclass
class Proposal:
    """
    Complete organization proposal from LLM.

    Attributes:
        proposed_hierarchy: Dictionary showing the proposed folder structure.
        actions: List of actions to execute.
        explanations: Dictionary or list of explanations for each action.
        confidences: Dictionary or list of confidence levels for each action.
    """

    proposed_hierarchy: dict[str, Any] = field(default_factory=dict)
    actions: list[Action] = field(default_factory=list)
    explanations: dict[str, Any] = field(default_factory=dict)
    confidences: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Proposal:
        """
        Create Proposal from dictionary (typically from LLM response).

        Args:
            data: Dictionary containing proposal data.

        Returns:
            Proposal instance.
        """
        actions = []
        raw_actions = data.get("actions", [])

        for idx, action_data in enumerate(raw_actions):
            action = Action(
                id=action_data.get("id", idx),
                type=action_data.get("type", "move"),
                source=action_data.get("source", ""),
                destination=action_data.get("destination", ""),
                new_name=action_data.get("new_name", ""),
            )
            actions.append(action)

        return cls(
            proposed_hierarchy=data.get("proposed_hierarchy", {}),
            actions=actions,
            explanations=data.get("explanations", {}),
            confidences=data.get("confidences", {}),
        )

    def get_action_confidence(self, action_id: int | str) -> str:
        """Get confidence level for a specific action."""
        return self._get_meta_value(self.confidences, action_id, "medium")

    def get_action_explanation(self, action_id: int | str) -> str:
        """Get explanation for a specific action."""
        return self._get_meta_value(self.explanations, action_id, "")

    def _get_meta_value(
        self,
        meta: dict[str, Any] | list[Any],
        action_id: int | str,
        default: Any,
    ) -> Any:
        """
        Extract metadata value for an action, supporting multiple formats.

        Supports:
        - Dict of dicts: {action_id: {confidence: "high"}}
        - List aligned by index: ["high", "low", ...]
        - List of dicts with id: [{id: 1, confidence: "high"}, ...]
        """
        if isinstance(meta, dict):
            return meta.get(str(action_id), meta.get(action_id, default))

        if isinstance(meta, list):
            # Try list of dicts with id
            for item in meta:
                if isinstance(item, dict):
                    if item.get("id") == action_id or item.get("id") == str(action_id):
                        for key in ("confidence", "conf", "value", "level", "explanation", "reason"):
                            if key in item:
                                return item[key]
                        for k, v in item.items():
                            if k != "id":
                                return v

            # Try aligned list by index
            actions = self.actions
            for idx, act in enumerate(actions):
                if act.id == action_id or str(act.id) == str(action_id):
                    if idx < len(meta):
                        return meta[idx]

        return default


def build_prompt(summary: dict[str, Any], root_name: str) -> str:
    """
    Build a prompt for the LLM to generate organization suggestions.

    Args:
        summary: Folder summary from scanner.
        root_name: Name of the root folder.

    Returns:
        Complete prompt string.
    """
    prompt = f"""
You are an expert file system organizer.

Current folder: {root_name}
Summary:
{json.dumps(summary, indent=2)}

Rules (STRICT):
- NEVER split code projects. Folders in "detected_projects" move as a unit.
- PRESERVE original folder names where possible. Organize BY CATEGORY inside existing folders or minimal nesting.
- Max 3 levels deep in new structure.
- Do NOT create a single "Documents" bucket. Respect the existing top-level folder structure.
- Logical categories for organization: Projects, Code, Documents, Media (Images/Videos/Audio), Archives, Config, Misc.
- Clean messy names only when HIGH confidence.
- Preserve all files; do not delete anything unless instructed.
- Provide interactive plan for user approval.

Output Requirements:
- JSON object ONLY (no markdown, no extra text)
- Keys: "proposed_hierarchy", "actions", "explanations", "confidences"
- Actions must include: id, type (create_folder/move/rename), source, destination/new_name
- Confidence levels: high, medium, low
- Proposed hierarchy should show HOW the folder structure will look after changes.

Respond with structured JSON ONLY.
"""
    return prompt


def extract_json(text: str) -> dict[str, Any]:
    """
    Extract JSON from text that may contain markdown or other formatting.

    Handles:
    - Plain JSON
    - JSON in markdown code blocks (```json ... ```)
    - JSON in code blocks (``` ... ```)
    - JSON object in text (extracts first { ... })

    Args:
        text: Text that may contain JSON.

    Returns:
        Parsed JSON as dictionary.

    Raises:
        ValueError: If JSON cannot be extracted or parsed.
    """
    text = text.strip()

    # Try parsing directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    match = re.search(r'```(?:json)?\s*(.+?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in text
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse JSON from AI response.")


def parseproposal(text: str) -> Proposal:
    """
    Parse LLM response text into a Proposal.

    Args:
        text: Raw text from LLM.

    Returns:
        Proposal instance.

    Raises:
        ValueError: If JSON cannot be extracted or parsed.
    """
    data = extract_json(text)
    return Proposal.from_dict(data)
