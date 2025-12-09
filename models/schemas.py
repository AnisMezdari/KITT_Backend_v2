"""
Modèles de données pour KITT Backend
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ClientProfile(str, Enum):
    """Profils de client disponibles"""
    INTERESTED = "interested"
    RUSHED = "rushed"
    SUSPICIOUS = "suspicious"
    DEMANDING = "demanding"
    ENTHUSIASTIC = "enthusiastic"
    CURIOUS = "curious"
    OPEN = "open"
    HOSTILE = "hostile"
    BUDGET_CONSCIOUS = "budget_conscious"
    INDECISIVE = "indecisive"


class InsightType(str, Enum):
    """Types d'insights"""
    ALERT = "alert"
    OPPORTUNITY = "opportunity"
    PROGRESSION = "progression"


# ============================================================================
# CLIENT PERSONALITY MODELS
# ============================================================================

class ClientPersonality(BaseModel):
    """Personnalité dynamique du client avec comportements qui s'entrelacent"""
    primary_profile: ClientProfile
    secondary_profiles: List[ClientProfile] = []
    mood: str = "neutral"
    openness: float = 0.5
    patience: float = 0.5
    empathy: float = 0.5
    confidence: float = 0.5
    risk_tolerance: float = 0.5
    objection_level: float = 0.5
    engagement_level: float = 0.5
    frustration: float = 0.0
    curiosity: float = 0.5
    custom_traits: Dict[str, Any] = {}


class CallConfig(BaseModel):
    """Configuration de l'appel"""
    client_personality: ClientPersonality
    product_description: str
    call_context: str = "Initial cold call"
    duration_limit: int = 300
    ai_temperature: float = 0.7
    ai_top_p: float = 0.9
    custom_instructions: str = ""


class PersonalityTuning(BaseModel):
    """Fine-tuning de la personnalité"""
    profile: ClientProfile
    traits_to_adjust: Dict[str, Any]
    behavior_modifiers: Dict[str, str] = {}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class MessageRequest(BaseModel):
    """Requête d'envoi de message"""
    call_id: str
    user_message: str
    timestamp: float


class InsightResponse(BaseModel):
    """Réponse contenant un insight"""
    title: str
    type: InsightType
    details: Dict[str, str]


class AudioProcessResponse(BaseModel):
    """Réponse du traitement audio"""
    advice: Optional[InsightResponse]
    transcription: str
    conversation_phase: Optional[str] = None
    reason: Optional[str] = None
    blocked_insight: Optional[Dict[str, Any]] = None


class CallStateResponse(BaseModel):
    """État d'un appel"""
    call_id: str
    context_message_count: int
    total_message_count: int
    insight_count: int
    created_at: str
    last_insights: List[str]
    recent_concepts: List[str]
    max_context_messages: int
    conversation_phase: str
    pain_points: List[str]
    topics_covered: List[str]
    current_personality: Optional[Dict[str, Any]] = None


class InsightHistoryResponse(BaseModel):
    """Historique complet des insights"""
    session_id: str
    total_insights: int
    insights: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    conversation_context: Dict[str, Any]
    duplicate_detection: Dict[str, Any]


class SummaryResponse(BaseModel):
    """Résumé d'appel"""
    summary: Dict[str, Any]
