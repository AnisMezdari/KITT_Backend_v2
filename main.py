"""
KITT Backend - Application FastAPI principale
Version refactorisée et modulaire
"""
import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import (
    VERSION,
    ALLOWED_ORIGINS,
    LOG_LEVEL,
    LOG_FORMAT,
    MAX_CONTEXT_MESSAGES,
    LOG_DIR,
    LOG_FILE_MAIN,
    LOG_FILE_ERRORS,
    LOG_FILE_TRANSCRIPTION,
    LOG_FILE_INSIGHTS,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT
)

# Configuration avancée du logging
def setup_logging():
    """Configure le système de logs avec fichiers et rotation"""
    
    # Créer le dossier logs s'il n'existe pas
    LOG_DIR.mkdir(exist_ok=True)
    
    # Formatter commun
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Logger principal
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Handler 1: Console (pour le terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Handler 2: Fichier principal (tous les logs)
    main_handler = RotatingFileHandler(
        LOG_FILE_MAIN,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    main_handler.setLevel(logging.DEBUG)
    main_handler.setFormatter(formatter)
    root_logger.addHandler(main_handler)
    
    # Handler 3: Fichier erreurs uniquement
    error_handler = RotatingFileHandler(
        LOG_FILE_ERRORS,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Handler 4: Fichier transcription
    transcription_handler = RotatingFileHandler(
        LOG_FILE_TRANSCRIPTION,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    transcription_handler.setLevel(logging.INFO)
    transcription_handler.setFormatter(formatter)
    
    # Filtrer uniquement les logs de transcription
    class TranscriptionFilter(logging.Filter):
        def filter(self, record):
            return 'TRANSCRIPTION' in record.getMessage()
    
    transcription_handler.addFilter(TranscriptionFilter())
    root_logger.addHandler(transcription_handler)
    
    # Handler 5: Fichier insights
    insights_handler = RotatingFileHandler(
        LOG_FILE_INSIGHTS,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    insights_handler.setLevel(logging.INFO)
    insights_handler.setFormatter(formatter)
    
    # Filtrer uniquement les logs d'insights
    class InsightsFilter(logging.Filter):
        def filter(self, record):
            msg = record.getMessage()
            return any(keyword in msg for keyword in ['INSIGHT', 'COACHING', 'ANTI-DOUBLON'])
    
    insights_handler.addFilter(InsightsFilter())
    root_logger.addHandler(insights_handler)
    
    # Log de démarrage
    logging.info(f"{'='*80}")
    logging.info(f"🚀 KITT Backend v{VERSION} - Démarrage")
    logging.info(f"{'='*80}")
    logging.info(f"📁 Logs enregistrés dans : {LOG_DIR}")
    logging.info(f"   - Logs principaux    : {LOG_FILE_MAIN.name}")
    logging.info(f"   - Erreurs uniquement : {LOG_FILE_ERRORS.name}")
    logging.info(f"   - Transcriptions     : {LOG_FILE_TRANSCRIPTION.name}")
    logging.info(f"   - Insights           : {LOG_FILE_INSIGHTS.name}")
    logging.info(f"📊 Niveau de log : {LOG_LEVEL}")
    logging.info(f"🔄 Rotation : {LOG_MAX_BYTES // (1024*1024)} MB, {LOG_BACKUP_COUNT} backups")
    logging.info(f"{'='*80}\n")

# Initialiser le logging
setup_logging()

logger = logging.getLogger(__name__)

# Création de l'application
app = FastAPI(
    title="KITT Backend",
    description="API de coaching commercial en temps réel avec IA",
    version=VERSION
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import et enregistrement des routes
from api import calls, audio, insights, summary

app.include_router(calls.router)
app.include_router(audio.router)
app.include_router(insights.router)
app.include_router(summary.router)

# ═══════════════════════════════════════════════════════════════════════════
# PRÉCHARGEMENT DES MODÈLES AU DÉMARRAGE
# ═══════════════════════════════════════════════════════════════════════════
@app.on_event("startup")
async def startup_event():
    """Précharge les modèles lourds au démarrage du serveur"""
    logger.info("\n" + "="*80)
    logger.info("🔄 PRÉCHARGEMENT DES MODÈLES")
    logger.info("="*80)

    # Précharger le modèle d'embeddings pour la détection de doublons
    try:
        from services.duplicate_detector import get_embedding_model
        logger.info("📥 Chargement du modèle sentence-transformers...")
        model = get_embedding_model()

        # Force le téléchargement complet des poids du modèle
        logger.info("🔄 Téléchargement des poids du modèle (peut prendre quelques secondes)...")
        _ = model.encode(["test preload"], show_progress_bar=False)

        logger.info("✅ Modèle d'embeddings préchargé avec succès")
        logger.info(f"   Type: {type(model).__name__}")
        logger.info(f"   Modèle: paraphrase-multilingual-MiniLM-L12-v2")
    except Exception as e:
        logger.error(f"❌ Erreur lors du préchargement du modèle: {e}")

    logger.info("="*80)
    logger.info("✅ Serveur prêt à traiter les requêtes")
    logger.info("="*80 + "\n")


# Routes principales
@app.get("/")
async def root():
    """Informations sur l'API"""
    return {
        "message": "KITT Backend - Version Refactorisée",
        "version": VERSION,
        "description": "Architecture modulaire et scalable",
        "features": [
            f"🔥 Contexte étendu ({MAX_CONTEXT_MESSAGES} messages max)",
            "🔥 Tracking de phase de conversation",
            "🔥 Extraction automatique des pain points",
            "🔥 Système de personnalité client dynamique",
            "🔥 Fine-tuning GPT-4o-mini optimisé",
            "🔥 Anti-doublon IA avec fenêtre temporelle",
            "🔥 Architecture modulaire (services séparés)",
            "🔥 Historique complet des insights",
            "🔥 2 endpoints de résumé (client + commercial)"
        ],
        "architecture": {
            "api": "Routes FastAPI modulaires par domaine",
            "core": "CallManager avec contexte structuré",
            "services": [
                "TranscriptionService (Deepgram Nova-2)",
                "ContextAnalyzer (Phase, pain points, concepts)",
                "CoachingService (Insights temps réel)",
                "SummaryService (Résumés structurés)"
            ],
            "models": "Pydantic schemas + profils clients",
            "config": "Configuration centralisée"
        },
        "endpoints": {
            "calls": {
                "start": "POST /calls/start",
                "end": "POST /calls/{session_id}/end",
                "state": "GET /calls/{session_id}/state"
            },
            "audio": {
                "process": "POST /audio/{session_id}"
            },
            "insights": {
                "history": "GET /calls/{session_id}/insights"
            },
            "summary": {
                "client_focused": "POST /resume/{session_id}",
                "commercial_focused": "POST /summary/{session_id}"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Vérification de santé du backend"""
    from api.calls import get_active_calls
    
    active_calls = get_active_calls()
    
    return {
        "status": "healthy",
        "version": VERSION,
        "active_calls": len(active_calls),
        "max_context_messages": MAX_CONTEXT_MESSAGES,
        "features": [
            "extended-context-window",
            "structured-context",
            "conversation-phase-tracking",
            "pain-point-extraction",
            "ai-duplicate-detection",
            "temporal-filtering",
            "modular-architecture",
            "fine-tuned-model",
            "insights-history",
            "dual-summary-modes"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
