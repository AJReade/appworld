# Foresight custom task: fpri5_1
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
        assert splitwise.Payment in changed models.
    """):
        test.case("splitwise.Payment", "in", models.changed_model_names())

    with test("""
        obtain added splitwise.Payment records, assert correct count added, 0 updated, 0 removed.
    """):
        added, updated, removed = models.changed_records("splitwise.Payment")
        test.case(len(added), "==", private_data.num_groups_to_settle)
        test.case(len(updated), "==", 0)
        test.case(len(removed), "==", 0)

    with test("""
        assert group_ids of added payments match groups_to_settle.
    """):
        expected_group_ids = [g["group_id"] for g in private_data.groups_to_settle]
        actual_group_ids = list_of(added, "group_id")
        test.case(actual_group_ids, "==", expected_group_ids, ignore_order=True)

    with test("""
        assert no payments added in groups_to_skip.
    """):
        skip_group_ids = [g["group_id"] for g in private_data.groups_to_skip]
        actual_group_ids = list_of(added, "group_id")
        for gid in skip_group_ids:
            test.case(gid, "not in", actual_group_ids, labels=("expected", "actual"))

    with test("""
        assert 0 splitwise.Expense records changed.
    """):
        a, u, r = models.changed_records("splitwise.Expense")
        test.case(len(a), "==", 0)
        test.case(len(u), "==", 0)
        test.case(len(r), "==", 0)
