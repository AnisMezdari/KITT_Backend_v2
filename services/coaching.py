"""
Service de génération d'insights et coaching en temps réel
"""
import logging
import asyncio
from typing import Optional, Dict
import openai

from config.settings import (
    FINE_TUNED_MODEL,
    COACHING_TEMPERATURE,
    PRODUCT_NAME,
    PRODUCT_DESCRIPTION,
    SALES_FRAMEWORK,
    COMPANY_INDUSTRY,
)

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
                max_tokens=80,  # ✅ OPTIMISÉ: 80 tokens pour format dataset complet
                temperature=self.temperature
            )
            
            raw_advice = response.choices[0].message.content.strip()
            logger.info(f"[IA] Réponse brute: {raw_advice}")
            
            return raw_advice
            
        except Exception as e:
            logger.error(f"[IA] Erreur lors de l'appel GPT: {e}")
            return None
    
    def build_coaching_prompt(self, context: str, manager) -> str:
        """
        ⚡ PROMPT SYSTÈME OPTIMISÉ : 5 Piliers + Analyse Incrémentale (30 dernières secondes)

        Architecture Performance:
        - Contexte réduit: 30 dernières secondes max (au lieu de tout l'historique)
        - Prompt structuré: 5 piliers explicites pour guidance IA
        - Format court forcé: Max 15 mots pour lecture instantanée
        """

        # ═══════════════════════════════════════════════════════════════════════════
        # 1. ANALYSE INCRÉMENTALE : 30 DERNIÈRES SECONDES UNIQUEMENT
        # ═══════════════════════════════════════════════════════════════════════════
        # Approximation: 1 message ≈ 5-10 secondes de conversation
        # → Prendre max 5 derniers messages (≈ 30 secondes de contexte)
        recent_messages = manager.messages[-5:] if len(manager.messages) >= 5 else manager.messages

        phase_labels = {
            "introduction": "Intro",
            "discovery": "Discovery",
            "presentation": "Pitch",
            "negotiation": "Négo",
            "closing": "Closing"
        }
        phase = phase_labels.get(manager.conversation_phase, manager.conversation_phase)

        # ✅ FORMAT EXACT DU DATASET: emoji + "Pilier X - Nom"
        pillar_icons = {
            "not_started": "⚪",
            "in_progress": "🟡",
            "completed": "🟢"
        }

        # Mapping des noms pour matcher EXACTEMENT le dataset
        pillar_names_dataset = {
            1: "Comprendre le contexte",
            2: "Identifier le problème",  # Sans "vrai"
            3: "Mesurer l'impact",
            4: "Valider le décisionnel",
            5: "Next Step"  # Sans "intelligent"
        }

        pillar_summary = "\n".join([
            f"{pillar_icons[p['status']]} Pilier {i} - {pillar_names_dataset[i]}"
            for i, p in manager.pillar_progress.items()
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # 2. FORMATAGE DES MESSAGES (5 derniers = ~30 secondes)
        # ═══════════════════════════════════════════════════════════════════════════
        # Utiliser recent_messages défini plus haut (5 derniers messages)
        formatted_messages = "\n".join([
            f"{'CLIENT' if msg['role'] == 'assistant' else 'COMMERCIAL'}: {msg['content']}"
            for msg in recent_messages
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # 3. PROMPT SYSTÈME OPTIMISÉ : Les 5 Piliers explicites
        # ═══════════════════════════════════════════════════════════════════════════
        prompt = f"""**MÉTHODOLOGIE - 5 PILIERS DE DISCOVERY B2B** :
1️⃣ Comprendre le contexte : Questions sur situation actuelle AVANT de pitcher
2️⃣ Identifier le problème : Creuser les pains profonds et quantifiables
3️⃣ Mesurer l'impact : Quantifier en temps, argent, risques
4️⃣ Valider le décisionnel : Qui décide, budget, timeline (MEDDIC)
5️⃣ Next Step : Proposer suite concrète (démo, pilot)

**DERNIERS ÉCHANGES (30 dernières secondes)** :
{formatted_messages}

**PROGRESSION DES PILIERS** :
{pillar_summary}

Que recommandes-tu ?

Réponds en 1 ligne courte (max 15 mots) au format : [titre simple] - [action simple]"""

        return prompt
    
    def parse_insight_response(self, raw_response: str) -> Optional[Dict]:
        """
        Parse la réponse du modèle au format SIMPLE: titre - action

        ✅ FORMAT ATTENDU: [titre simple] - [action simple]
        ✅ ACCEPTE avec ou sans emojis, avec ou sans préfixes
        """

        response = raw_response.strip()

        # Vérifier si vide
        if not response or len(response) < 5:
            logger.warning("[PARSING] ❌ Réponse vide ou trop courte")
            return None

        # Nettoyer les emojis et préfixes communs (optionnels)
        emoji_to_type = {
            "🟢": "progression",
            "🔵": "opportunity",
            "🔴": "alert"
        }

        detected_type = "progression"  # Type par défaut

        # Détecter l'emoji si présent (optionnel)
        for emoji, type_name in emoji_to_type.items():
            if emoji in response:
                detected_type = type_name
                response = response.replace(emoji, "").strip()
                break

        # Retirer préfixes communs si présents (optionnel)
        prefixes = ["Signal de progression", "Signal d'opportunité", "Signal d'alerte",
                   "Progression", "Opportunité", "Alerte"]
        for prefix in prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
                # Retirer : ou | au début
                if response.startswith(":") or response.startswith("|"):
                    response = response[1:].strip()
                break

        # PARSER "Titre - Action" (seule contrainte obligatoire)
        if " - " not in response:
            logger.warning(f"[PARSING] ❌ Séparateur ' - ' manquant: {raw_response}")
            return None

        parts = response.split(" - ", 1)
        title = parts[0].strip()
        action = parts[1].strip()

        # Validation minimale (juste éviter les cas absurdes)
        if len(title) < 3:
            title = "Signal détecté"
        if len(action) < 3:
            action = "Analyser la situation"

        # Limiter les longueurs max
        if len(title) > 100:
            title = title[:97] + "..."
        if len(action) > 150:
            action = action[:147] + "..."

        # CONSTRUIRE L'INSIGHT
        insight = {
            "title": title,
            "type": detected_type,
            "details": {
                "description": action
            }
        }

        logger.info(f"[PARSING] ✅ Format simple: {title} - {action}")

        return insight
