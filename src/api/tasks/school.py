"""
© Ocado Group
Created on 23/10/2025 at 17:13:48(+01:00).
"""

from codeforlife.tasks import DataWarehouseTask
from codeforlife.user.models import School
from django.db.models import Count


@DataWarehouseTask.shared(
    DataWarehouseTask.Settings(
        bq_table_write_mode="overwrite",
        chunk_size=1000,
        fields=["id", "country", "creation_time", "is_active", "county"],
    )
)
def common_school():
    """
    Collects information about School objects. Used to report on location of
    schools and whether the school is still active or not.

    https://console.cloud.google.com/bigquery?tc=europe:60643198-0000-2efe-8b5f-f403043816d8&project=decent-digit-629&ws=!1m0
    """
    return School.objects.all()


@DataWarehouseTask.shared(
    DataWarehouseTask.Settings(
        bq_table_write_mode="overwrite",
        chunk_size=1000,
        fields=["id", "name", "country", "teacher_count"],
    )
)
def teachers_per_school():
    """
    Collects data about the School table, and counting how many Teacher rows are
    related to the School object. Used to report on metrics like average and max
    number of teachers per school.

    https://console.cloud.google.com/bigquery?tc=europe:608bfedc-0000-2064-9e7f-94eb2c139c38&project=decent-digit-629&ws=!1m0
    """
    return (
        School.objects.values("id", "name", "country")
        .annotate(teacher_count=Count("teacher_school"))
        .filter(teacher_count__gt=0)  # Caveat: Mimics INNER JOIN of SQL query
        .order_by("-teacher_count")
    )
