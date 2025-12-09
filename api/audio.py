"""
Routes API pour le traitement audio et génération d'insights
"""
import logging
import numpy as np
from fastapi import APIRouter, Request, HTTPException

from services import TranscriptionService, CoachingService
from api.calls import get_active_calls
from config.settings import TIME_THRESHOLD_DUPLICATE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audio"])

# Services
transcription_service = TranscriptionService()
coaching_service = CoachingService()


@router.post("/audio/{session_id}")
async def process_audio(session_id: str, request: Request):
    """
    Traite l'audio client et commercial, génère des insights
    Version optimisée avec contexte structuré enrichi
    """
    
    active_calls = get_active_calls()
    
    if session_id not in active_calls:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    manager = active_calls[session_id]
    
    # Récupérer les fichiers audio
    form = await request.form()
    client_audio_file = form.get('client_audio')
    commercial_audio_file = form.get('commercial_audio')
    
    if not client_audio_file or not commercial_audio_file:
        raise HTTPException(status_code=400, detail="Les deux fichiers audio sont requis")
    
    # Lire les données audio
    client_data = await client_audio_file.read()
    commercial_data = await commercial_audio_file.read()
    
    client_audio = np.frombuffer(client_data, dtype=np.int16)
    commercial_audio = np.frombuffer(commercial_data, dtype=np.int16)
    
    # TRANSCRIPTION PARALLÈLE
    client_text, commercial_text = await transcription_service.transcribe_parallel(
        client_audio,
        commercial_audio
    )
    
    # Ajouter au contexte (🆕 avec await pour détection phase IA)
    if client_text:
        await manager.add_message("assistant", client_text)

    if commercial_text:
        await manager.add_message("user", commercial_text)

    # Log historique
    if client_text or commercial_text:
        manager.log_conversation_history()

    # Si aucun des deux n'a parlé
    if not client_text and not commercial_text:
        return {"advice": None, "transcription": ""}

    # 🗑️ THROTTLING SUPPRIMÉ (MIN_INSIGHT_INTERVAL=0, code mort inutile)
    
    # CONSTRUCTION DU CONTEXTE
    context_window = manager.get_context_window()
    context = "\n".join([
        f"{'COMMERCIAL' if msg['role'] == 'user' else 'CLIENT'}: {msg['content']}" 
        for msg in context_window
    ])
    
    # GÉNÉRATION DU COACHING
    prompt = coaching_service.build_coaching_prompt(context, manager)
    raw_advice = await coaching_service.generate_insight(prompt)
    
    if not raw_advice:
        return {
            "advice": None,
            "transcription": f"CLIENT: {client_text}\nCOMMERCIAL: {commercial_text}"
        }
    
    # PARSING
    advice_json = coaching_service.parse_insight_response(raw_advice)
    
    if not advice_json:
        return {
            "advice": None,
            "transcription": f"CLIENT: {client_text}\nCOMMERCIAL: {commercial_text}"
        }
    
    # VÉRIFICATION ANTI-DOUBLON AVEC IA (avec prise en compte du temps)
    full_insight = f"{advice_json['title']} - {advice_json['details']['description']}"
    
    logger.info(f"\n{'='*80}")
    logger.info(f"[ANTI-DOUBLON] 🔍 VÉRIFICATION DOUBLON EN COURS")
    logger.info(f"{'='*80}")
    logger.info(f"[INSIGHT] 📝 NOUVEL INSIGHT GÉNÉRÉ:")
    logger.info(f"[INSIGHT]    Type: {advice_json['type'].upper()}")
    logger.info(f"[INSIGHT]    Titre: {advice_json['title']}")
    logger.info(f"[INSIGHT]    Action: {advice_json['details']['description']}")
    logger.info(f"[INSIGHT]    Insight complet: {full_insight}")
    logger.info(f"{'='*80}")
    logger.info(f"[INSIGHT] ⏱️  Seuil temporel harmonisé: {TIME_THRESHOLD_DUPLICATE}s (utilisé partout)")
    logger.info(f"[INSIGHT] 🧬 Vérification par vectorisation sémantique...")

    # 🆕 Utiliser le seuil harmonisé (30s par défaut)
    is_duplicate = await manager.is_duplicate_insight(full_insight, time_threshold_seconds=TIME_THRESHOLD_DUPLICATE)
    
    if is_duplicate:
        logger.info(f"\n{'='*80}")
        logger.info(f"[ANTI-DOUBLON] ❌ INSIGHT REJETÉ - DOUBLON DÉTECTÉ")
        logger.info(f"{'='*80}")
        logger.info(f"[INSIGHT] 🚫 INSIGHT BLOQUÉ:")
        logger.info(f"[INSIGHT]    Type: {advice_json['type'].upper()}")
        logger.info(f"[INSIGHT]    Titre: {advice_json['title']}")
        logger.info(f"[INSIGHT]    Action: {advice_json['details']['description']}")
        logger.info(f"[INSIGHT]    Insight complet: {full_insight}")
        logger.info(f"")
        logger.info(f"[INSIGHT] 📊 HISTORIQUE DES INSIGHTS (pour comparaison):")
        for i, old_insight in enumerate(manager.last_insights[-5:], 1):
            logger.info(f"[INSIGHT]    {i}. {old_insight[:80]}...")
        logger.info(f"{'='*80}\n")
        
        return {
            "advice": None,
            "transcription": f"CLIENT: {client_text}\nCOMMERCIAL: {commercial_text}",
            "reason": "duplicate",
            "blocked_insight": {
                "type": advice_json['type'],
                "title": advice_json['title'],
                "description": advice_json['details']['description'],
                "full_text": full_insight
            }
        }
    
    # Ajouter au cache
    logger.info(f"\n{'='*80}")
    logger.info(f"[ANTI-DOUBLON] ✅ INSIGHT VALIDÉ ET ACCEPTÉ")
    logger.info(f"{'='*80}")
    logger.info(f"[INSIGHT] ✨ INSIGHT AJOUTÉ AU CACHE:")
    logger.info(f"[INSIGHT]    Type: {advice_json['type'].upper()}")
    logger.info(f"[INSIGHT]    Titre: {advice_json['title']}")
    logger.info(f"[INSIGHT]    Action: {advice_json['details']['description']}")
    logger.info(f"{'='*80}\n")
    manager.add_insight(full_insight)
    
    return {
        "advice": advice_json,
        "transcription": f"CLIENT: {client_text}\nCOMMERCIAL: {commercial_text}",
        "conversation_phase": manager.conversation_phase
    }


