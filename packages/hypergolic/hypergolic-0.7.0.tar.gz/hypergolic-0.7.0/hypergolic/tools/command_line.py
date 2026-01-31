import subprocess

from anthropic.types import ToolParam
from anthropic.types.tool_result_block_param import Content
from pydantic import BaseModel, Field

from hypergolic.tools.cancellation import (
    CancellableProcess,
    CancellationToken,
)
from hypergolic.tools.schemas import CommandToolOutput

from .enums import ToolName


class CommandLineToolInput(BaseModel):
    cmd: str = Field(description="The command to run")


def issue_cmd(
    input: CommandLineToolInput,
    cancellation_token: CancellationToken | None = None,
) -> list[Content]:
    if cancellation_token:
        process = CancellableProcess(cmd=input.cmd, timeout=30.0, grace_period=1.0)
        proc_result = process.execute(cancellation_token)

        result = CommandToolOutput(
            returncode=proc_result.returncode,
            stderr=proc_result.stderr,
            stdout=proc_result.stdout,
        )

        if proc_result.was_cancelled:
            result.stderr = (
                result.stderr + f"\n[Cancelled: {proc_result.cancellation_method}]"
            )
    else:
        output = subprocess.run(
            input.cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        result = CommandToolOutput(
            returncode=output.returncode,
            stderr=output.stderr,
            stdout=output.stdout,
        )

    return [{"type": "text", "text": result.model_dump_json()}]


CommandLineTool: ToolParam = {
    "input_schema": {
        "type": "object",
        "properties": {
            "cmd": {
                "type": "string",
                "description": "The command to run",
            }
        },
    },
    "name": ToolName.COMMAND_LINE,
    "description": "Runs a command on a user's local MacOS computer",
}
