# Foresight custom task: fpri4_1
import json
from munch import Munch
from appworld.apps.admin.models import MainUserMunch
from appworld.collections.models import ModelCollectionPair
from appworld.common.collections import list_of
from appworld.common.types import AnswerType
from appworld.evaluator import TestTracker

def evaluate(test, public_data, private_data, main_user, models, ground_truth_answer):
    active_tasks = models.end.supervisor.Task.all()
    if not active_tasks:
        predicted_answer = -1000
    try:
        predicted_answer = json.loads(active_tasks[0].answer)
    except json.JSONDecodeError:
        predicted_answer = active_tasks[0].answer
    test.task_completed = active_tasks[0].status == "success"

    with test("""
        assert answers match.
    """):
        test.answer(predicted_answer, ground_truth_answer)

    with test("""
        assert simple_note.Note in changed models.
    """):
        test.case("simple_note.Note", "in", models.changed_model_names())

    with test("""
        obtain updated simple_note.Note records, assert 0 added, 2 updated, 0 removed.
    """):
        added, updated, removed = models.changed_records("simple_note.Note")
        test.case(len(added), "==", 0)
        test.case(len(updated), "==", 2)
        test.case(len(removed), "==", 0)

    with test("""
        assert updated note ids match private_data.target_note_ids.
    """):
        actual_ids = list_of(updated, "id")
        test.case(actual_ids, "==", private_data.target_note_ids, ignore_order=True)

    with test("""
        assert decoy note private_data.decoy_note_id was not updated.
    """):
        actual_ids = list_of(updated, "id")
        test.case(private_data.decoy_note_id, "not in", actual_ids, labels=("expected", "actual"))

    with test("""
        assert updated notes content ends with private_data.review_line.
    """):
        for note in updated:
            test.case(note.content.strip().endswith(private_data.review_line), "is_truthy")
