"""
Service de génération de résumés d'appels
"""
import logging
import asyncio
import json
from typing import Dict, Any
import openai

from config.settings import FINE_TUNED_MODEL, SUMMARY_TEMPERATURE

logger = logging.getLogger(__name__)


class SummaryService:
    """Service de génération de résumés d'appels"""
    
    def __init__(self):
        self.model = FINE_TUNED_MODEL
        self.temperature = SUMMARY_TEMPERATURE
    
    async def generate_client_focused_summary(self, full_transcript: str) -> Dict[str, Any]:
        """
        Génère un résumé centré sur le CLIENT
        
        Args:
            full_transcript: Transcript complet de la conversation
        
        Returns:
            Dict avec summary structuré
        """
        prompt = f"""Tu es un analyste commercial expert qui évalue des appels de vente de manière objective et factuelle.

TRANSCRIPTION DE L'ÉCHANGE :
\"\"\"{full_transcript}\"\"\"

MISSION :
Analyse cet appel et fournis une évaluation structurée :

1) **UNE PHRASE UNIQUE** factuelle résumant l'échange du point de vue du client

2) **UN RÉSUMÉ DÉTAILLÉ** (5-7 lignes) centré sur le CLIENT : ses besoins exprimés, ses objections, ses attentes, son niveau d'intérêt, ses contraintes, et les informations clés qu'il a partagées.

FORMAT DE RÉPONSE (JSON strict, sans markdown) :
{{
  "summary": {{
    "main": "Phrase unique factuelle résumant la situation du client",
    "details": "Résumé factuel détaillé centré sur le client"
  }},
  "next_actions": {{
    "priority": "high" | "medium" | "low",
    "actions": [
      {{
        "action": "Action concrète",
        "deadline": "Délai recommandé",
        "reason": "Pourquoi cette action"
      }}
    ],
    "follow_up": "Stratégie de relance"
  }},
  "key_points": {{
    "strengths": ["Point fort 1", "Point fort 2", "Point fort 3"],
    "weaknesses": ["Point faible 1", "Point faible 2"],
    "improvements": ["Axe d'amélioration 1", "Axe d'amélioration 2"],
    "score": {{
      "value": 15,
      "comment": "Justification de la note sur 20"
    }}
  }}
}}

Réponds uniquement avec le JSON"""
        
        try:
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=900,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            raw_summary = response.choices[0].message.content
            logger.info("[RÉSUMÉ] Génération réussie")
            
            summary_json = self._safe_json_parse(raw_summary)
            return summary_json
            
        except Exception as e:
            logger.exception("Erreur appel OpenAI pour summary")
            return self._get_fallback_summary()
    
    async def generate_commercial_focused_summary(self, conversation_text: str) -> Dict[str, Any]:
        """
        Génère un résumé centré sur le COMMERCIAL
        
        Args:
            conversation_text: Texte de la conversation
        
        Returns:
            Dict avec évaluation du commercial
        """
        prompt = f"""Tu es un coach commercial expert. Analyse le dialogue suivant et évalue UNIQUEMENT la performance du commercial.

TRANSCRIPTION DE L'ÉCHANGE :
\"\"\"{conversation_text}\"\"\"

TÂCHES :
1. Fournis un résumé global de l'appel en 2-3 phrases.
2. Liste clairement les points forts (strengths) et points faibles (weaknesses) du commercial.
3. Donne des notes sur 10 pour chaque critère :
   - politeness
   - listening
   - persuasion
   - clarity
   - objection_handling
4. Donne une note globale "overall" sur 10.

FORMAT DE RÉPONSE (JSON strict, sans markdown) :
{{
  "summary": "Résumé global de l'appel",
  "strengths": ["Point fort 1", "Point fort 2"],
  "weaknesses": ["Point faible 1", "Point faible 2"],
  "ratings": {{
    "politeness": 0,
    "listening": 0,
    "persuasion": 0,
    "clarity": 0,
    "objection_handling": 0,
    "overall": 0
  }}
}}

Réponds UNIQUEMENT avec le JSON."""
        
        try:
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.25
            )
            raw_summary = response.choices[0].message.content
            
            summary_json = self._safe_json_parse(raw_summary)
            return summary_json
            
        except Exception as e:
            logger.exception("Erreur appel OpenAI pour summary commercial")
            return self._get_fallback_commercial_summary()
    
    def _safe_json_parse(self, raw_text: str) -> Dict[str, Any]:
        """Parse JSON de manière sécurisée avec nettoyage"""
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            logger.warning("[RÉSUMÉ] JSON invalide, tentative de nettoyage...")
            cleaned = raw_text.strip().strip("`").replace("```json", "").replace("```", "")
            try:
                return json.loads(cleaned)
            except Exception:
                logger.error("[RÉSUMÉ] Impossible de parser le JSON")
                return None
    
    def _get_fallback_summary(self) -> Dict[str, Any]:
        """Résumé par défaut en cas d'erreur"""
        return {
            "summary": {"main": "Non disponible", "details": "Résumé non disponible"},
            "next_actions": {"priority": "medium", "actions": [], "follow_up": "Non disponible"},
            "key_points": {
                "strengths": [],
                "weaknesses": [],
                "improvements": [],
                "score": {"value": 0, "comment": "Non évalué"}
            }
        }
    
    def _get_fallback_commercial_summary(self) -> Dict[str, Any]:
        """Résumé commercial par défaut en cas d'erreur"""
        return {
            "summary": "",
            "strengths": [],
            "weaknesses": [],
            "ratings": {
                "politeness": 0,
                "listening": 0,
                "persuasion": 0,
                "clarity": 0,
                "objection_handling": 0,
                "overall": 0
            }
        }
