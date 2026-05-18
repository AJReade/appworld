# Foresight custom task: fpri1_1 — Triage payment requests by description
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
        assert venmo.PaymentRequest in changed models.
    """):
        test.case("venmo.PaymentRequest", "in", models.changed_model_names())

    with test("""
        obtain updated venmo.PaymentRequest, assert exactly 3 updated, 0 added, 0 removed.
    """):
        added, updated, removed = models.changed_records("venmo.PaymentRequest")
        test.case(len(updated), "==", private_data.num_rent_requests)
        test.case(len(added), "==", 0)
        test.case(len(removed), "==", 0)

    with test("""
        assert updated requests are the rent ones by checking their IDs.
    """):
        updated_ids = list_of(updated, "id")
        test.case(updated_ids, "==", private_data.rent_request_ids, ignore_order=True)

    with test("""
        assert all updated requests were approved.
    """):
        for req in updated:
            test.case(req.approved_at, "is not", None)
            test.case(req.denied_at, "is", None)

    with test("""
        assert non-rent requests were not modified.
    """):
        updated_ids = set(list_of(updated, "id"))
        for nid in private_data.non_rent_request_ids:
            test.case(nid, "not in", updated_ids, labels=("expected", "actual"))
