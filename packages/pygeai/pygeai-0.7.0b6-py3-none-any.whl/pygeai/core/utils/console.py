import os
import sys
from abc import ABC, abstractmethod


class StreamWriter(ABC):
    """
    Abstract base class for custom stream writers.
    """

    @abstractmethod
    def write_stdout(self, message: str = "", end: str = "\n"):
        pass

    @abstractmethod
    def write_success(self, message: str = "", end: str = "\n"):
        pass

    @abstractmethod
    def write_warning(self, message: str = "", end: str = "\n"):
        pass

    @abstractmethod
    def write_stderr(self, message: str = "", end: str = "\n"):
        pass


class ConsoleMeta(type):
    def __getattr__(cls, name):
        writer = cls._writer
        attr = getattr(writer, name, None)
        if callable(attr):
            return attr
        
        def noop(*args, **kwargs):
            pass
        return noop


class Console(metaclass=ConsoleMeta):
    """
    A utility class for writing messages to standard output and standard error streams.

    This class provides static methods to write messages to `sys.stdout` and `sys.stderr`
    with customizable end characters. It serves as a simple abstraction for console output
    operations, ensuring consistent handling of messages in command-line applications.

    Additionally, it allows setting a custom stream writer to override the default behavior,
    enabling redirection of output to alternative targets such as loggers, files, or testing sinks.
    """
    class DefaultStreamWriter(StreamWriter):
        """
        Default StreamWriter that writes to sys.stdout and sys.stderr with color support.
        """
        
        # ANSI color codes
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        RED = "\033[31m"
        RESET = "\033[0m"
        
        @staticmethod
        def _should_use_color(stream) -> bool:
            """Check if colors should be used based on terminal support and environment."""
            if os.getenv("NO_COLOR"):
                return False
            return hasattr(stream, "isatty") and stream.isatty()
        
        def write_stdout(self, message: str = "", end: str = "\n"):
            sys.stdout.write(f"{message}{end}")
            sys.stdout.flush()

        def write_success(self, message: str = "", end: str = "\n"):
            if self._should_use_color(sys.stdout):
                sys.stdout.write(f"{self.GREEN}{message}{self.RESET}{end}")
            else:
                sys.stdout.write(f"{message}{end}")
            sys.stdout.flush()

        def write_warning(self, message: str = "", end: str = "\n"):
            if self._should_use_color(sys.stderr):
                sys.stderr.write(f"{self.YELLOW}{message}{self.RESET}{end}")
            else:
                sys.stderr.write(f"{message}{end}")
            sys.stderr.flush()

        def write_stderr(self, message: str = "", end: str = "\n"):
            if self._should_use_color(sys.stderr):
                sys.stderr.write(f"{self.RED}{message}{self.RESET}{end}")
            else:
                sys.stderr.write(f"{message}{end}")
            sys.stderr.flush()

    _writer: StreamWriter = DefaultStreamWriter()

    @staticmethod
    def write_stdout(message: str = "", end: str = "\n"):
        """
        Writes a message to the standard output stream (sys.stdout).

        :param message: str - The message to write. Defaults to an empty string.
        :param end: str - The string to append after the message. Defaults to a newline ('\\n').
        :return: None - No return value; output is written to sys.stdout.
        """
        Console._writer.write_stdout(message, end)

    @staticmethod
    def write_success(message: str = "", end: str = "\n"):
        """
        Writes a success message to the standard output stream (sys.stdout) in green.

        :param message: str - The message to write. Defaults to an empty string.
        :param end: str - The string to append after the message. Defaults to a newline ('\\n').
        :return: None - No return value; output is written to sys.stdout.
        """
        Console._writer.write_success(message, end)

    @staticmethod
    def write_warning(message: str = "", end: str = "\n"):
        """
        Writes a warning message to the standard error stream (sys.stderr) in yellow.

        :param message: str - The message to write. Defaults to an empty string.
        :param end: str - The string to append after the message. Defaults to a newline ('\\n').
        :return: None - No return value; output is written to sys.stderr.
        """
        Console._writer.write_warning(message, end)

    @staticmethod
    def write_stderr(message: str = "", end: str = "\n"):
        """
        Writes a message to the standard error stream (sys.stderr) in red.

        :param message: str - The message to write. Defaults to an empty string.
        :param end: str - The string to append after the message. Defaults to a newline ('\\n').
        :return: None - No return value; output is written to sys.stderr.
        """
        Console._writer.write_stderr(message, end)

    @staticmethod
    def set_writer(writer: StreamWriter):
        """
        Sets a custom StreamWriter to handle console output.

        :param writer: StreamWriter - Implementation of the StreamWriter interface.
        """
        Console._writer = writer
