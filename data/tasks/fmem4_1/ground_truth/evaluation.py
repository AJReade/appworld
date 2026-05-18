# Foresight custom task: fmem4_1 — Bills note to Venmo payments
import json

from munch import Munch

from appworld.apps.admin.models import MainUserMunch
from appworld.collections.models import ModelCollectionPair
from appworld.common.collections import list_of
from appworld.common.types import AnswerType
from appworld.evaluator import TestTracker


def evaluate(
    test: TestTracker,
    public_data: Munch,
    private_data: Munch,
    main_user: MainUserMunch,
    models: ModelCollectionPair,
    ground_truth_answer: AnswerType,
) -> None:
    active_tasks = models.end.supervisor.Task.all()
    predicted_answer: AnswerType
    if not active_tasks:
        predicted_answer = -1000
    try:
        predicted_answer = json.loads(active_tasks[0].answer)
    except json.JSONDecodeError:
        predicted_answer = active_tasks[0].answer
    test.task_completed = active_tasks[0].status == "success"

    with test(
        """
        assert answers match.
        """
    ):
        test.answer(predicted_answer, ground_truth_answer)

    with test(
        """
        assert model changes match venmo.Transaction.
        """
    ):
        changed_model_names = models.changed_model_names()
        test.case("venmo.Transaction", "in", changed_model_names)

    with test(
        """
        obtain added, updated, removed venmo.Transaction records using models.changed_records,
        and assert correct number added, 0 updated, 0 removed.
        """
    ):
        added_txns, updated_txns, removed_txns = models.changed_records("venmo.Transaction")
        test.case(len(added_txns), "==", len(private_data.due_bills))
        test.case(len(updated_txns), "==", 0)
        test.case(len(removed_txns), "==", 0)

    with test(
        """
        assert receiver_ids of added transactions match private_data.due_recipient_venmo_ids.
        """
    ):
        actual_receiver_ids = list_of(added_txns, "receiver_id")
        test.case(
            actual_receiver_ids, "==",
            private_data.due_recipient_venmo_ids,
            ignore_order=True,
        )

    with test(
        """
        assert amounts of added transactions match expected bill amounts.
        """
    ):
        expected_amounts = [b["amount"] for b in private_data.due_bills]
        actual_amounts = sorted(list_of(added_txns, "amount"))
        expected_sorted = sorted(expected_amounts)
        test.case(actual_amounts, "==", expected_sorted, tolerance=0.51)

    with test(
        """
        assert no transactions were made to non-due bill recipients.
        """
    ):
        actual_receiver_ids = list_of(added_txns, "receiver_id")
        for nid in private_data.not_due_recipient_venmo_ids:
            test.case(nid, "not in", actual_receiver_ids, labels=("expected", "actual"))

    with test(
        """
        assert 0 venmo.PaymentRequest records were added, updated, or removed.
        """
    ):
        added_pr, updated_pr, removed_pr = models.changed_records("venmo.PaymentRequest")
        test.case(len(added_pr), "==", 0)
        test.case(len(updated_pr), "==", 0)
        test.case(len(removed_pr), "==", 0)
