# Future Library
from __future__ import annotations

# Standard Library
import atexit
import dataclasses
import datetime
import json
import logging
import logging.config
import time
import warnings

from dataclasses import field
from functools import cache
from queue import Empty, Queue
from random import SystemRandom
from threading import Event, Thread
from typing import Any, Optional

# 3rd Party Library
from pydantic.dataclasses import dataclass
from sqlalchemy import (
    URL,
    BigInteger,
    Column,
    DateTime,
    Engine,
    Integer,
    MetaData,
    SmallInteger,
    String,
    Table,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB

# 1st Party Library
from rwskit.cli import LogLevel
from rwskit.config import YamlConfig

log = logging.getLogger(__name__)

DEFAULT_LOGGING_LEVEL: str = "INFO"
DEFAULT_LOGGING_FORMAT: str = (
    "%(asctime)-15s [%(name)s]:%(lineno)d %(levelname)s %(message)s"
)
UTC = datetime.timezone.utc


@dataclass(kw_only=True, frozen=True, config={"arbitrary_types_allowed": True})
class DictLoggingConfig(YamlConfig):
    version: int = 1
    """The logging configuration version (1 is currently the only valid value)."""

    disable_existing_loggers: bool = False
    """Disable all other previously existing non-root loggers."""

    incremental: bool | None = None
    """Whether this config should replace any current configuration ``False`` or update it."""

    formatters: dict[str, LogFormatConfig] = field(default_factory=dict)
    """The formatters to configure."""

    handlers: dict[str, LogHandlerConfig] = field(default_factory=dict)
    """Configures the log handlers."""

    # Not supported
    # filters: dict[str, LogFilterConfig] = field(default_factory=dict)

    loggers: dict[str, LoggerConfig] = field(default_factory=dict)
    """The individual loggers to configure."""

    root: RootLoggerConfig | None = None
    """The root logger configuration."""

    def to_dict(self, *args, **kwargs) -> dict[str, Any]:
        # TODO validate that the various "ID" names are defined
        data = {
            "version": self.version,
            "disable_existing_loggers": self.disable_existing_loggers,
            "incremental": self.incremental,
            "formatters": {k: f.to_dict() for k, f in self.formatters.items()},
            "handlers": {k: h.to_dict() for k, h in self.handlers.items()},
            "loggers": {k: g.to_dict() for k, g in self.loggers.items()},
            "root": self.root.to_dict() if self.root else None,
        }

        return {k: v for k, v in data.items() if v is not None}

    def configure(self):
        logging.config.dictConfig(self.to_dict())


@dataclass(kw_only=True, frozen=True, config={"arbitrary_types_allowed": True})
class LogFormatConfig(YamlConfig):
    """Options for configuring a log formatter."""

    format: str
    """The format string."""

    datefmt: str | None = None
    """A format string in the given style for the date/time portion of the logged output."""

    style: str = "%"
    """Can be one of '%', '{' or '$' and determines how the format string will be merged with its data."""

    validate: bool = True
    """If ``True`` (the default), incorrect or mismatched fmt and style will raise a ``ValueError``."""

    defaults: dict[str, Any] | None = None
    """A dictionary with default values to use in custom fields"""

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in dataclasses.asdict(self).items() if v is not None}


@dataclass(kw_only=True, frozen=True, config={"arbitrary_types_allowed": True})
class LogHandlerConfig(YamlConfig):
    """Options for configuring a log handler."""

    class_: str
    """The fully qualified name of the handler."""

    level: LogLevel | str | int | None = None
    """The level to use for this handler."""

    formatter: str | None = None
    """The id of the formatter for this handler."""

    kwargs: dict[str, Any] = field(default_factory=dict)
    """Any keyword args that should be passed to the handler constructor."""

    # Not supported
    # filters: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.level is not None and isinstance(self.level, (str, int)):
            # Use object.__setattr__ because the dataclass is frozen
            object.__setattr__(self, "level", LogLevel(self.level))

    def to_dict(self) -> dict[str, Any]:
        data = {"class": self.class_, "level": self.level, "formatter": self.formatter}

        # The keyword handler keyword args are passed as additional key/value
        # pairs in the main dictionary.
        return {k: v for k, v in data.items() if v is not None} | self.kwargs


