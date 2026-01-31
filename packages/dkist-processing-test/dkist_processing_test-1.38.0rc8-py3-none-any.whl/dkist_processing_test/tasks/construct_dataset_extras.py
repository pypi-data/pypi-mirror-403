from dkist_processing_common.codecs.fits import fits_array_decoder
from dkist_processing_common.models.extras import DatasetExtraHeaderSection
from dkist_processing_common.models.extras import DatasetExtraType
from dkist_processing_common.models.tags import Tag
from dkist_processing_common.models.task_name import TaskName
from dkist_processing_common.tasks.write_extra import WriteL1DatasetExtras


class TestWriteL1DatasetExtras(WriteL1DatasetExtras):
    def dataset_extra_headers(
        self,
        filename: str,
        task_type: TaskName = None,
        extra_name: DatasetExtraType = None,
        end_time: str = None,
        total_exposure: float | None = None,
        readout_exposure: float | None = None,
    ) -> dict:
        header_dict = super().dataset_extra_headers(
            task_type=task_type,
            filename=filename,
            total_exposure=total_exposure,
            readout_exposure=readout_exposure,
            extra_name=DatasetExtraType.dark,
            end_time=end_time,
        )
        new_header_section = {
            "ATLASURL": "example URL for testing",
        }
        header_dict[DatasetExtraHeaderSection.wavecal] = new_header_section
        return header_dict

    def run(self) -> None:
        # Get intermediate frame to turn into a dataset extra
        filename = self.format_extra_filename(extra_name=DatasetExtraType.dark)
        data = next(
            self.read(
                tags=[Tag.frame(), Tag.task("observe")],
                decoder=fits_array_decoder,
            )
        )
        header = self.build_dataset_extra_header(
            sections=[
                DatasetExtraHeaderSection.common,
                DatasetExtraHeaderSection.aggregate,
                DatasetExtraHeaderSection.iptask,
                DatasetExtraHeaderSection.gos,
                DatasetExtraHeaderSection.wavecal,
            ],
            filename=filename,
            task_type=TaskName.dark,
            total_exposure=0.05,
            readout_exposure=0.025,
            extra_name=DatasetExtraType.dark,
            end_time=self.constants.dark_date_end,
        )

        # Write the dataset extra
        self.assemble_and_write_dataset_extra(data=data, header=header, filename=filename)
