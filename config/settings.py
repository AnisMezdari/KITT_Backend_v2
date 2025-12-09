"""
Configuration centralisée pour KITT Backend
Sépare les secrets (.env) de la configuration fonctionnelle (audio_config.yaml)
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Charger les secrets depuis .env
load_dotenv()

# Charger la configuration audio depuis YAML
_config_dir = Path(__file__).parent
_audio_config_path = _config_dir / "audio_config.yaml"

def load_audio_config():
    """Charge la configuration audio depuis le fichier YAML"""
    if not _audio_config_path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable: {_audio_config_path}")

    with open(_audio_config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Charger la config audio
_audio_cfg = load_audio_config()

# ============================================================================
# SECRETS (depuis .env)
# ============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ============================================================================
# MODÈLES IA
# ============================================================================
OPENAI_MODEL = "gpt-4o-mini"
FINE_TUNED_MODEL = "ft:gpt-4o-mini-2024-07-18:kitt:kitt-insight-v1:CfTuoM91"
WHISPER_MODEL = "whisper-1"

# ============================================================================
# AUDIO & TRANSCRIPTION (depuis audio_config.yaml)
# ============================================================================

# ----- DÉTECTION DE SILENCE (MICROPHONE - COMMERCIAL) -----
SILENCE_THRESHOLD_MIC = float(_audio_cfg['silence_detection']['microphone']['rms_threshold'])
MIN_AMPLITUDE_MIC = int(_audio_cfg['silence_detection']['microphone']['min_amplitude'])
MIN_AUDIO_LENGTH_MIC = int(_audio_cfg['silence_detection']['microphone']['min_audio_length'])

# ----- DÉTECTION DE SILENCE (NAVIGATEUR - CLIENT) -----
SILENCE_THRESHOLD_BROWSER = float(_audio_cfg['silence_detection']['browser']['rms_threshold'])
MIN_AMPLITUDE_BROWSER = int(_audio_cfg['silence_detection']['browser']['min_amplitude'])
MIN_AUDIO_LENGTH_BROWSER = int(_audio_cfg['silence_detection']['browser']['min_audio_length'])

# Rétrocompatibilité (utilisé par défaut si non spécifié)
SILENCE_THRESHOLD = SILENCE_THRESHOLD_MIC
MIN_AMPLITUDE = MIN_AMPLITUDE_MIC
MIN_AUDIO_LENGTH = MIN_AUDIO_LENGTH_MIC

# ----- WHISPER -----
WHISPER_LANGUAGE = _audio_cfg['whisper']['language']
WHISPER_PROMPT = _audio_cfg['whisper']['prompt']
WHISPER_TEMPERATURE = float(_audio_cfg['whisper']['temperature'])

# ----- FILTRAGE -----
MIN_TRANSCRIPTION_LENGTH = int(_audio_cfg['transcription_filtering']['min_length'])
UNWANTED_PATTERNS = _audio_cfg['transcription_filtering']['unwanted_patterns']

# ----- AUDIO DE BASE -----
AUDIO_SAMPLE_RATE = int(_audio_cfg['audio']['sample_rate'])
AUDIO_SUBTYPE = _audio_cfg['audio']['subtype']

# ============================================================================
# INSIGHTS & COACHING
# ============================================================================
MIN_INSIGHT_INTERVAL = int(os.getenv("MIN_INSIGHT_INTERVAL", "1"))
MAX_CONTEXT_MESSAGES = 50  # ⚡ OPTIMISÉ : Augmenté de 24 à 50 pour un meilleur contexte RAG
SUMMARY_THRESHOLD = 10  # Nombre de messages avant résumé
TIME_THRESHOLD_DUPLICATE = 30  # ⚡ OPTIMISÉ : Réduit de 60s à 30s pour accepter plus vite les insights similaires
MAX_INSIGHTS_CACHE = 5  # Nombre d'insights gardés en cache

# ============================================================================
# IA CONFIGURATION
# ============================================================================
DEFAULT_TEMPERATURE = 0.3
COACHING_TEMPERATURE = 0.3
SUMMARY_TEMPERATURE = 0.3
DUPLICATE_CHECK_TEMPERATURE = 0.2

# ============================================================================
# CORS
# ============================================================================
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

# Dossier des logs
import pathlib
LOG_DIR = pathlib.Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Fichiers de logs
LOG_FILE_MAIN = LOG_DIR / "kitt_main.log"
LOG_FILE_ERRORS = LOG_DIR / "kitt_errors.log"
LOG_FILE_TRANSCRIPTION = LOG_DIR / "kitt_transcription.log"
LOG_FILE_INSIGHTS = LOG_DIR / "kitt_insights.log"

# Rotation des logs
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5  # Garder 5 fichiers de backup

# ============================================================================
# VERSION
# ============================================================================
VERSION = "3.1-refactored"
