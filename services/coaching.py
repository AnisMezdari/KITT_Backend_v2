"""
Service de génération d'insights et coaching en temps réel
"""
import logging
import asyncio
import json
from typing import Optional, Dict, Any
import openai

from config.settings import FINE_TUNED_MODEL, COACHING_TEMPERATURE

logger = logging.getLogger(__name__)


class CoachingService:
    """Service de génération d'insights de coaching"""
    
    def __init__(self):
        self.model = FINE_TUNED_MODEL
        self.temperature = COACHING_TEMPERATURE
    
    async def generate_insight(self, prompt: str) -> Optional[str]:
        """
        Génère un insight de coaching via le modèle fine-tuné
        
        Args:
            prompt: Prompt complet avec contexte
        
        Returns:
            Texte brut de l'insight ou None
        """
        try:
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
                temperature=self.temperature
            )
            
            raw_advice = response.choices[0].message.content.strip()
            logger.info(f"[IA] Réponse brute: {raw_advice}")
            
            return raw_advice
            
        except Exception as e:
            logger.error(f"[IA] Erreur lors de l'appel GPT: {e}")
            return None
    
    def build_coaching_prompt(self, context: str, manager) -> str:
        """Construit le prompt pour le modèle fine-tuné"""
        
        structured_context = manager.get_structured_context()
        
        insights_history = ""
        if manager.last_insights:
            insights_history = "\n📝 DERNIERS INSIGHTS DONNÉS (NE PAS RÉPÉTER) :\n"
            for i, insight in enumerate(manager.last_insights[-3:], 1):
                concepts_idx = -(3-i+1) if (3-i+1) <= len(manager.recent_concepts) else 0
                concepts = manager.recent_concepts[concepts_idx] if concepts_idx < 0 else "général"
                insights_history += f"{i}. {insight[:80]}...\n"
                insights_history += f"   📊 Concepts traités: {concepts}\n"
            
            insights_history += "\n⚠️ RÈGLE CRITIQUE ANTI-REDONDANCE :\n"
            insights_history += "- Si ton insight traite des MÊMES CONCEPTS que ci-dessus, réponds : \"\"\n"
            insights_history += "- Si ton insight apporte EXACTEMENT la même information, réponds : \"\"\n"
            insights_history += "- Privilégie la QUALITÉ sur la QUANTITÉ\n"
            insights_history += "- En cas de doute sur la pertinence, réponds : \"\"\n"
        
        prompt = f"""Tu es un coach commercial pour KITT. Donne des insights courts (1 phrase max) classés en 3 catégories : Alerte, Opportunité, Progression.

**CONTEXTE PRODUIT**
KITT est un copilote de vente en temps réel pour équipes commerciales B2B.

{structured_context}

**DERNIERS ÉCHANGES (contexte immédiat - BASE TOI UNIQUEMENT SUR CECI)** :
───────────────────────────────────────────────────────────────────────────
{context}
───────────────────────────────────────────────────────────────────────────

{insights_history}

**MISSION**
Analyse UNIQUEMENT les DERNIERS ÉCHANGES ci-dessus et fournis UN insight actionnable.

**FORMAT DE RÉPONSE STRICT**
[Emoji] Signal de [catégorie] : [Observation courte] - [Action recommandée]

Si aucun signal significatif détecté OU si l'insight serait redondant, réponds uniquement : ""

RÉPONDS UNIQUEMENT AVEC LE FORMAT CI-DESSUS, RIEN D'AUTRE."""

        return prompt
    
    def parse_insight_response(self, raw_response: str) -> Optional[Dict]:
        """Parse la réponse du modèle au format structuré"""
        
        emoji_to_type = {
            "🟢": "progression",
            "🔵": "opportunity",
            "🔴": "alert"
        }
        
        response = raw_response.strip()
        
        if not response or response == '""' or response == "":
            return None
        
        detected_type = None
        
        for emoji, type_name in emoji_to_type.items():
            if emoji in response:
                detected_type = type_name
                break
        
        if not detected_type:
            response_lower = response.lower()
            
            if any(word in response_lower for word in ["alerte", "attention", "danger", "risque", "erreur", "problème"]):
                detected_type = "alert"
            elif any(word in response_lower for word in ["opportunité", "occasion", "pain point", "signal", "moment clé"]):
                detected_type = "opportunity"
            else:
                detected_type = "progression"
        
        try:
            title = ""
            action = ""
            
            if " : " in response:
                parts = response.split(" : ", 1)
                content = parts[1]
                
                if " - " in content:
                    title_part, action_part = content.split(" - ", 1)
                    title = title_part.strip()
                    action = action_part.strip()
                else:
                    title = content.strip()
                    action = "Analyser et agir sur ce signal"
            else:
                clean_response = response
                for emoji in emoji_to_type.keys():
                    clean_response = clean_response.replace(emoji, "")
                
                clean_response = clean_response.strip()
                
                if len(clean_response) > 100:
                    title = clean_response[:80].strip()
                    action = clean_response[80:].strip()
                else:
                    title = clean_response
                    action = "Prendre en compte ce signal"
            
            if not title:
                title = "Signal détecté"
            
            if not action:
                action = "Analyser la situation"
            
            insight = {
                "title": title,
                "type": detected_type,
                "details": {
                    "description": action
                }
            }
            
            return insight
        
        except Exception as e:
            logger.error(f"[PARSING] Erreur: {e}")
            return {
                "title": "Signal détecté",
                "type": detected_type or "progression",
                "details": {
                    "description": response[:100] if len(response) > 100 else response
                }
            }
