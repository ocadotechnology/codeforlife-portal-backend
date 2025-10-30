"""
© Ocado Group
Created on 30/10/2025 at 17:09:18(+00:00).
"""

from datetime import timedelta

from codeforlife.tasks import DataWarehouseTask
from django.utils import timezone

from ..models import Attempt


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
    one_day_ago = timezone.now() - timedelta(days=1)

    return Attempt.objects.filter(finish_time__gte=one_day_ago)
