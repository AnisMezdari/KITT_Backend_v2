"""
Routes API pour la gestion des sessions d'appels
"""
import logging
import uuid
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from models import CallConfig
from core import CallManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calls", tags=["calls"])

# Stockage des sessions actives
active_calls: Dict[str, CallManager] = {}


@router.post("/start")
async def start_call(config: CallConfig = None) -> Dict[str, Any]:
    """Démarre une nouvelle session d'appel"""
    call_id = str(uuid.uuid4())
    manager = CallManager(config)
    manager.call_id = call_id
    active_calls[call_id] = manager
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🟢 DÉBUT SESSION: {call_id}")
    logger.info(f"{'='*80}\n")

    # Log spécifique pour le fichier de transcription
    logger.info(f"[TRANSCRIPTION] {'='*60}")
    logger.info(f"[TRANSCRIPTION] 🎙️ NOUVELLE SESSION DÉMARRÉE")
    logger.info(f"[TRANSCRIPTION] ID: {call_id}")
    logger.info(f"[TRANSCRIPTION] Date: {manager.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"[TRANSCRIPTION] {'='*60}")
    
    result = {
        "call_id": call_id,
        "status": "active",
        "created_at": manager.created_at.isoformat(),
        "max_context_messages": manager.context_analyzer.__class__.__name__,  # Placeholder
        "conversation_phase": manager.conversation_phase
    }
    
    if config:
        result["client_profile"] = config.client_personality.dict()
    
    return result


@router.post("/{session_id}/end")
async def end_call(session_id: str):
    """Termine une session d'appel"""
    
    if session_id not in active_calls:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    manager = active_calls[session_id]
    
    manager.log_conversation_history()
    
    context_count = len(manager.messages)
    total_count = len(manager.full_transcript)
    insight_count = len(manager.last_insights)
    
    del active_calls[session_id]

    logger.info(f"\n{'='*80}")
    logger.info(f"🔴 FIN SESSION: {session_id}")
    logger.info(f"{'='*80}\n")

    # Log spécifique pour le fichier de transcription
    logger.info(f"[TRANSCRIPTION] {'='*60}")
    logger.info(f"[TRANSCRIPTION] 🏁 SESSION TERMINÉE")
    logger.info(f"[TRANSCRIPTION] ID: {session_id}")
    logger.info(f"[TRANSCRIPTION] Messages contexte: {context_count}")
    logger.info(f"[TRANSCRIPTION] Messages total: {total_count}")
    logger.info(f"[TRANSCRIPTION] Insights générés: {insight_count}")
    logger.info(f"[TRANSCRIPTION] Phase finale: {manager.conversation_phase}")
    logger.info(f"[TRANSCRIPTION] {'='*60}")
    
    return {
        "status": "ended",
        "context_message_count": context_count,
        "total_message_count": total_count,
        "insight_count": insight_count,
        "final_phase": manager.conversation_phase,
        "pain_points_identified": len(manager.pain_points)
    }


@router.get("/{session_id}/state")
async def get_call_state(session_id: str):
    """Récupère l'état d'une session"""
    
    if session_id not in active_calls:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    manager = active_calls[session_id]
    
    from config.settings import MAX_CONTEXT_MESSAGES
    
    result = {
        "call_id": session_id,
        "context_message_count": len(manager.messages),
        "total_message_count": len(manager.full_transcript),
        "insight_count": len(manager.last_insights),
        "created_at": manager.created_at.isoformat(),
        "last_insights": manager.last_insights[-3:] if manager.last_insights else [],
        "recent_concepts": manager.recent_concepts[-3:] if manager.recent_concepts else [],
        "max_context_messages": MAX_CONTEXT_MESSAGES,
        "conversation_phase": manager.conversation_phase,
        "pain_points": manager.pain_points,
        "topics_covered": manager.topics_covered
    }
    
    if manager.config:
        personality = manager.config.client_personality
        result["current_personality"] = {
            "openness": round(personality.openness, 3),
            "patience": round(personality.patience, 3),
            "empathy": round(personality.empathy, 3),
            "confidence": round(personality.confidence, 3),
            "risk_tolerance": round(personality.risk_tolerance, 3),
            "objection_level": round(personality.objection_level, 3),
            "engagement_level": round(personality.engagement_level, 3),
            "frustration": round(personality.frustration, 3),
            "curiosity": round(personality.curiosity, 3),
            "mood": personality.mood
        }
    
    return result


def get_active_calls():
    """Fonction utilitaire pour accéder aux appels actifs depuis d'autres routes"""
    return active_calls
