"""
© Ocado Group
Created on 24/10/2025 at 14:02:48(+01:00).
"""

from datetime import timedelta

from codeforlife.tasks import DataWarehouseTask
from django.utils import timezone

from ..models import Level


@DataWarehouseTask.shared(
    DataWarehouseTask.Settings(
        bq_table_write_mode="append",
        chunk_size=1000,
        fields=[
            "id",
            "start_time",
            "finish_time",
            "score",
            "student_id",
            "level_id",
            "is_best_attempt",
        ],
    )
)
def rapid_router_attempts():
    """
    Collects Attempt objects that were successfully finished in the last 24
    hours. We use this to be able to report on the total number of level
    attempts by students. Time series. Only query in append-mode.

    https://console.cloud.google.com/bigquery?tc=europe:5f3f9273-0000-2bdd-886a-94eb2c0d7776&project=decent-digit-629&ws=!1m5!1m4!1m3!1sdecent-digit-629!2sbquxjob_28afdd57_19a164ff9c0!3sEU
    """
    # pylint: disable-next=import-outside-toplevel
    from game.models import Attempt  # type: ignore[import-untyped]

    one_day_ago = timezone.now() - timedelta(days=1)

    return Attempt.objects.filter(finish_time__gte=one_day_ago)


@DataWarehouseTask.shared(
    DataWarehouseTask.Settings(
        bq_table_write_mode="overwrite",
        chunk_size=1000,
        fields=["id", "level_id", "user_id"],
    )
)
def game_level_shared_with():
    """
    Collects data from the Level table. Used to report on number of levels
    shared and how many times a level was shared (not 100% how this one works).

    https://console.cloud.google.com/bigquery?tc=europe:62bc89fc-0000-23a7-b082-001a114be4b0&project=decent-digit-629&ws=!1m5!1m4!1m3!1sdecent-digit-629!2sbquxjob_33469129_19a165a8ef4!3sEU
    """
    return Level.shared_with.through.objects.all()
