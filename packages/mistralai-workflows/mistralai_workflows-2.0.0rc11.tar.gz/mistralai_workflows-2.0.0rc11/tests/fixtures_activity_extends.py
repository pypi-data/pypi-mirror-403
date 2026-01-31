from typing import Literal

from pydantic import BaseModel

from mistralai_workflows import activity, workflow


class ConfigBase(BaseModel):
    pass


class ProcessParams(BaseModel):
    data: str


class ProcessResult(BaseModel):
    result: str


@activity(display_name="Base Processor")
async def process_base(config: ConfigBase, params: ProcessParams) -> ProcessResult:
    return ProcessResult(result=f"base: {params.data}")


class V1Config(ConfigBase):
    version: Literal["v1"] = "v1"


@activity(display_name="V1 Processor", _extends=process_base)
async def process_v1(config: V1Config, params: ProcessParams) -> ProcessResult:
    return ProcessResult(result=f"v1: {params.data}")


class V2Config(ConfigBase):
    version: Literal["v2"] = "v2"


@activity(display_name="V2 Processor", _extends=process_base)
async def process_v2(config: V2Config, params: ProcessParams) -> ProcessResult:
    return ProcessResult(result=f"v2: {params.data}")


class WorkflowParams(BaseModel):
    config: V1Config | V2Config | ConfigBase
    data: str


class WorkflowResult(BaseModel):
    result: str


@workflow.define(name="activity_extends_workflow")
class ActivityExtendsWorkflow:
    @workflow.entrypoint
    async def run(self, params: WorkflowParams) -> WorkflowResult:
        process_result = await process_base(params.config, ProcessParams(data=params.data))
        return WorkflowResult(result=process_result.result)
