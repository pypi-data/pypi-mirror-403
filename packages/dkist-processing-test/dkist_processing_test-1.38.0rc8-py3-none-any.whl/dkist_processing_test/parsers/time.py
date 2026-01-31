import datetime
from typing import Callable

from dkist_processing_common.models.fits_access import MetadataKey
from dkist_processing_common.parsers.task import passthrough_header_ip_task
from dkist_processing_common.parsers.time import TaskDatetimeBudBase


class TaskDateEndBud(TaskDatetimeBudBase):
    """Class for the date begin task Bud."""

    def __init__(
        self,
        constant_name: str,
        ip_task_types: str | list[str],
        task_type_parsing_function: Callable = passthrough_header_ip_task,
    ):
        super().__init__(
            stem_name=constant_name,
            metadata_key=MetadataKey.time_obs,
            ip_task_types=ip_task_types,
            task_type_parsing_function=task_type_parsing_function,
        )

    def getter(self) -> str:
        """
        Return the latest date begin for the ip task type converted from unix seconds to datetime string.

        Returns
        -------
        Return the maximum date begin as a datetime string
        """
        # super().getter() returns a sorted list
        max_time = super().getter()[-1]
        max_time_dt = datetime.datetime.fromtimestamp(max_time, tz=datetime.timezone.utc)
        return max_time_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")
