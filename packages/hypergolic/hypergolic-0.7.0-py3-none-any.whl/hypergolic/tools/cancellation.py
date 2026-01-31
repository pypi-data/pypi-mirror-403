import os
import signal
import subprocess
import threading
from dataclasses import dataclass, field


class CancellationToken:
    """Thread-safe cancellation token.

    Uses threading.Event which is safe to use from both sync and async contexts.
    Note: The wait() method blocks and should only be used in sync code or
    via asyncio.to_thread(). Use is_cancelled() for non-blocking checks.
    """

    def __init__(self):
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        self._cancelled.set()

    def is_cancelled(self) -> bool:
        """Non-blocking check if cancellation was requested. Safe for async use."""
        return self._cancelled.is_set()

    def wait(self, timeout: float | None = None) -> bool:
        """Block until cancelled or timeout. Do NOT call from async code."""
        return self._cancelled.wait(timeout)


@dataclass
class CancellableProcessResult:
    returncode: int
    stdout: str
    stderr: str
    was_cancelled: bool = False
    cancellation_method: str | None = None


@dataclass
class CancellableProcess:
    cmd: str
    timeout: float = 30.0
    grace_period: float = 1.0
    _process: subprocess.Popen[str] | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False
    )
    _cancelled: bool = field(default=False, init=False)
    _cancellation_method: str | None = field(default=None, init=False)

    def execute(
        self, cancellation_token: CancellationToken | None = None
    ) -> CancellableProcessResult:
        with self._lock:
            self._process = subprocess.Popen(
                self.cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

        try:
            if cancellation_token:
                return self._execute_with_cancellation(cancellation_token)
            else:
                return self._execute_simple()
        except Exception as e:
            self._force_kill()
            raise e

    def _execute_simple(self) -> CancellableProcessResult:
        if self._process is None:
            return CancellableProcessResult(
                returncode=-1,
                stdout="",
                stderr="Process failed to start",
                was_cancelled=False,
            )

        try:
            stdout, stderr = self._process.communicate(timeout=self.timeout)
            return CancellableProcessResult(
                returncode=self._process.returncode,
                stdout=stdout,
                stderr=stderr,
                was_cancelled=False,
            )
        except subprocess.TimeoutExpired:
            self._force_kill()
            return CancellableProcessResult(
                returncode=-1,
                stdout="",
                stderr=f"Command timed out after {self.timeout} seconds",
                was_cancelled=False,
            )

    def _execute_with_cancellation(
        self, token: CancellationToken
    ) -> CancellableProcessResult:
        if self._process is None:
            return CancellableProcessResult(
                returncode=-1,
                stdout="",
                stderr="Process failed to start",
                was_cancelled=False,
            )

        poll_interval = 0.1
        elapsed = 0.0

        while True:
            retcode = self._process.poll()
            if retcode is not None:
                stdout, stderr = self._process.communicate()
                return CancellableProcessResult(
                    returncode=retcode,
                    stdout=stdout,
                    stderr=stderr,
                    was_cancelled=self._cancelled,
                    cancellation_method=self._cancellation_method,
                )

            if token.is_cancelled():
                return self._handle_cancellation()

            if elapsed >= self.timeout:
                self._force_kill()
                return CancellableProcessResult(
                    returncode=-1,
                    stdout="",
                    stderr=f"Command timed out after {self.timeout} seconds",
                    was_cancelled=False,
                )

            token.wait(poll_interval)
            elapsed += poll_interval

    def _handle_cancellation(self) -> CancellableProcessResult:
        self._cancelled = True

        if self._graceful_terminate():
            self._cancellation_method = "graceful"
        else:
            self._force_kill()
            self._cancellation_method = "forced"

        if self._process is None:
            return CancellableProcessResult(
                returncode=-1,
                stdout="",
                stderr="[Process cancelled by user]",
                was_cancelled=True,
                cancellation_method=self._cancellation_method,
            )

        try:
            stdout, stderr = self._process.communicate(timeout=0.5)
        except subprocess.TimeoutExpired:
            stdout, stderr = "", ""
            self._process.kill()
            self._process.wait()

        return CancellableProcessResult(
            returncode=self._process.returncode or -1,
            stdout=stdout,
            stderr=stderr + "\n[Process cancelled by user]",
            was_cancelled=True,
            cancellation_method=self._cancellation_method,
        )

    def _graceful_terminate(self) -> bool:
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                return True

            try:
                if os.name != "nt":
                    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                else:
                    self._process.terminate()
            except (ProcessLookupError, OSError):
                return True

        try:
            self._process.wait(timeout=self.grace_period)
            return True
        except subprocess.TimeoutExpired:
            return False

    def _force_kill(self) -> None:
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                return

            try:
                if os.name != "nt":
                    os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
                else:
                    self._process.kill()
            except (ProcessLookupError, OSError):
                pass

        try:
            self._process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            pass

    def cancel(self) -> None:
        self._handle_cancellation()
