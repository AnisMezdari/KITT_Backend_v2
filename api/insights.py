"""
Routes API pour l'historique et les statistiques des insights
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

from api.calls import get_active_calls

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calls", tags=["insights"])


@router.get("/{session_id}/insights")
async def get_insights_history(session_id: str) -> Dict[str, Any]:
    """
    Récupère l'historique COMPLET des insights générés pour cette session
    
    Retourne:
    - Liste complète de tous les insights avec timestamps
    - Concepts associés
    - Temps écoulé depuis chaque insight
    - Statistiques
    """
    active_calls = get_active_calls()
    
    if session_id not in active_calls:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    manager = active_calls[session_id]
    
    current_time = datetime.now().timestamp()
    
    # Construire l'historique détaillé
    insights_with_metadata = []
    for i, insight in enumerate(manager.last_insights):
        # Récupérer les concepts associés
        concepts = manager.recent_concepts[i] if i < len(manager.recent_concepts) else "général"
        
        # Récupérer le timestamp
        if i < len(manager.insight_timestamps):
            timestamp = manager.insight_timestamps[i]
            time_elapsed = current_time - timestamp
            minutes_ago = int(time_elapsed / 60)
            seconds_ago = int(time_elapsed % 60)
            time_display = f"{minutes_ago}min {seconds_ago}s ago" if minutes_ago > 0 else f"{seconds_ago}s ago"
        else:
            time_elapsed = 0
            time_display = "Unknown"
        
        # Extraire le type d'insight
        insight_type = "unknown"
        if "🔴" in insight or "alerte" in insight.lower():
            insight_type = "alert"
        elif "🔵" in insight or "opportunité" in insight.lower():
            insight_type = "opportunity"
        elif "🟢" in insight or "progression" in insight.lower():
            insight_type = "progression"
        
        # Déterminer si l'insight est "ancien" (> 60s)
        is_old = time_elapsed > 60
        
        insights_with_metadata.append({
            "index": i + 1,
            "insight": insight,
            "concepts": concepts,
            "type": insight_type,
            "time_ago": time_display,
            "seconds_elapsed": int(time_elapsed),
            "is_old": is_old,
            "status": "⏰ ANCIEN" if is_old else "🔥 RÉCENT"
        })
    
    # Statistiques par type
    type_counts = {"alert": 0, "opportunity": 0, "progression": 0, "unknown": 0}
    for item in insights_with_metadata:
        type_counts[item["type"]] += 1
    
    # Concepts les plus fréquents
    all_concepts = []
    for concepts_str in manager.recent_concepts:
        all_concepts.extend(concepts_str.split(", "))
    
    concept_frequency = {}
    for concept in all_concepts:
        concept_frequency[concept] = concept_frequency.get(concept, 0) + 1
    
    # Top 10 concepts
    top_concepts = sorted(concept_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Statistiques temporelles
    recent_count = sum(1 for item in insights_with_metadata if not item["is_old"])
    old_count = len(insights_with_metadata) - recent_count
    
    return {
        "session_id": session_id,
        "total_insights": len(manager.last_insights),
        "insights": insights_with_metadata,
        "statistics": {
            "by_type": type_counts,
            "by_age": {
                "recent": recent_count,
                "old": old_count
            },
            "top_concepts": [{"concept": c[0], "count": c[1]} for c in top_concepts],
            "average_insights_per_message": round(
                len(manager.last_insights) / max(len(manager.full_transcript), 1), 2
            )
        },
        "conversation_context": {
            "phase": manager.conversation_phase,
            "total_messages": len(manager.full_transcript),
            "pain_points_identified": len(manager.pain_points)
        },
        "duplicate_detection": {
            "time_threshold_seconds": 30,
            "description": "Les insights similaires séparés de plus de 30s ne sont pas considérés comme doublons (TIME_THRESHOLD_DUPLICATE)"
        }
    }
