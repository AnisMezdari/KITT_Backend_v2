"""
Routes API pour le traitement audio et génération d'insights
"""
import logging
import numpy as np
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException

from services import TranscriptionService, CoachingService
from services.relevance_filter import RelevanceFilter
from api.calls import get_active_calls
from config.settings import (
    TIME_THRESHOLD_DUPLICATE,
    COOLDOWN_BASE,
    COOLDOWN_HIGH_RELEVANCE,
    COOLDOWN_AFTER_INSIGHT,
    MIN_RELEVANCE_SCORE,
    ALLOW_COOLDOWN_BYPASS
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audio"])

# Services
transcription_service = TranscriptionService()
coaching_service = CoachingService()
relevance_filter = RelevanceFilter()


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

    # ═══════════════════════════════════════════════════════════════════════════
    # 🆕 DÉTECTION DE L'ORDRE CHRONOLOGIQUE
    # ═══════════════════════════════════════════════════════════════════════════
    # Détecte qui a parlé en premier en analysant le début de la parole dans chaque audio
    client_start_time = transcription_service.detect_speech_start_time(client_audio, "CLIENT")
    commercial_start_time = transcription_service.detect_speech_start_time(commercial_audio, "COMMERCIAL")

    # Déterminer qui a parlé en premier
    client_spoke_first = client_start_time < commercial_start_time

    logger.info(f"[CHRONOLOGIE] Client start: {client_start_time:.3f}s, Commercial start: {commercial_start_time:.3f}s")
    logger.info(f"[CHRONOLOGIE] {'CLIENT' if client_spoke_first else 'COMMERCIAL'} a parlé en premier")

    # TRANSCRIPTION PARALLÈLE
    client_text, commercial_text = await transcription_service.transcribe_parallel(
        client_audio,
        commercial_audio
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # ✅ AJOUT AU CONTEXTE DANS L'ORDRE CHRONOLOGIQUE
    # ═══════════════════════════════════════════════════════════════════════════
    if client_spoke_first:
        # CLIENT a parlé en premier → ajouter dans l'ordre : CLIENT puis COMMERCIAL
        if client_text:
            await manager.add_message("assistant", client_text)
        if commercial_text:
            await manager.add_message("user", commercial_text)
    else:
        # COMMERCIAL a parlé en premier → ajouter dans l'ordre : COMMERCIAL puis CLIENT
        if commercial_text:
            await manager.add_message("user", commercial_text)
        if client_text:
            await manager.add_message("assistant", client_text)

    # Log historique
    if client_text or commercial_text:
        manager.log_conversation_history()

    # Si aucun des deux n'a parlé
    if not client_text and not commercial_text:
        return {"advice": None, "transcription": ""}

    # ═══════════════════════════════════════════════════════════════════════════
    # 🆕 SYSTÈME DE PERTINENCE INTELLIGENTE v2
    # ═══════════════════════════════════════════════════════════════════════════

    # 1. Vérifier le score de pertinence AVANT de générer l'insight
    should_generate, relevance_score, analysis = relevance_filter.should_generate_insight(
        manager.messages,
        manager.pillar_progress,
        manager.last_insight_time,
        manager.conversation_phase,
        min_score=MIN_RELEVANCE_SCORE
    )

    # 2. Cooldown adaptatif
    current_time = datetime.now().timestamp()
    elapsed_since_last = current_time - manager.last_insight_time if manager.last_insight_time > 0 else 999

    # Déterminer le cooldown requis selon le score
    if relevance_score >= 85:
        required_cooldown = COOLDOWN_HIGH_RELEVANCE  # 10s pour événements critiques
    elif relevance_score >= 70:
        required_cooldown = COOLDOWN_BASE  # 20s pour pertinence moyenne
    else:
        required_cooldown = COOLDOWN_AFTER_INSIGHT  # 25s pour faible pertinence

    # Vérifier le cooldown (sauf bypass autorisé)
    cooldown_active = elapsed_since_last < required_cooldown
    can_bypass = ALLOW_COOLDOWN_BYPASS and relevance_score >= 85

    if cooldown_active and not can_bypass:
        logger.info(f"\n{'='*80}")
        logger.info(f"[COOLDOWN] ⏸️  INSIGHT BLOQUÉ - COOLDOWN ACTIF")
        logger.info(f"{'='*80}")
        logger.info(f"[COOLDOWN] ⏱️  Temps écoulé: {elapsed_since_last:.1f}s / {required_cooldown}s requis")
        logger.info(f"[COOLDOWN] 📊 Score de pertinence: {relevance_score}/100")
        logger.info(f"[COOLDOWN] 🚫 Raison: Cooldown adaptatif en cours")
        logger.info(f"{'='*80}\n")

        return {
            "advice": None,
            "transcription": f"CLIENT: {client_text}\nCOMMERCIAL: {commercial_text}",
            "reason": "cooldown_active",
            "cooldown_info": {
                "elapsed": round(elapsed_since_last, 1),
                "required": required_cooldown,
                "relevance_score": relevance_score
            }
        }

    # Si score trop faible, ne pas générer
    if not should_generate:
        logger.info(f"\n{'='*80}")
        logger.info(f"[PERTINENCE] 🚫 INSIGHT NON GÉNÉRÉ - SCORE TROP FAIBLE")
        logger.info(f"{'='*80}")
        logger.info(f"[PERTINENCE] 📊 Score: {relevance_score}/100 (min requis: {MIN_RELEVANCE_SCORE})")
        logger.info(f"[PERTINENCE] 📝 Analyse: {', '.join(analysis['reasons'])}")
        logger.info(f"[PERTINENCE] 💡 Triggers: {', '.join(analysis['triggers']) if analysis['triggers'] else 'Aucun'}")
        logger.info(f"{'='*80}\n")

        return {
            "advice": None,
            "transcription": f"CLIENT: {client_text}\nCOMMERCIAL: {commercial_text}",
            "reason": "low_relevance",
            "relevance_info": {
                "score": relevance_score,
                "min_required": MIN_RELEVANCE_SCORE,
                "analysis": analysis
            }
        }

    # 3. Si on arrive ici : pertinence OK + cooldown OK → Générer l'insight
    logger.info(f"\n{'='*80}")
    logger.info(f"[PERTINENCE] ✅ GÉNÉRATION D'INSIGHT AUTORISÉE")
    logger.info(f"{'='*80}")
    logger.info(f"[PERTINENCE] 📊 Score: {relevance_score}/100")
    logger.info(f"[PERTINENCE] ⏱️  Cooldown: {elapsed_since_last:.1f}s (requis: {required_cooldown}s)")
    logger.info(f"[PERTINENCE] 🎯 Triggers: {', '.join(analysis['triggers'])}")
    logger.info(f"{'='*80}\n")

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
    
    # Générer l'insight complet
    full_insight = f"{advice_json['title']} - {advice_json['details']['description']}"

    # VÉRIFICATION ANTI-DOUBLON
    logger.info(f"\n{'='*80}")
    logger.info(f"[ANTI-DOUBLON] 🔍 VÉRIFICATION DOUBLON EN COURS")
    logger.info(f"{'='*80}")
    logger.info(f"[INSIGHT] 📝 NOUVEL INSIGHT GÉNÉRÉ:")
    logger.info(f"[INSIGHT]    Type: {advice_json['type'].upper()}")
    logger.info(f"[INSIGHT]    Titre: {advice_json['title']}")
    logger.info(f"[INSIGHT]    Action: {advice_json['details']['description']}")
    logger.info(f"[INSIGHT]    Insight complet: {full_insight}")
    logger.info(f"{'='*80}")

    # Vérification de doublon avec détection titre + sémantique
    is_duplicate = await manager.is_duplicate_insight(
        full_insight,
        new_title=advice_json['title'],  # ✅ Passer le titre pour vérification anti-répétition
        time_threshold_seconds=TIME_THRESHOLD_DUPLICATE
    )

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

    # Ajouter l'insight au cache
    logger.info(f"\n{'='*80}")
    logger.info(f"[ANTI-DOUBLON] ✅ INSIGHT VALIDÉ ET ACCEPTÉ")
    logger.info(f"{'='*80}")
    logger.info(f"[INSIGHT] ✨ AJOUT AU CACHE:")
    logger.info(f"[INSIGHT]    Type: {advice_json['type'].upper()}")
    logger.info(f"[INSIGHT]    Titre: {advice_json['title']}")
    logger.info(f"[INSIGHT]    Action: {advice_json['details']['description']}")
    logger.info(f"{'='*80}\n")
    manager.add_insight(full_insight, title=advice_json['title'])  # ✅ Passer le titre pour tracking
    
    return {
        "advice": advice_json,
        "transcription": f"CLIENT: {client_text}\nCOMMERCIAL: {commercial_text}",
        "conversation_phase": manager.conversation_phase
    }


