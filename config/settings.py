# config/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv

# --------------------------------------------------
# LOAD ENV (local development)
# --------------------------------------------------
load_dotenv()


# --------------------------------------------------
# SECRET LOADER (Streamlit + ENV fallback)
# --------------------------------------------------
def get_secret(key: str, default=None, cast_type=None):
    """
    Priority:
    1. Streamlit secrets
    2. Environment variables (.env or system)
    3. Default value

    Optional:
    - cast_type: type conversion (int, float, bool, etc.)
    """

    value = None

    # Try Streamlit secrets (only if available)
    try:
        import streamlit as st  # lazy import
        if key in st.secrets:
            value = st.secrets[key]
    except Exception:
        pass

    # Fallback to environment
    if value is None:
        value = os.getenv(key, default)

    # Type casting
    if cast_type and value is not None:
        try:
            if cast_type == bool:
                value = str(value).lower() in ["true", "1", "yes"]
            else:
                value = cast_type(value)
        except Exception:
            value = default

    return value


# --------------------------------------------------
# SETTINGS CLASS
# --------------------------------------------------
class Settings:

    # =========================
    # BASIC APP CONFIG
    # =========================
    APP_NAME: str = "PCB AI Copilot"
    ENV: str = get_secret("ENV", "development")
    DEBUG: bool = get_secret("DEBUG", True, bool)

    # =========================
    # PATHS
    # =========================
    BASE_DIR = Path(__file__).resolve().parent.parent

    DATA_DIR = BASE_DIR / "data"
    SAMPLE_DATA_DIR = DATA_DIR / "samples"
    UPLOAD_DIR = DATA_DIR / "uploads"
    PROCESSED_DIR = DATA_DIR / "processed"

    OUTPUT_DIR = BASE_DIR / "outputs"
    IMAGE_DIR = OUTPUT_DIR / "images"
    NETLIST_DIR = OUTPUT_DIR / "netlists"
    SCHEMATIC_DIR = OUTPUT_DIR / "schematics"
    PCB_DIR = OUTPUT_DIR / "pcbs"
    LOG_DIR = OUTPUT_DIR / "logs"

    # Ensure directories exist
    for path in [
        DATA_DIR, SAMPLE_DATA_DIR, UPLOAD_DIR, PROCESSED_DIR,
        OUTPUT_DIR, IMAGE_DIR, NETLIST_DIR, SCHEMATIC_DIR,
        PCB_DIR, LOG_DIR
    ]:
        path.mkdir(parents=True, exist_ok=True)

    # =========================
    # GROQ LLM CONFIG
    # =========================
    GROQ_API_KEY: str = get_secret("GROQ_API_KEY", "")
    LLM_MODEL: str = get_secret("LLM_MODEL", "llama3-70b-8192")
    LLM_TEMPERATURE: float = get_secret("LLM_TEMPERATURE", 0.2, float)
    LLM_MAX_TOKENS: int = get_secret("LLM_MAX_TOKENS", 2048, int)

    # =========================
    # RAG CONFIG
    # =========================
    VECTOR_DB_PATH = DATA_DIR / "vector_db"
    EMBEDDING_MODEL: str = get_secret(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    RETRIEVER_K: int = get_secret("RETRIEVER_K", 3, int)

    # =========================
    # PCB DESIGN RULES
    # =========================
    MIN_TRACE_WIDTH: float = get_secret("MIN_TRACE_WIDTH", 0.25, float)
    MIN_CLEARANCE: float = get_secret("MIN_CLEARANCE", 0.2, float)
    MAX_AUTOFIX_ITER: int = get_secret("MAX_AUTOFIX_ITER", 5, int)

    # =========================
    # LAYOUT SETTINGS
    # =========================
    GRID_SIZE: int = get_secret("GRID_SIZE", 10, int)
    BOARD_WIDTH: int = get_secret("BOARD_WIDTH", 200, int)
    BOARD_HEIGHT: int = get_secret("BOARD_HEIGHT", 200, int)

    # =========================
    # ROUTING SETTINGS
    # =========================
    ROUTING_STYLE: str = get_secret("ROUTING_STYLE", "manhattan")
    MAX_ROUTE_ATTEMPTS: int = get_secret("MAX_ROUTE_ATTEMPTS", 100, int)

    # =========================
    # KICAD CLI CONFIG
    # =========================
    KICAD_CLI: str = get_secret("KICAD_CLI", "kicad-cli")

    # =========================
    # STREAMLIT CONFIG
    # =========================
    STREAMLIT_PORT: int = get_secret("STREAMLIT_PORT", 8501, int)

    # =========================
    # FEATURE FLAGS
    # =========================
    ENABLE_RAG: bool = get_secret("ENABLE_RAG", True, bool)
    ENABLE_DRC: bool = get_secret("ENABLE_DRC", True, bool)
    ENABLE_AUTOFIX: bool = get_secret("ENABLE_AUTOFIX", True, bool)
    ENABLE_SIMULATION: bool = get_secret("ENABLE_SIMULATION", False, bool)

    # =========================
    # DEBUG UTIL
    # =========================
    def print_summary(self):
        print("\n=== SETTINGS SUMMARY ===")
        print(f"APP: {self.APP_NAME}")
        print(f"ENV: {self.ENV}")
        print(f"DEBUG: {self.DEBUG}")
        print(f"GROQ KEY LOADED: {bool(self.GROQ_API_KEY)}")
        print(f"MODEL: {self.LLM_MODEL}")
        print(f"RAG ENABLED: {self.ENABLE_RAG}")
        print("========================\n")


# Singleton instance
settings = Settings()
