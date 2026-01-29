from collections.abc import Callable
from typing import Final, Generic, TypeVar, final

UnprocessedOutput = TypeVar("UnprocessedOutput")
ProcessedOutput = TypeVar("ProcessedOutput")


@final
class BatchedOperationFutureOutput(Generic[UnprocessedOutput, ProcessedOutput]):
    """Inspired by :class:`concurrent.futures.Future`."""

    def __init__(
        self,
        *,
        process_output: Callable[[UnprocessedOutput], ProcessedOutput],
    ) -> None:
        """Constructor.

        Args:
            process_result: Called to process the output of this operation once the batch is executed.
        """
        self._process_output: Final = process_output
        self._output: ProcessedOutput | None = None

    def _set_output(self, unprocessed_output: UnprocessedOutput, /) -> None:
        assert self._output is None, "Output has already been set."
        processed_output = self._process_output(unprocessed_output)
        assert processed_output is not None, "Processed output cannot be `None`."
        self._output = processed_output

    def output(self) -> ProcessedOutput:
        """Return the processed output of this operation if the batch has been executed.

        If the batch has not been executed yet, an error will be raised.
        """
        if self._output is None:
            raise RuntimeError("The batched operations have not been executed yet.")
        return self._output