@dataclass(kw_only=True, frozen=True, config={"arbitrary_types_allowed": True})
class RootLoggerConfig(YamlConfig):
    """Options for configuring a root logger."""

    level: LogLevel | int | str

    handlers: list[str] | None = None

    def __post_init__(self):
        if self.level is not None and isinstance(self.level, (str, int)):
            # Use object.__setattr__ because the dataclass is frozen
            object.__setattr__(self, "level", LogLevel(self.level))

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in dataclasses.asdict(self).items() if v is not None}


@dataclass(kw_only=True, frozen=True, config={"arbitrary_types_allowed": True})
class LoggerConfig(RootLoggerConfig):
    """Options for configuring an individual logger."""

    propagate: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in dataclasses.asdict(self).items() if v is not None}


@dataclass(kw_only=True, frozen=True, config={"arbitrary_types_allowed": True})
class LoggingConfig(YamlConfig):
    """Logging configuration."""

    level: LogLevel = LogLevel(DEFAULT_LOGGING_LEVEL)
    """The logging level."""

    format: str = DEFAULT_LOGGING_FORMAT
    """The logging format"""

    filename: Optional[str] = None
    """Log to this file instead of stderr."""

    log_level_overrides: dict[str, LogLevel | int] = field(default_factory=dict)
    """Override the log level for specific named loggers."""

    @property
    def is_logging_configured(self) -> bool:
        """Tries to determine if logging has already been configured.

        This method simply checks if any handlers are present. The existence
        of at least one handler indicates it is likely that some library
        (including our own) has already configured logging.

        Returns
        -------
        bool
            ``True`` if logging is already configured.
        """
        return bool(logging.getLogger().handlers)

    def configure(self):
        if self.is_logging_configured:
            log.warning(
                "Unable to configure logging because it has likely already been "
                "configured."
            )
        else:
            logging.basicConfig(
                filename=self.filename, level=self.level, format=self.format
            )

    def set_level_overrides(self):
        for log_name, log_level in self.log_level_overrides.items():
            log.debug(f"Overriding logger '{log_name}' with level '{log_level}'")
            logger = logging.getLogger(log_name)
            # logger.propagate = True
            logger.setLevel(log_level)


class AlchemyLoggingError(Exception):
    """Raised when the :class:`AlchemyHandler` can't connect to the database or table."""

    ...


