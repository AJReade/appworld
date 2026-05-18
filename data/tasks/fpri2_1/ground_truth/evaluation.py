# Foresight custom task: fpri2_1
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
        assert todoist.Task in changed models.
    """):
        test.case("todoist.Task", "in", models.changed_model_names())

    with test("""
        obtain updated todoist.Task records, assert 0 added, 2 updated, 0 removed.
    """):
        added, updated, removed = models.changed_records("todoist.Task")
        test.case(len(added), "==", 0)
        test.case(len(updated), "==", 2)
        test.case(len(removed), "==", 0)

    with test("""
        assert updated task titles match private_data.overdue_titles.
    """):
        actual_titles = list_of(updated, "title")
        test.case(actual_titles, "==", private_data.overdue_titles, ignore_order=True)

    with test("""
        assert future task titles are not in updated tasks.
    """):
        actual_titles = list_of(updated, "title")
        for title in private_data.future_titles:
            test.case(title, "not in", actual_titles, labels=("expected", "actual"))

    with test("""
        assert updated tasks have is_completed True in end state.
    """):
        for task in updated:
            test.case(task.is_completed, "is_truthy")
