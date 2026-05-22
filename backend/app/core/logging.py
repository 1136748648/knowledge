import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


class DailyFileHandler(logging.Handler):
    """每天一个日志文件，文件名格式：yyyyMMdd[_pod].log"""

    def __init__(self, log_dir: str):
        super().__init__()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._current_date = ""
        self._fh = None

        # 检测 POD 环境变量（K8s 部署时自动附加）
        self._pod = os.environ.get("POD_NAME") or os.environ.get("HOSTNAME", "")

    def _get_filename(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        if self._pod:
            return f"{date_str}_{self._pod}.log"
        return f"{date_str}.log"

    def _ensure_file(self):
        today = datetime.now().strftime("%Y%m%d")
        if today != self._current_date:
            if self._fh:
                self._fh.close()
            filepath = self.log_dir / self._get_filename()
            self._fh = open(filepath, "a", encoding="utf-8")
            self._current_date = today

    def emit(self, record):
        try:
            self._ensure_file()
            msg = self.format(record)
            self._fh.write(msg + "\n")
            self._fh.flush()
        except Exception:
            self.handleError(record)

    def close(self):
        if self._fh:
            self._fh.close()
        super().close()


def setup_logging(log_dir: str = "logs", level: str = "INFO"):
    """配置日志：控制台 + 每日文件 + 错误日志"""

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # 清除已有 handler（避免 uvicorn reload 时重复添加）
    root.handlers.clear()

    # 格式：具体时间-日志等级-日志信息
    fmt = logging.Formatter(
        "%(asctime)s-%(levelname)s-%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ---- 控制台 ----
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, level.upper(), logging.INFO))
    console.setFormatter(fmt)
    root.addHandler(console)

    # ---- 每日日志文件 ----
    daily = DailyFileHandler(log_dir)
    daily.setLevel(logging.DEBUG)
    daily.setFormatter(fmt)
    root.addHandler(daily)

    # ---- 错误日志文件（仅 ERROR 及以上） ----
    error_path = Path(log_dir)
    error_path.mkdir(exist_ok=True)
    error_file = logging.handlers.RotatingFileHandler(
        error_path / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_file.setLevel(logging.ERROR)
    error_file.setFormatter(fmt)
    root.addHandler(error_file)

    # 降低第三方库日志噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(f"Logging initialized -> {Path(log_dir).absolute()}")
