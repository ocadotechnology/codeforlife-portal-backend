"""
© Ocado Group
Created on 23/10/2025 at 17:13:48(+01:00).
"""

from codeforlife.tasks import DataWarehouseTask
from codeforlife.user.models import School


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
