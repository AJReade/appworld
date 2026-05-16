# Foresight custom task: fmem1_1
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
        assert spotify.MusicPlayer in changed models.
    """):
        test.case("spotify.MusicPlayer", "in", models.changed_model_names())

    with test("""
        assert private_data.target_song_id is in the music player queue_song_ids in end state.
    """):
        music_player = models.end.spotify.MusicPlayer.first()
        test.case(private_data.target_song_id, "in", music_player.queue_song_ids)

    with test("""
        assert 0 spotify.Playlist records changed.
    """):
        a, u, r = models.changed_records("spotify.Playlist")
        test.case(len(a), "==", 0)
        test.case(len(u), "==", 0)
        test.case(len(r), "==", 0)