class AlchemyHandler(logging.Handler):
    """A log handler that writes records to a database through sqlalchemy."""

    def __init__(
        self,
        engine: Engine | str | URL,
        table_name: str = "log",
        schema: str | None = None,
        autocommit: bool = True,
        batch_size: int = 20,
        flush_interval: float = 2.0,
        create_if_missing: bool = True,
        raise_if_not_active: bool = False,
    ):
        """A log handler that writes records to a database through sqlalchemy.

        The handler will write logs to a table named ``table_name`` in the
        optional ``schema``. The table has the following columns that mostly
        correspond to the attributes of a :class:`logging.LogRecord`:

        * **id**: An autogenerated primary key
        * **run_id**: A random integer created each time this handler is
          constructed. This helps identify separate runs of a program.
        * **relative_created_at**: The time in milliseconds since the record
          was created relative to when the logging module was loaded.
        * **created_at**: The UTC time when the record was created.
        * **logger_name**: The name of the logger.
        * **level_num**: The numeric level number of the record.
        * **pathname**: The full pathname to the module that issued the message
          (may be ``None``).
        * **function_name**: The name of the function where the message was logged.
        * *line_num**: The line number where the message was logged.
        * **message**: The formatted message after ``Formatter.format()`` has been invoked.
        * **exc_info**: The string representation of the ``exc_info`` (if any).
        * **stack_info**: The string representation of the stack trace (if any).
        * **extra**: Any extra data added to the record using the ``extra`` dictionary.
          **Note**, all values must be json serializable. If not, the extra data
          will be omitted and a warning raised.

        ..warning::
            If the program exits uncleanly, log messages in the buffer may
            not write to the database. If this is a concern lower the batch
            size to minimize this problem.

        ..note::
            Some ``LogRecord`` attributes are not stored for efficiency.
            For example, the ``filename`` attribute can be derived from the
            ``pathname`` attribute. I'm sure there are cases where
            the ``processName`` might be useful, but in standard single process
            applications it seems wasteful.

        Parameters
        ----------
        engine : Engine | str | URL
            The ``sqlalchemy`` engine to use. This can be specified as an
            existing ``sqlalchemy.Engine`` instance or as a database connection
            url.
        table_name : str, optional
            The name of the table where logs will be written.
        schema : str | None, optional
            _description_, by default None
        autocommit : bool, optional
            _description_, by default True
        batch_size : int, optional
            _description_, by default 20
        flush_interval : float, default = 2.0
            The interval in seconds at which the queue will be flushed no matter what.
        create_if_missing : bool, optional
            _description_, by default True
        raise_if_not_active : bool, optional
            _description_, by default False

        Raises
        ------
        AlchemyLoggingError
            _description_
        """
        super().__init__()

        self._engine = self._init_engine(engine)
        self._log_table = self.make_log_table(table_name, schema)

        if create_if_missing:
            self._create_table(self._log_table, self._engine)

        self._active = self._test_database_connection(self._engine, self._log_table)

        if not self._active and raise_if_not_active:
            raise AlchemyLoggingError()

        self._autocommit = autocommit

        # Give a (probably) unique identifier to the handler each time it is
        # constructed.
        self._run_id = SystemRandom().randrange((1 << 63) - 1)

        # The number of items to store in the buffer before flushing them
        # all to the database.
        self._batch_size = batch_size

        self._flush_interval = flush_interval if flush_interval > 0 else 2.0

        # AlLow the user to flush the batch manually.
        self._flush_request = Event()
        self._flush_complete = Event()

        # The buffer of log messages.
        self._queue: Queue[logging.LogRecord] = Queue()

        self._stop_event = Event()
        self._worker = Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

        atexit.register(self.close)

    @property
    def log_table(self) -> Table:
        return self._log_table

    @classmethod
    @cache
    def make_log_table(cls, table_name: str, schema: str | None = None) -> Table:
        return Table(
            table_name,
            MetaData(),
            Column("id", BigInteger(), primary_key=True, autoincrement=True),
            Column("run_id", BigInteger()),
            Column("relative_created_at", Integer()),
            Column("created_at", DateTime(timezone=True)),
            Column("logger_name", String()),
            Column("level_num", SmallInteger()),
            Column("function_name", String(), nullable=True),
            Column("line_num", SmallInteger()),
            Column("message", String()),
            Column("exc_info", String(), nullable=True),
            Column("stack_info", String(), nullable=True),
            Column("extra", JSONB(), nullable=True),
            schema=schema,
        )

    def emit(self, record: logging.LogRecord) -> None:
        if not self._active:
            return

        self._queue.put(record)

    def flush(self, timeout: float = 5):
        """Flush the current batch immediately."""

        self._flush_complete.clear()

        # Signal the worker to flush the current batch.
        self._flush_request.set()

        # Wait until the worker clears the value or we timeout.
        # The 'timeout' probably shouldn't be hard coded, but there isn't
        # an obvious value.
        self._flush_complete.wait(timeout=timeout)

    def close(self):
        try:
            self._stop_event.set()

            # Wait for the thread to end
            self._worker.join()
        except Exception:
            super().close()

    @classmethod
    def _init_engine(cls, engine: Engine | str | URL) -> Engine:
        if isinstance(engine, Engine):
            return engine

        if isinstance(engine, (str, URL)):
            return create_engine(engine)

        raise ValueError(f"Unsupported engine type '{type(engine)}'")

    @classmethod
    def _create_table(cls, table: Table, engine: Engine):
        try:
            table.metadata.create_all(engine, tables=[table])
        except Exception:
            log.error("Unable to create logging table.", exc_info=True)

    @classmethod
    def _test_database_connection(cls, engine: Engine, table: Table) -> bool:
        try:
            with engine.connect() as connection:
                return engine.dialect.has_table(
                    connection, table.name, schema=table.schema
                )
        except Exception as e:
            log.error("Connection to the database failed: %s", str(e))
            return False

    @classmethod
    @cache
    def _get_reserved_record_keys(cls) -> set[str]:
        # If the user stores "extra" data in the log message, the keys of
        # the dictionary get merged with the other items in the LogRecord
        # __dict__. This method uses a dummy LogRecord to find the standard
        # __dict__ keys so we can identify user defined ones.
        # See: https://stackoverflow.com/a/74604356
        record = logging.LogRecord("dummy", 0, "dummy", 0, "", None, None)

        # Keys that are present after construction
        record_keys = set(record.__dict__.keys())

        # These keys appear to be added later, but should not be considered
        # extra
        derived_keys = {"asctime", "message"}

        # Alternatively, I could probably just use the set of attribute
        # names from the documentation:
        # https://docs.python.org/3/library/logging.html#logrecord-attributes
        return record_keys | derived_keys

    def _worker_loop(self):
        # Keep track of the last time we flushed to calculate the time delta
        last_flush = time.time()

        # The current batch of records to flush.
        batch: list[logging.LogRecord] = []

        # Keep going until we are told to stop and the queue is empty.
        while not self._stop_event.is_set() or not self._queue.empty():
            try:
                # Wait up to `flush_interval` seconds for new records
                batch.append(self._queue.get(timeout=self._flush_interval))
            except Empty:
                pass

            # Flush if the buffer is full, we've reached the flush interval,
            # or the user has asked for a manual flush.
            now = time.time()
            if self._should_flush(batch, now, last_flush):
                self._flush_batch(batch)
                last_flush = now

        # Make sure the final batch is flushed
        if batch:
            self._flush_batch(batch)

    def _should_flush(
        self,
        batch: list[logging.LogRecord],
        now: float,
        last_flush: float,
    ) -> bool:
        n_records = len(batch)

        if n_records == 0:
            return False

        flush_delta = now - last_flush
        is_full = n_records >= self._batch_size
        is_time = flush_delta >= self._flush_interval
        is_manual = self._flush_request.is_set()

        return is_full or is_time or is_manual

    def _flush_batch(self, batch: list[logging.LogRecord]):
        try:
            values = [self._build_entry(r) for r in batch]
            context = (
                self._engine.connect().execution_options(isolation_level="AUTOCOMMIT")
                if self._autocommit
                else self._engine.begin()
            )

            with context as connection:
                connection.execute(self._log_table.insert().values(values))

        except Exception:
            for record in batch:
                self.handleError(record)
        finally:
            batch.clear()

            if self._flush_request.is_set():
                self._flush_request.clear()
                self._flush_complete.set()

    def _build_entry(self, record: logging.LogRecord) -> dict[str, Any]:
        return {
            "run_id": self._run_id,
            "relative_created_at": record.relativeCreated,
            "created_at": datetime.datetime.fromtimestamp(record.created, tz=UTC),
            "logger_name": record.name,
            "level_num": record.levelno,
            "function_name": record.funcName,
            "line_num": record.lineno,
            "message": record.getMessage(),
            "exc_info": self._format_exc_info(record.exc_info),
            "stack_info": self._format_stack_info(record.stack_info),
            "extra": self._decode_extra_data(record),
        }

    @classmethod
    def _format_exc_info(cls, exc_info: tuple | None) -> str | None:
        formatter = logging.Formatter()
        return formatter.formatException(exc_info) if exc_info else None

    @classmethod
    def _format_stack_info(cls, stack_info: str | None) -> str | None:
        return stack_info or None

    @classmethod
    def _decode_extra_data(cls, record: logging.LogRecord) -> dict[str, Any] | None:
        record_keys = set(record.__dict__.keys())
        extra_keys = record_keys - cls._get_reserved_record_keys()

        if extra_keys:
            extra = {k: getattr(record, k) for k in extra_keys}

            try:
                json.dumps(extra)
            except (TypeError, OverflowError):
                warnings.warn(
                    f"The provided 'extra' data is not serializable and cannot be "
                    f"stored as JSONB: {extra}",
                    UserWarning,
                )
                return None
        else:
            extra = None

        return extra
