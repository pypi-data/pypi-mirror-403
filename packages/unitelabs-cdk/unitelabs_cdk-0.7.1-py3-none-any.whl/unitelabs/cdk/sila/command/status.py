import datetime
import weakref


from sila.server import CommandExecution


class Status:
    """A class representing the status of an observablØe command execution."""

    def __init__(self, command_execution: CommandExecution):
        self.command_execution: CommandExecution = weakref.proxy(command_execution)

    def update(
        self,
        progress: float | None = None,
        remaining_time: datetime.timedelta | None = None,
        updated_lifetime: datetime.timedelta | None = None,
    ) -> None:
        """Update the execution status of an observable command execution."""
        self.command_execution.update_execution_info(
            progress=progress,
            remaining_time=remaining_time,
            updated_lifetime=updated_lifetime,
        )
