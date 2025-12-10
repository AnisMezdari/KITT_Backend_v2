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

# Charger les configurations depuis YAML
_config_dir = Path(__file__).parent
_audio_config_path = _config_dir / "audio_config.yaml"
_company_context_path = _config_dir / "company_context.yaml"

def load_audio_config():
    """Charge la configuration audio depuis le fichier YAML"""
    if not _audio_config_path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable: {_audio_config_path}")

    with open(_audio_config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_company_context():
    """Charge le contexte entreprise/produit depuis le fichier YAML"""
    if not _company_context_path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable: {_company_context_path}")

    with open(_company_context_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Charger les configs
_audio_cfg = load_audio_config()
_company_ctx = load_company_context()

# ============================================================================
# SECRETS (depuis .env)
# ============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ============================================================================
# MODÈLES IA
# ============================================================================
OPENAI_MODEL = "gpt-4o-mini"
# FINE_TUNED_MODEL = "gpt-4o-mini"  # 🧪 TEST MODE : Utilise modèle standard pour tester nouveau prompt
FINE_TUNED_MODEL = "ft:gpt-4o-mini-2024-07-18:kitt:kitt-insight-v1:CfTuoM91"  # Ancien modèle
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
TIME_THRESHOLD_DUPLICATE = 60  # ⚡ OPTIMISÉ v2 : Augmenté à 60s pour éviter les doublons à long terme
MAX_INSIGHTS_CACHE = 5  # Nombre d'insights gardés en cache

# ============================================================================
# SYSTÈME DE PERTINENCE INTELLIGENTE (v2)
# ============================================================================
# Cooldown adaptatif selon la pertinence
COOLDOWN_BASE = 20  # Cooldown de base entre insights (20s)
COOLDOWN_HIGH_RELEVANCE = 10  # Cooldown réduit si score > 80 (moment clé détecté)
COOLDOWN_AFTER_INSIGHT = 25  # Cooldown après un insight généré

# Score minimum de pertinence pour générer un insight
MIN_RELEVANCE_SCORE = 60  # 0-100, seuil pour déclencher génération IA

# Bypass du cooldown pour événements critiques
ALLOW_COOLDOWN_BYPASS = True  # Permet de bypass le cooldown si score > 85

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
# CONTEXTE ENTREPRISE & PRODUIT (depuis company_context.yaml)
# ============================================================================
PRODUCT_NAME = _company_ctx['product']['name']
PRODUCT_DESCRIPTION = _company_ctx['product']['description']
PRODUCT_FULL_DESCRIPTION = _company_ctx['product']['full_description']

COMPANY_NAME = _company_ctx['company']['name']
COMPANY_INDUSTRY = _company_ctx['company']['industry']

SALES_FRAMEWORK = _company_ctx['sales_methodology']['framework']
SALES_FRAMEWORK_DESCRIPTION = _company_ctx['sales_methodology']['description']

# ============================================================================
# VERSION
# ============================================================================
VERSION = "3.1-refactored"
