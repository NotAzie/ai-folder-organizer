"""Tests for proposal module."""

import pytest

from organiser.proposal import (
    Action,
    Proposal,
    build_prompt,
    extract_json,
    parseproposal,
)


class TestAction:
    """Tests for Action dataclass."""

    def test_action_creation(self):
        """Action should store all fields."""
        action = Action(
            id=1,
            type="move",
            source="old.txt",
            destination="newfolder/new.txt",
        )

        assert action.id == 1
        assert action.type == "move"
        assert action.source == "old.txt"
        assert action.destination == "newfolder/new.txt"

    def test_action_default_values(self):
        """Action should have sensible defaults."""
        action = Action(id=1, type="create_folder")

        assert action.source == ""
        assert action.destination == ""
        assert action.new_name == ""
        assert action.confidence == "medium"
        assert action.explanation == ""


class TestProposal:
    """Tests for Proposal dataclass."""

    def test_proposal_from_dict(self):
        """Proposal should parse from dictionary."""
        data = {
            "proposed_hierarchy": {"Projects": ["proj1"]},
            "actions": [
                {"id": 1, "type": "move", "source": "a.txt", "destination": "Projects/proj1/a.txt"},
                {"id": 2, "type": "create_folder", "destination": "Projects"},
            ],
            "confidences": {"1": "high", "2": "medium"},
            "explanations": {"1": "It's a project file"},
        }

        proposal = Proposal.from_dict(data)

        assert len(proposal.actions) == 2
        assert proposal.actions[0].id == 1
        assert proposal.actions[0].type == "move"
        assert proposal.actions[1].type == "create_folder"

    def test_proposal_empty(self):
        """Empty proposal should have no actions."""
        proposal = Proposal()

        assert proposal.proposed_hierarchy == {}
        assert proposal.actions == []
        assert proposal.explanations == {}
        assert proposal.confidences == {}

    def test_get_action_confidence_dict(self):
        """Should get confidence from dict format."""
        proposal = Proposal(
            actions=[Action(id=1, type="move")],
            confidences={"1": "high"},
        )

        assert proposal.get_action_confidence(1) == "high"
        assert proposal.get_action_confidence(999) == "medium"  # default

    def test_get_action_confidence_list(self):
        """Should get confidence from list format."""
        proposal = Proposal(
            actions=[Action(id=1, type="move"), Action(id=2, type="rename")],
            confidences=["high", "low"],
        )

        assert proposal.get_action_confidence(1) == "high"
        assert proposal.get_action_confidence(2) == "low"

    def test_get_action_confidence_list_of_dicts(self):
        """Should get confidence from list of dicts format."""
        proposal = Proposal(
            actions=[Action(id=1, type="move")],
            confidences=[{"id": 1, "confidence": "high"}],
        )

        assert proposal.get_action_confidence(1) == "high"

    def test_get_action_explanation(self):
        """Should get explanation for action."""
        proposal = Proposal(
            actions=[Action(id=1, type="move")],
            explanations={"1": "Because it's a project file"},
        )

        assert proposal.get_action_explanation(1) == "Because it's a project file"
        assert proposal.get_action_explanation(999) == ""  # default


class TestBuildPrompt:
    """Tests for build_prompt function."""

    def test_build_prompt_structure(self):
        """Prompt should have correct structure."""
        summary = {"total_files": 100}
        prompt = build_prompt(summary, "TestFolder")

        assert "TestFolder" in prompt
        assert "total_files" in prompt
        assert "100" in prompt
        assert "JSON object ONLY" in prompt
        assert "proposed_hierarchy" in prompt
        assert "actions" in prompt

    def test_build_prompt_includes_rules(self):
        """Prompt should include organization rules."""
        prompt = build_prompt({}, "Test")

        assert "NEVER split code projects" in prompt
        assert "PRESERVE original folder names" in prompt
        assert "Max 3 levels deep" in prompt


class TestExtractJson:
    """Tests for extract_json function."""

    def test_extract_plain_json(self):
        """Should extract plain JSON."""
        text = '{"key": "value"}'
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_in_code_block(self):
        """Should extract JSON from markdown code block."""
        text = "```json\n{\"key\": \"value\"}\n```"
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_in_code_block_no_lang(self):
        """Should extract JSON from code block without language."""
        text = "```\n{\"key\": \"value\"}\n```"
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_from_text(self):
        """Should extract JSON object from text."""
        text = "Here is the JSON: {\"key\": \"value\"} and more text"
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_raises_on_invalid(self):
        """Should raise ValueError on invalid JSON."""
        text = "This is not JSON at all"
        with pytest.raises(ValueError, match="Could not parse JSON"):
            extract_json(text)


class TestParseProposal:
    """Tests for parseproposal function."""

    def test_parse_proposal(self):
        """Should parse proposal from text."""
        text = '''
        ```json
        {
            "proposed_hierarchy": {"Projects": []},
            "actions": [{"id": 1, "type": "move", "source": "a.txt", "destination": "Projects/a.txt"}],
            "confidences": {"1": "high"},
            "explanations": {"1": "Project file"}
        }
        ```
        '''

        proposal = parseproposal(text)

        assert len(proposal.actions) == 1
        assert proposal.actions[0].id == 1
        assert proposal.actions[0].type == "move"

    def test_parse_proposal_plain_json(self):
        """Should parse plain JSON."""
        text = '{"actions": [{"id": 1, "type": "create_folder", "destination": "New"}]}'

        proposal = parseproposal(text)

        assert len(proposal.actions) == 1
        assert proposal.actions[0].type == "create_folder"
