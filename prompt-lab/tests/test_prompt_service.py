import pytest

from app.services.prompt_service import PromptService


def test_render_replaces_variables() -> None:
    rendered = PromptService.render("Hello {name}, do {task}.", {"name": "Ada", "task": "a review"})
    assert rendered == "Hello Ada, do a review."


def test_render_reports_missing_variables() -> None:
    with pytest.raises(ValueError, match="Missing template variables: task"):
        PromptService.render("Do {task}", {})
