from logging import Formatter, StreamHandler, getLogger, LogRecord, DEBUG, INFO, WARNING, ERROR, CRITICAL, Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path
from sys import stdout, argv

LOG_LEVELS = {
    'DEBUG': DEBUG,
    'INFO': INFO,
    'WARNING': WARNING,
    'ERROR': ERROR,
    'CRITICAL': CRITICAL
}


class ColoredFormatter(Formatter):
    def __init__(self, fmt: str, datefmt: str | None = None):
        super().__init__(fmt, datefmt)
        self.red = '\033[01;38;05;167m'
        self.blue = '\033[01;38;05;74m'
        self.orange = '\033[01;38;05;173m'
        self.pink = '\033[01;38;05;168m'
        self.gray = '\033[01;38;05;247m'
        self.usual = '\033[m'
        self.FORMATS = {
            DEBUG: self.gray + fmt + self.usual,
            INFO: self.blue + fmt + self.usual,
            WARNING: self.orange + fmt + self.usual,
            ERROR: self.red + fmt + self.usual,
            CRITICAL: self.pink + fmt + self.usual
        }

    def format(self, record: LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = Formatter(log_fmt, self.datefmt)
        return formatter.format(record)


def root_caller():
    return Path(argv[0]).stem.upper()


def setup_logger(
        name: str = Path(argv[0]).stem.upper(),
        level: str = 'INFO',
        log_file: Path | None = None,
        datefmt: str = '%d.%m.%Y %H:%M:%S',
        logfmt: str = '%(asctime)s [%(name)s] | %(levelname)s: %(message)s'
) -> Logger:
    log_level = LOG_LEVELS.get(level.upper())
    if not log_level:
        raise ValueError(f'invalid logging level: {level}, available levels:\n{list(LOG_LEVELS.keys())}')

    logger = getLogger(name)
    logger.setLevel(log_level)
    if logger.handlers:
        return logger

    formatter = Formatter(fmt=logfmt, datefmt=datefmt)
    color_formatter = ColoredFormatter(fmt=logfmt, datefmt=datefmt)
    console_handler = StreamHandler(stdout)
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=2 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False

    return logger
