# Foresight custom task: fdep1_1
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
        assert model changes match venmo.Transaction.
    """):
        test.case("venmo.Transaction", "in", models.changed_model_names())

    with test("""
        obtain added venmo.Transaction, assert 1 added, 0 updated, 0 removed.
    """):
        added, updated, removed = models.changed_records("venmo.Transaction")
        test.case(len(added), "==", 1)
        test.case(len(updated), "==", 0)
        test.case(len(removed), "==", 0)

    with test("""
        assert the added transaction receiver_id is private_data.overpayer_venmo_id.
    """):
        test.case(added[0].receiver_id, "==", private_data.overpayer_venmo_id)

    with test("""
        assert the added transaction amount is private_data.refund_amount.
    """):
        test.case(added[0].amount, "==", private_data.refund_amount, tolerance=0.51)

    with test("""
        assert 0 venmo.PaymentRequest records changed.
    """):
        a, u, r = models.changed_records("venmo.PaymentRequest")
        test.case(len(a), "==", 0)
        test.case(len(u), "==", 0)
        test.case(len(r), "==", 0)
