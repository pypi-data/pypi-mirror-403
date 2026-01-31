"""Configurations for the dkist-processing-ops package."""

from dkist_processing_common.config import DKISTProcessingCommonConfiguration
from pydantic import Field


class DKISTProcessingOpsConfigurations(DKISTProcessingCommonConfiguration):
    example_setting: str = Field(
        default="default_value", description="An example setting for demonstration purposes."
    )


dkist_processing_ops_configurations = DKISTProcessingOpsConfigurations()
dkist_processing_ops_configurations.log_configurations()
