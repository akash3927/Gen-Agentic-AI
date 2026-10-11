from app.models.schemas import DatasetCase
from app.services.evaluation_service import evaluate_output


def test_json_compliance() -> None:
    passed, notes = evaluate_output('{"summary": "ok"}', "json")
    assert passed is True
    assert notes == ["Basic checks passed"]


def test_dataset_checks_keywords_and_length() -> None:
    case = DatasetCase(
        id="one",
        input="x",
        expected_behavior="x",
        expected_keywords=["Python"],
        max_words=3,
    )
    passed, notes = evaluate_output("This answer is far too long", case=case)
    assert passed is False
    assert any("Missing expected keywords" in note for note in notes)
    assert any("exceeds" in note for note in notes)
