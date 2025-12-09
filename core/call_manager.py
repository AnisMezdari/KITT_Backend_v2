"""
Gestionnaire de session d'appel avec contexte structuré
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from models import CallConfig, PROFILE_TEMPLATES
from services.context_analyzer import ContextAnalyzer
from services.duplicate_detector import DuplicateDetector
from config.settings import MAX_CONTEXT_MESSAGES, MAX_INSIGHTS_CACHE

logger = logging.getLogger(__name__)


class CallManager:
    """Gestionnaire de session d'appel avec contexte structuré + personnalité client"""
    
    def __init__(self, config: Optional[CallConfig] = None):
        self.call_id: Optional[str] = None
        self.config = self._apply_profile_defaults(config) if config else None
        
        # Messages et transcripts
        self.messages: List[Dict] = []
        self.full_transcript: List[Dict] = []
        
        # Insights
        self.last_insights: List[str] = []
        self.insight_timestamps: List[float] = []
        self.recent_concepts: List[str] = []
        self.last_insight_time: float = 0
        
        # Contexte structuré
        self.conversation_summary = ""
        self.pain_points: List[str] = []
        self.conversation_phase = "introduction"
        self.topics_covered: List[str] = []
        self.needs_summary_update = False
        
        # Métriques de performance
        self.performance_metrics = {
            "objections_handled": 0,
            "engagement_evolution": [],
            "client_emotional_arc": [],
            "trait_evolution": {
                "openness": [], "patience": [], "empathy": [],
                "confidence": [], "risk_tolerance": [], "objection_level": [],
                "engagement_level": [], "frustration": [], "curiosity": []
            },
            "seller_performance": []
        }
        
        # Services
        self.context_analyzer = ContextAnalyzer()
        self.duplicate_detector = DuplicateDetector()
        
        self.created_at = datetime.now()
    
    def _apply_profile_defaults(self, config: CallConfig) -> CallConfig:
        """Applique automatiquement les valeurs par défaut d'un profil client"""
        primary = PROFILE_TEMPLATES.get(config.client_personality.primary_profile)
        if not primary:
            return config

        personality = config.client_personality
        for key in ["objection_level", "engagement_level", "curiosity", "frustration",
                    "patience", "empathy", "confidence", "risk_tolerance"]:
            template_value = primary.get(key)
            if template_value is not None:
                if hasattr(personality, key):
                    current_value = getattr(personality, key)
                    if current_value in [0.5, 0.0]:
                        setattr(personality, key, template_value)
                else:
                    personality.custom_traits[key] = template_value

        return config
    
    async def add_message(self, role: str, content: str):
        """Ajoute un message et maintient l'historique limité"""
        message = {"role": role, "content": content}

        self.full_transcript.append(message)
        self.messages.append(message)

        # Mise à jour du contexte structuré (avec IA pour la phase)
        await self._update_structured_context()

        # Limiter l'historique
        if len(self.messages) > MAX_CONTEXT_MESSAGES:
            self.needs_summary_update = True
            self.messages = self.messages[-MAX_CONTEXT_MESSAGES:]
            logger.info(f"[CONTEXT] Historique tronqué à {MAX_CONTEXT_MESSAGES} messages")
    
    async def _update_structured_context(self):
        """Met à jour le contexte structuré avec détection de phase IA"""
        # 🆕 Utiliser la détection de phase avec IA
        self.conversation_phase = await self.context_analyzer.detect_conversation_phase_ai(self.messages)
        self.pain_points = self.context_analyzer.extract_pain_points(self.messages)
        
        if self.recent_concepts:
            all_topics = set()
            for concepts in self.recent_concepts:
                all_topics.update(concepts.split(", "))
            self.topics_covered = list(all_topics)[-10:]
    
    def get_structured_context(self) -> str:
        """Retourne le contexte structuré formaté"""
        duration_info = f"{len(self.full_transcript)} échanges"
        
        pain_points_str = "Aucun identifié pour le moment"
        if self.pain_points:
            pain_points_str = "\n".join([f"  • {pp}" for pp in self.pain_points[-3:]])
        
        topics_str = ", ".join(self.topics_covered[-8:]) if self.topics_covered else "Aucun"
        
        phase_str = self.context_analyzer.get_phase_label(self.conversation_phase)
        
        structured_context = f"""
═══════════════════════════════════════════════════════════════════════════
📊 CONTEXTE GLOBAL DE L'APPEL
═══════════════════════════════════════════════════════════════════════════
🔄 Phase actuelle : {phase_str}
⏱️  Durée : {duration_info}

💡 Pain Points Identifiés :
{pain_points_str}

📝 Sujets Déjà Traités : {topics_str}

{self.conversation_summary}
═══════════════════════════════════════════════════════════════════════════
"""
        return structured_context
    
    def get_context_window(self, max_messages: int = None) -> List[Dict]:
        """
        🆕 Retourne la fenêtre de contexte (adaptative selon la phase)
        Optimisation: Contexte plus court en début, plus long en négociation/closing
        """
        if max_messages is not None:
            # Si un maximum est spécifié, l'utiliser
            limit = max_messages
        else:
            # Calcul adaptatif selon la phase
            if self.conversation_phase in ["introduction", "discovery"]:
                limit = 15  # Début : contexte court suffit
            elif self.conversation_phase == "presentation":
                limit = 30  # Présentation : contexte moyen
            else:
                limit = 50  # Negotiation/Closing : contexte complet

        return self.messages[-limit:]
    
    def get_full_transcript(self) -> str:
        """Retourne le transcript complet pour le résumé"""
        parts = []
        for msg in self.full_transcript:
            role = "COMMERCIAL" if msg['role'] == 'user' else "CLIENT"
            parts.append(f"{role}: {msg['content']}")
        return "\n".join(parts)
    
    def add_insight(self, insight: str):
        """Ajoute un insight au cache avec extraction de concepts et timestamp"""
        current_time = datetime.now().timestamp()
        
        self.last_insights.append(insight)
        self.last_insight_time = current_time
        self.insight_timestamps.append(current_time)
        
        concepts = self.context_analyzer.extract_key_concepts(insight)
        self.recent_concepts.append(concepts)
        
        # Limiter l'historique
        if len(self.last_insights) > MAX_INSIGHTS_CACHE:
            self.last_insights = self.last_insights[-MAX_INSIGHTS_CACHE:]
            self.recent_concepts = self.recent_concepts[-MAX_INSIGHTS_CACHE:]
            self.insight_timestamps = self.insight_timestamps[-MAX_INSIGHTS_CACHE:]
    
    async def is_duplicate_insight(self, new_insight: str, time_threshold_seconds: int = None) -> bool:
        """
        Vérifie si l'insight est un doublon avec VECTORISATION SÉMANTIQUE

        🆕 Harmonisé à 30s (TIME_THRESHOLD_DUPLICATE) pour cohérence
        Nouvelle méthode: Utilise sentence-transformers pour une détection plus rapide et précise
        """
        is_dup, analysis = self.duplicate_detector.check_duplicate_semantic(
            new_insight,
            self.last_insights,
            self.insight_timestamps,
            time_threshold_seconds  # Utilisera TIME_THRESHOLD_DUPLICATE (30s) si None
        )
        return is_dup
    
    def should_throttle(self, min_interval: int = 20) -> bool:
        """Vérifie si on doit throttler"""
        if self.last_insight_time == 0:
            return False
        
        elapsed = datetime.now().timestamp() - self.last_insight_time
        
        if elapsed < min_interval:
            logger.info(f"[THROTTLE] Trop tôt pour nouvel insight ({elapsed:.1f}s < {min_interval}s)")
            return True
        
        return False
    
    def _clamp_value(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """S'assure qu'une valeur reste dans les limites"""
        return max(min_val, min(max_val, value))
    
    def _track_trait_evolution(self) -> None:
        """Enregistre l'évolution des traits pour l'analyse"""
        if not self.config:
            return
        
        personality = self.config.client_personality
        for trait in ["openness", "patience", "empathy", "confidence", "risk_tolerance",
                      "objection_level", "engagement_level", "frustration", "curiosity"]:
            if hasattr(personality, trait):
                value = getattr(personality, trait)
                self.performance_metrics["trait_evolution"][trait].append(value)
    
    def log_conversation_history(self):
        """Affiche l'historique de contexte"""
        logger.info("\n" + "="*80)
        logger.info(f"📚 CONTEXTE ACTUEL ({len(self.messages)}/{MAX_CONTEXT_MESSAGES} messages)")
        logger.info(f"🔄 Phase: {self.conversation_phase}")
        logger.info(f"💡 Pain points: {len(self.pain_points)}")
        logger.info(f"📝 Topics couverts: {', '.join(self.topics_covered[-5:])}")
        logger.info("="*80)
        
        if not self.messages:
            logger.info("Aucun message dans le contexte")
        else:
            for i, msg in enumerate(self.messages[-5:], 1):
                role = "🗣️  COMMERCIAL" if msg['role'] == 'user' else "👤 CLIENT"
                content = msg.get('content', '')
                logger.info(f"\n[...{i}] {role}: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        logger.info(f"\n💾 Historique complet: {len(self.full_transcript)} messages")
        logger.info("="*80 + "\n")
