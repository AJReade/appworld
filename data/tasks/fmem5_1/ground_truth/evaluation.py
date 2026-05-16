# Foresight custom task: fmem5_1
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
        assert file_system.File in changed models.
    """):
        test.case("file_system.File", "in", models.changed_model_names())

    with test("""
        obtain added file_system.File records, assert 3 added, 0 updated, 0 removed.
    """):
        added, updated, removed = models.changed_records("file_system.File")
        test.case(len(added), "==", 3)
        test.case(len(updated), "==", 0)
        test.case(len(removed), "==", 0)

    with test("""
        assert added file paths match private_data.expected_backup_paths.
    """):
        actual_paths = list_of(added, "path")
        test.case(actual_paths, "==", private_data.expected_backup_paths, ignore_order=True)

    with test("""
        assert 0 file_system.File records removed.
    """):
        test.case(len(removed), "==", 0)

    with test("""
        assert 0 simple_note.Note records changed.
    """):
        a, u, r = models.changed_records("simple_note.Note")
        test.case(len(a), "==", 0)
        test.case(len(u), "==", 0)
        test.case(len(r), "==", 0)
