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
        self.last_titles: List[str] = []  # ✅ NOUVEAU: Tracking des titres pour éviter répétitions
        self.insight_timestamps: List[float] = []
        self.recent_concepts: List[str] = []
        self.last_insight_time: float = 0
        
        # Contexte structuré
        self.conversation_summary = ""
        self.pain_points: List[str] = []
        self.conversation_phase = "introduction"
        self.topics_covered: List[str] = []
        self.needs_summary_update = False

        # Tracking des 5 piliers de discovery
        self.pillar_progress = {
            1: {"name": "Comprendre le contexte", "status": "not_started", "signals": []},
            2: {"name": "Identifier le vrai problème", "status": "not_started", "signals": []},
            3: {"name": "Mesurer l'impact", "status": "not_started", "signals": []},
            4: {"name": "Valider le décisionnel", "status": "not_started", "signals": []},
            5: {"name": "Next Step intelligent", "status": "not_started", "signals": []}
        }
        
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

        # 🆕 NOUVEAU : Mise à jour de la progression des piliers
        self.update_pillar_progress(self.messages)

        if self.recent_concepts:
            all_topics = set()
            for concepts in self.recent_concepts:
                all_topics.update(concepts.split(", "))
            self.topics_covered = list(all_topics)[-10:]

    def update_pillar_progress(self, messages: List[Dict]) -> None:
        """
        Analyse les derniers échanges pour détecter la progression sur chaque pilier
        Status possibles : not_started, in_progress, completed
        """
        if not messages:
            return

        # Analyse des 5 derniers messages
        recent_messages = " ".join([m['content'].lower() for m in messages[-5:]])

        # Pilier 1 : Contexte (questions sur situation, processus, outils)
        context_keywords = ["utilisez", "processus", "actuellement", "comment", "qui", "équipe", "rôle"]
        if any(kw in recent_messages for kw in context_keywords):
            if self.pillar_progress[1]["status"] == "not_started":
                self.pillar_progress[1]["status"] = "in_progress"
            question_count = recent_messages.count("?")
            if question_count >= 2:
                self.pillar_progress[1]["status"] = "completed"

        # Pilier 2 : Pain (problème, difficulté, perte)
        pain_keywords = ["problème", "difficulté", "perd", "manque", "frustrant", "compliqué"]
        if any(kw in recent_messages for kw in pain_keywords):
            if self.pillar_progress[2]["status"] == "not_started":
                self.pillar_progress[2]["status"] = "in_progress"
            # Completed si pain + quantification
            quantif_keywords = ["heures", "jours", "€", "euros", "temps", "coûte"]
            if any(pk in recent_messages for pk in pain_keywords) and any(qk in recent_messages for qk in quantif_keywords):
                self.pillar_progress[2]["status"] = "completed"

        # Pilier 3 : Impact (quantification, urgence, conséquences)
        impact_keywords = ["combien", "coûte", "impact", "conséquences", "urgent", "important"]
        if any(kw in recent_messages for kw in impact_keywords):
            if self.pillar_progress[3]["status"] == "not_started":
                self.pillar_progress[3]["status"] = "in_progress"
            if recent_messages.count("€") > 0 or "heures" in recent_messages:
                self.pillar_progress[3]["status"] = "completed"

        # Pilier 4 : Décisionnel (budget, timeline, qui décide)
        decision_keywords = ["décide", "budget", "timing", "quand", "validation", "décision"]
        if any(kw in recent_messages for kw in decision_keywords):
            if self.pillar_progress[4]["status"] == "not_started":
                self.pillar_progress[4]["status"] = "in_progress"
            if sum(kw in recent_messages for kw in decision_keywords) >= 2:
                self.pillar_progress[4]["status"] = "completed"

        # Pilier 5 : Next Step (démo, pilot, essai, suite)
        nextstep_keywords = ["démo", "essai", "tester", "pilot", "prochaine étape", "rendez-vous"]
        if any(kw in recent_messages for kw in nextstep_keywords):
            if self.pillar_progress[5]["status"] == "not_started":
                self.pillar_progress[5]["status"] = "in_progress"
            if "démo" in recent_messages or "rendez-vous" in recent_messages:
                self.pillar_progress[5]["status"] = "completed"

    def get_structured_context(self) -> str:
        """Retourne le contexte structuré formaté avec progression des piliers"""
        duration_info = f"{len(self.full_transcript)} échanges"

        pain_points_str = "Aucun identifié pour le moment"
        if self.pain_points:
            pain_points_str = "\n".join([f"  • {pp}" for pp in self.pain_points[-3:]])

        topics_str = ", ".join(self.topics_covered[-8:]) if self.topics_covered else "Aucun"

        phase_str = self.context_analyzer.get_phase_label(self.conversation_phase)

        # 🆕 Progression des piliers
        pillar_status_icons = {
            "not_started": "⚪",
            "in_progress": "🟡",
            "completed": "🟢"
        }

        pillars_str = "\n".join([
            f"{pillar_status_icons[p['status']]} Pilier {i} - {p['name']}"
            for i, p in self.pillar_progress.items()
        ])

        structured_context = f"""
═══════════════════════════════════════════════════════════════════════════
📊 CONTEXTE GLOBAL DE L'APPEL
═══════════════════════════════════════════════════════════════════════════
🔄 Phase actuelle : {phase_str}
⏱️  Durée : {duration_info}

🎯 PROGRESSION DES 5 PILIERS DE DISCOVERY :
{pillars_str}

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
    
    def add_insight(self, insight: str, title: str = None):
        """Ajoute un insight au cache avec extraction de concepts et timestamp"""
        current_time = datetime.now().timestamp()

        self.last_insights.append(insight)
        self.last_insight_time = current_time
        self.insight_timestamps.append(current_time)

        # Extraire le titre si non fourni
        if title:
            self.last_titles.append(title)
        else:
            # Extraire depuis l'insight (format: "titre - action")
            if " - " in insight:
                extracted_title = insight.split(" - ")[0].strip()
                self.last_titles.append(extracted_title)
            else:
                self.last_titles.append(insight[:50])  # Fallback: premiers 50 chars

        concepts = self.context_analyzer.extract_key_concepts(insight)
        self.recent_concepts.append(concepts)

        # Limiter l'historique
        if len(self.last_insights) > MAX_INSIGHTS_CACHE:
            self.last_insights = self.last_insights[-MAX_INSIGHTS_CACHE:]
            self.last_titles = self.last_titles[-MAX_INSIGHTS_CACHE:]
            self.recent_concepts = self.recent_concepts[-MAX_INSIGHTS_CACHE:]
            self.insight_timestamps = self.insight_timestamps[-MAX_INSIGHTS_CACHE:]

    async def is_duplicate_insight(self, new_insight: str, new_title: str = None, time_threshold_seconds: int = None) -> bool:
        """
        Vérifie si l'insight est un doublon avec VÉRIFICATION TITRE + VECTORISATION SÉMANTIQUE

        Utilise sentence-transformers pour une détection rapide et précise
        """
        # Extraire le titre si non fourni
        if not new_title:
            if " - " in new_insight:
                new_title = new_insight.split(" - ")[0].strip()
            else:
                new_title = new_insight[:50]

        # ✅ VÉRIFICATION 1: Bloquer si même titre répété consécutivement
        is_title_dup, title_reason = self.duplicate_detector.check_duplicate_title(
            new_title,
            self.last_titles,
            max_consecutive=1  # ✅ Bloquer dès le 2ème insight avec même titre (autoriser 1 seul)
        )

        if is_title_dup:
            logger.warning(f"[ANTI-DOUBLON] ❌ TITRE RÉPÉTITIF: {title_reason}")
            return True

        # ✅ VÉRIFICATION 2: Similarité sémantique
        is_dup, analysis = self.duplicate_detector.check_duplicate_semantic(
            new_insight,
            self.last_insights,
            self.insight_timestamps,
            time_threshold_seconds
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
