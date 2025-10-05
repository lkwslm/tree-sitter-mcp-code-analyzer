import logging
import os
from pathlib import Path
from typing import Optional

try:
    import yaml  # 用于读取 config.yaml 的日志相关配置（可选）
except Exception:
    yaml = None


DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def _resolve_config(config_path: str) -> dict:
    """读取配置文件中的 logging 配置（如果存在）。"""
    cfg = {}
    try:
        path = Path(config_path)
        if path.exists() and yaml:
            with path.open("r", encoding="utf-8") as f:
                full = yaml.safe_load(f) or {}
                cfg = full.get("logging", {}) or {}
    except Exception:
        # 读取配置失败时使用默认设置
        cfg = {}
    return cfg


def init_logging(
    app_name: str = "tree-sitter-mcp-server",
    config_path: str = "config/config.yaml",
    default_log_dir: str = "logs",
    default_level: str = "INFO",
) -> None:
    """
    初始化全局日志系统：控制台 + 按天滚动文件。

    - 优先使用 `config/config.yaml` 中的 logging 配置
    - 如果未指定文件，则默认写入 `logs/<app_name>.log`
    - 自动创建日志目录
    """

    # 读取可能的配置
    cfg = _resolve_config(config_path)

    # 级别
    level_name = (cfg.get("level") or default_level).upper()
    level = getattr(logging, level_name, logging.INFO)

    # 格式
    fmt = cfg.get("format") or DEFAULT_FORMAT
    formatter = logging.Formatter(fmt)

    # 目标文件
    file_cfg: Optional[str] = cfg.get("file")
    if not file_cfg:
        # 默认日志文件：logs/<app_name>.log
        log_dir = Path(default_log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{app_name}.log"
    else:
        log_file = Path(file_cfg)
        if not log_file.parent.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)

    # 根 logger
    root = logging.getLogger()
    # 清理已有 handler，避免重复输出
    if root.handlers:
        for h in list(root.handlers):
            root.removeHandler(h)

    root.setLevel(level)

    # 文件滚动：按天滚动，保留最近14天
    from logging.handlers import TimedRotatingFileHandler

    file_handler = TimedRotatingFileHandler(
        filename=str(log_file), when="midnight", interval=1, backupCount=14, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # 捕获 warnings 到日志
    logging.captureWarnings(True)

    # 示例：记录初始化完成
    logging.getLogger(app_name).info(
        f"日志初始化完成：level={level_name}, file='{log_file}', console=on"
    )