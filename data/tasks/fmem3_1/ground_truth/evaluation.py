# Foresight custom task: fmem3_1
import json
from munch import Munch
from appworld.apps.admin.models import MainUserMunch
from appworld.collections.models import ModelCollectionPair
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
        obtain updated venmo.PaymentRequest, assert 0 added, 1 updated, 0 removed.
    """):
        added, updated, removed = models.changed_records("venmo.PaymentRequest")
        test.case(len(added), "==", 0)
        test.case(len(updated), "==", 1)
        test.case(len(removed), "==", 0)

    with test("""
        assert the updated request sender_id matches private_data.payment_request_sender_venmo_id.
    """):
        test.case(updated[0].sender_id, "==", private_data.payment_request_sender_venmo_id)

    with test("""
        assert the updated request was approved.
    """):
        test.case(updated[0].approved_at, "is not", None)
        test.case(updated[0].denied_at, "is", None)

    with test("""
        assert 0 venmo.Transaction records were added or removed.
    """):
        a, u, r = models.changed_records("venmo.Transaction")
        test.case(len(a), "==", 0)
        test.case(len(r), "==", 0)
