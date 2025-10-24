"""
© Ocado Group
Created on 24/10/2025 at 14:02:48(+01:00).
"""

from datetime import date, timedelta

from codeforlife.tasks import DataWarehouseTask
from django.db.models import Count, IntegerField, Q, Value
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


@DataWarehouseTask.shared(
    DataWarehouseTask.Settings(
        bq_table_write_mode="overwrite",
        chunk_size=1000,
        fields=["date", "level_control_submits"],
        id_field="date",
    )
)
def level_control_submits():
    """
    Collects data from the DailyActivity table to report on how often the level
    access control feature gets used. This could be achieved in GA too but doing
    it this way in the DB ensures we get 100% of the data.

    https://console.cloud.google.com/bigquery?tc=europe:63dc3efb-0000-2aed-b0b8-001a114be98a&project=decent-digit-629&ws=!1m5!1m4!1m3!1sdecent-digit-629!2sbquxjob_69eca5da_19a166735d3!3sEU
    """
    # pylint: disable-next=import-outside-toplevel
    from common.models import DailyActivity  # type: ignore[import-untyped]

    return DailyActivity.objects.filter(
        date__gt=date(year=2022, month=12, day=9)
    )


@DataWarehouseTask.shared(
    DataWarehouseTask.Settings(
        bq_table_write_mode="overwrite",
        chunk_size=10,  # There's only ever 1 row.
        fields=[
            "teacher_levels",
            "school_student_levels",
            "independent_student_levels",
            "unallocated_users",
            "total_games_created",
        ],
        id_field="teacher_levels",  # There's only ever 1 row.
    )
)
def levels_created():
    """
    Collects data from the Level table. Used to report on how many levels have
    been created, sorted by user type.

    https://console.cloud.google.com/bigquery?tc=europe:64e35e2c-0000-2e19-87e8-94eb2c1b0db0&project=decent-digit-629&ws=!1m0
    """
    student_filter = Q(owner__student__isnull=False)

    counts = Level.objects.filter(
        episode_id__isnull=True, owner__isnull=False
    ).aggregate(
        teacher_levels=Count("id", filter=Q(owner__teacher__isnull=False)),
        school_student_levels=Count(
            "id",
            filter=(
                student_filter & Q(owner__student__class_field_id__isnull=False)
            ),
        ),
        independent_student_levels=Count(
            "id",
            filter=(
                student_filter & Q(owner__student__class_field_id__isnull=True)
            ),
        ),
        unallocated_users=Count(
            "id",
            filter=(
                Q(owner__student__isnull=True) & Q(owner__teacher__isnull=True)
            ),
        ),
        total_games_created=Count("id"),
    )

    # Hacky solution to return a queryset of 1 row.
    return Level.objects.all()[:1].annotate(
        teacher_levels=Value(
            counts["teacher_levels"], output_field=IntegerField()
        ),
        school_student_levels=Value(
            counts["school_student_levels"], output_field=IntegerField()
        ),
        independent_student_levels=Value(
            counts["independent_student_levels"], output_field=IntegerField()
        ),
        unallocated_users=Value(
            counts["unallocated_users"], output_field=IntegerField()
        ),
        total_games_created=Value(
            counts["total_games_created"], output_field=IntegerField()
        ),
    )
