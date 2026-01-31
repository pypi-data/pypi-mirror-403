"""Task for smoke testing which innocuously exercises the task dependencies."""

from dkist_processing_common.codecs.bytes import bytes_decoder
from dkist_processing_common.tasks import WorkflowTaskBase
from dkist_service_configuration.logging import logger

from dkist_processing_ops.config import dkist_processing_ops_configurations

__all__ = ["SmokeTask"]

from opentelemetry.trace import StatusCode


class SmokeTask(WorkflowTaskBase):
    def run(self) -> None:
        with self.telemetry_span("Validate read write functionality") as rw_span:
            logger.info("Starting smoke test read/write validation.")
            write_file = b"This is a smoke test file.\n"
            self.write(data=write_file, tags=["smoke_test", "output"])
            read_files = list(self.read(tags=["smoke_test", "output"], decoder=bytes_decoder))
            file_count = len(read_files)
            if file_count != 1:
                rw_span.set_status(StatusCode.ERROR)
                logger.error(f"Smoke test read did not return exactly one file. {file_count = }")
                raise RuntimeError(
                    f"Smoke test read did not return exactly one file. {file_count = }"
                )
            if read_files[0] != write_file:
                rw_span.set_status(StatusCode.ERROR)
                logger.error("Smoke test read file contents do not match written contents.")
                raise RuntimeError("Smoke test read file contents do not match written contents.")
            rw_span.set_status(StatusCode.OK)
            logger.success("Smoke test read/write validation completed successfully.")
        with self.telemetry_span("Validate configuration access / logging") as config_span:
            logger.info("Starting smoke test configuration logging.")
            dkist_processing_ops_configurations.log_configurations()
            logger.success("Smoke test configuration logging completed successfully.")
            config_span.set_status(StatusCode.OK)
