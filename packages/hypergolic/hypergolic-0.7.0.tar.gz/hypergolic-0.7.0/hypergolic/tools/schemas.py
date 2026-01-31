from pydantic import BaseModel


class CommandToolOutput(BaseModel):
    returncode: int
    stderr: str
    stdout: str
