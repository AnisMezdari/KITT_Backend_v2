"""
Package des modèles de données
"""
from models.schemas import (
    ClientProfile,
    InsightType,
    ClientPersonality,
    CallConfig,
    PersonalityTuning,
    MessageRequest,
    InsightResponse,
    AudioProcessResponse,
    CallStateResponse,
    InsightHistoryResponse,
    SummaryResponse
)
from models.profiles import PROFILE_TEMPLATES

__all__ = [
    "ClientProfile",
    "InsightType",
    "ClientPersonality",
    "CallConfig",
    "PersonalityTuning",
    "MessageRequest",
    "InsightResponse",
    "AudioProcessResponse",
    "CallStateResponse",
    "InsightHistoryResponse",
    "SummaryResponse",
    "PROFILE_TEMPLATES"
]
