# utils/logger.py

import logging
import logging.config
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from config.settings import settings


# --------------------------------------------------
# DEFAULT FALLBACK CONFIG (if YAML missing)
# --------------------------------------------------
def default_logging_config():
    return {
        "version": 1,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }


# --------------------------------------------------
# SETUP LOGGING
# --------------------------------------------------
def setup_logging():
    """
    Load logging configuration from YAML file.
    Falls back to default config if YAML not found.
    """

    log_dir = settings.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    config_path = Path(settings.BASE_DIR) / "config" / "logging.yaml"

    if yaml and config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Ensure log file path exists
            file_handler = config.get("handlers", {}).get("file")
            if file_handler:
                log_file = file_handler.get("filename", "outputs/logs/app.log")
                log_path = Path(log_file)

                # Make absolute if relative
                if not log_path.is_absolute():
                    log_path = settings.BASE_DIR / log_path

                log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler["filename"] = str(log_path)

            logging.config.dictConfig(config)

        except Exception as e:
            print("⚠️ Logging YAML failed, using default config:", e)
            logging.config.dictConfig(default_logging_config())
    else:
        logging.config.dictConfig(default_logging_config())


# --------------------------------------------------
# GET LOGGER (SAFE)
# --------------------------------------------------
def get_logger(name: str = "pcb_ai") -> logging.Logger:
    """
    Returns a logger instance.
    Ensures no duplicate handlers.
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if not logger.handlers:
        setup_logging()

    return logger


# --------------------------------------------------
# MODULE LOGGER (RECOMMENDED)
# --------------------------------------------------
def get_module_logger(module_name: str) -> logging.Logger:
    """
    Use this inside modules:
    logger = get_module_logger(__name__)
    """
    return get_logger(module_name)


# --------------------------------------------------
# AGENT LOGGER (FOR LANGGRAPH AGENTS)
# --------------------------------------------------
def get_agent_logger(agent_name: str) -> logging.Logger:
    """
    Specialized logger for agents.
    Example:
        logger = get_agent_logger("LayoutAgent")
    """
    return get_logger(f"pcb_ai.agent.{agent_name}")


# --------------------------------------------------
# DEBUG HELPER
# --------------------------------------------------
def log_system_info():
    logger = get_logger("pcb_ai.system")

    logger.info("=== SYSTEM INFO ===")
    logger.info(f"ENV: {settings.ENV}")
    logger.info(f"DEBUG: {settings.DEBUG}")
    logger.info(f"GROQ KEY LOADED: {bool(settings.GROQ_API_KEY)}")
    logger.info(f"MODEL: {settings.LLM_MODEL}")
    logger.info(f"OUTPUT DIR: {settings.OUTPUT_DIR}")
    logger.info("===================")
