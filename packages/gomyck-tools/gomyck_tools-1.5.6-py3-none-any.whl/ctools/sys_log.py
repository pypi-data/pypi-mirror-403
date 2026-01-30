import sys
import os
import time
import logging
from typing import Protocol

from ctools import call


# =========================
# 日志接口（IDE 提示）
# =========================
class LoggerProtocol(Protocol):
  def debug(self, msg: str, *args, **kwargs) -> None: ...
  def info(self, msg: str, *args, **kwargs) -> None: ...
  def warning(self, msg: str, *args, **kwargs) -> None: ...
  def error(self, msg: str, *args, **kwargs) -> None: ...
  def critical(self, msg: str, *args, **kwargs) -> None: ...
  def exception(self, msg: str, *args, **kwargs) -> None: ...


class _LazyLogger:
  def __getattr__(self, item):
    raise RuntimeError("Logger not initialized, call init_log() first")


flog: LoggerProtocol = _LazyLogger()
clog: LoggerProtocol = _LazyLogger()


# =========================
# TeeStream
# =========================
class TeeStream:
  def __init__(self, *streams):
    self.streams = streams

  def write(self, data):
    if not data:
      return
    for s in self.streams:
      try:
        s.write(data)
      except Exception:
        pass

  def flush(self):
    for s in self.streams:
      try:
        s.flush()
      except Exception:
        pass

  def isatty(self):
    return any(getattr(s, "isatty", lambda: False)() for s in self.streams)

  def fileno(self):
    for s in self.streams:
      try:
        return s.fileno()
      except Exception:
        pass
    raise OSError


# =========================
# print → 文件
# =========================
class PrintToFile:
  def __init__(self, file_handler: logging.Handler, level=logging.INFO):
    self.handler = file_handler
    self.level = level
    self._buffer = ""

  def write(self, msg):
    if not msg:
      return
    self._buffer += msg
    while "\n" in self._buffer:
      line, self._buffer = self._buffer.split("\n", 1)
      line = line.rstrip()
      if line:
        record = logging.LogRecord(
          name="print",
          level=self.level,
          pathname="",
          lineno=0,
          msg=line,
          args=(),
          exc_info=None,
        )
        self.handler.emit(record)

  def flush(self):
    if self._buffer.strip():
      record = logging.LogRecord(
        name="print",
        level=self.level,
        pathname="",
        lineno=0,
        msg=self._buffer.strip(),
        args=(),
        exc_info=None,
      )
      self.handler.emit(record)
      self._buffer = ""

  def isatty(self):
    return False


# =========================
# 初始化日志
# =========================
@call.init
def init_log():
  global flog, clog

  # 绝对路径
  home_dir = os.path.expanduser("~")
  log_dir = os.path.join(home_dir, ".ck", "ck-py-log")
  os.makedirs(log_dir, exist_ok=True)

  log_file = os.path.join(
    log_dir, f"log-{time.strftime('%Y-%m-%d-%H')}.log"
  )

  formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
  )

  # ===== 文件 handler =====
  file_handler = logging.FileHandler(log_file, encoding="utf-8")
  file_handler.setLevel(logging.DEBUG)
  file_handler.setFormatter(formatter)

  # ===== 控制台 handler =====
  console_handler = logging.StreamHandler(sys.stderr)
  console_handler.setLevel(logging.INFO)
  console_handler.setFormatter(formatter)

  # ===== logger =====
  logger = logging.getLogger("app")
  logger.setLevel(logging.DEBUG)
  logger.handlers.clear()
  logger.addHandler(file_handler)
  logger.addHandler(console_handler)
  logger.propagate = False

  flog = logger
  clog = logger

  # ===== stdout / stderr tee =====
  original_stdout = sys.stdout
  original_stderr = sys.stderr

  sys.stdout = TeeStream(
    original_stdout,
    PrintToFile(file_handler, level=logging.INFO)
  )

  sys.stderr = TeeStream(
    original_stderr,
    PrintToFile(file_handler, level=logging.ERROR)
  )

  # 确认文件已经创建
  if not os.path.isfile(log_file):
    raise RuntimeError(f"日志文件未创建: {log_file}")

