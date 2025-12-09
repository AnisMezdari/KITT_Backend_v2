"""
Routes API pour les résumés d'appels
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from models import MessageRequest
from services import SummaryService
from api.calls import get_active_calls

logger = logging.getLogger(__name__)

router = APIRouter(tags=["summary"])

# Service
summary_service = SummaryService()


@router.post("/resume/{session_id}")
async def summarize_call_client_focused(session_id: str, request: MessageRequest) -> Dict[str, Any]:
    """
    Résume l'appel complet avec note et évaluation détaillée
    FOCUS : Client (ses besoins, objections, attentes)
    """
    active_calls = get_active_calls()
    
    if session_id not in active_calls:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    manager = active_calls[session_id]

    full_transcript = manager.get_full_transcript()
    
    if not full_transcript.strip():
        return {"error": "Aucune conversation enregistrée pour ce résumé."}

    logger.info(f"\n{'='*80}")
    logger.info("📊 GÉNÉRATION DU RÉSUMÉ (FOCUS CLIENT)")
    logger.info(f"{'='*80}")
    logger.info(f"Messages: {len(manager.full_transcript)}")
    logger.info(f"Phase: {manager.conversation_phase}")
    logger.info(f"{'='*80}\n")

    summary_json = await summary_service.generate_client_focused_summary(full_transcript)
    
    if not summary_json:
        return {"error": "Erreur lors de la génération du résumé"}
    
    return {"summary": summary_json}


@router.post("/summary/{session_id}")
async def summarize_call_commercial_focused(session_id: str, request: MessageRequest) -> Dict[str, Any]:
    """
    Résume l'appel avec focus sur l'évaluation du commercial
    FOCUS : Commercial (performance, points forts/faibles)
    """
    active_calls = get_active_calls()
    
    if session_id not in active_calls:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    manager = active_calls[session_id]

    # Récupérer le texte du dialogue
    text = (request.user_message or "").strip()

    if not text:
        parts = []
        for msg in manager.messages:
            if isinstance(msg, dict):
                parts.append(str(msg.get("content") or msg.get("text") or msg.get("user_message") or ""))
            elif isinstance(msg, str):
                parts.append(msg)
            else:
                parts.append(str(msg))
        text = " ".join([p for p in parts if p]).strip()

    if not text:
        return {"error": "Aucune conversation disponible pour ce résumé."}

    logger.info(f"\n{'='*80}")
    logger.info("📊 GÉNÉRATION DU RÉSUMÉ (FOCUS COMMERCIAL)")
    logger.info(f"{'='*80}")
    logger.info(f"Longueur texte: {len(text)} caractères")
    logger.info(f"{'='*80}\n")

    summary_json = await summary_service.generate_commercial_focused_summary(text)
    
    if not summary_json:
        return {"error": "Erreur lors de la génération du résumé"}

    return {"summary": summary_json}
