"""
Service de détection intelligente de doublons avec IA + vectorisation sémantique
"""
import logging
import asyncio
import json
from typing import List, Dict, Optional
from datetime import datetime
import openai
import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import (
    OPENAI_MODEL,
    DUPLICATE_CHECK_TEMPERATURE,
    TIME_THRESHOLD_DUPLICATE
)

logger = logging.getLogger(__name__)

# Modèle d'embeddings (chargé une seule fois au démarrage)
_embedding_model = None

def get_embedding_model():
    """Lazy loading du modèle d'embeddings"""
    global _embedding_model
    if _embedding_model is None:
        logger.info("🔄 Chargement du modèle d'embeddings (sentence-transformers)...")
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        logger.info("✅ Modèle d'embeddings chargé avec succès")
    return _embedding_model


class DuplicateDetector:
    """Détecte les insights en doublon avec IA et fenêtre temporelle"""

    def __init__(self):
        self.model = OPENAI_MODEL
        self.temperature = DUPLICATE_CHECK_TEMPERATURE
        self.time_threshold = TIME_THRESHOLD_DUPLICATE
        self.semantic_threshold = 0.85  # Seuil de similarité cosine pour doublons (0-1)

    def _compute_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité sémantique entre deux textes avec embeddings

        Args:
            text1: Premier texte
            text2: Deuxième texte

        Returns:
            Score de similarité cosine (0-1)
        """
        try:
            model = get_embedding_model()

            # Générer les embeddings (vecteurs) pour les deux textes
            embeddings = model.encode([text1, text2])

            # Calculer la similarité cosine
            vec1 = embeddings[0]
            vec2 = embeddings[1]

            # Formule de similarité cosine : (A · B) / (||A|| × ||B||)
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            similarity = dot_product / (norm1 * norm2)

            # Convertir de [-1, 1] à [0, 1]
            similarity = (similarity + 1) / 2

            return float(similarity)

        except Exception as e:
            logger.error(f"❌ Erreur lors du calcul de similarité sémantique: {e}")
            return 0.0

    def check_duplicate_semantic(
        self,
        new_insight: str,
        insights_history: List[str],
        timestamps_history: List[float],
        time_threshold_seconds: int = None
    ) -> tuple[bool, Dict]:
        """
        Vérifie si un insight est un doublon avec VECTORISATION SÉMANTIQUE

        NOUVELLE MÉTHODE : Plus rapide et plus précise que l'appel IA complet

        Args:
            new_insight: Nouvel insight à vérifier
            insights_history: Liste des insights précédents
            timestamps_history: Timestamps correspondants
            time_threshold_seconds: Seuil temporel (défaut: config)

        Returns:
            Tuple (is_duplicate: bool, analysis: dict)
        """
        if not insights_history:
            return False, {"reason": "Aucun historique", "method": "semantic"}

        threshold = time_threshold_seconds or self.time_threshold
        current_time = datetime.now().timestamp()

        logger.info(f"\n{'🔬'*40}")
        logger.info(f"[ANTI-DOUBLON SÉMANTIQUE] 🧬 ANALYSE PAR VECTORISATION")
        logger.info(f"{'🔬'*40}")
        logger.info(f"Nouvel insight: {new_insight[:80]}...")
        logger.info(f"Historique à comparer: {len(insights_history[-5:])} insights")

        max_similarity = 0.0
        most_similar_insight = None
        most_similar_index = None
        is_recent = False

        # Comparer avec les 5 derniers insights
        for i, old_insight in enumerate(insights_history[-5:]):
            actual_index = len(insights_history) - 5 + i

            if actual_index >= 0 and actual_index < len(timestamps_history):
                timestamp = timestamps_history[actual_index]
            else:
                timestamp = current_time - 100

            time_elapsed = current_time - timestamp
            is_old = time_elapsed > threshold

            # Calcul de la similarité sémantique
            similarity = self._compute_semantic_similarity(new_insight, old_insight)

            minutes_ago = int(time_elapsed / 60)
            seconds_ago = int(time_elapsed % 60)
            time_display = f"{minutes_ago}min {seconds_ago}s" if minutes_ago > 0 else f"{seconds_ago}s"
            marker = "⏰ [ANCIEN]" if is_old else "🔥 [RÉCENT]"

            logger.info(f"\n  #{i+1} {marker}")
            logger.info(f"    Insight: {old_insight[:60]}...")
            logger.info(f"    Ancienneté: {time_display}")
            logger.info(f"    Similarité sémantique: {similarity:.3f}")

            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_insight = old_insight
                most_similar_index = i + 1
                is_recent = not is_old

        # Décision finale
        is_duplicate = False
        reason = ""

        if max_similarity >= self.semantic_threshold:
            if is_recent:
                is_duplicate = True
                reason = f"Doublon sémantique RÉCENT (similarité: {max_similarity:.3f} ≥ {self.semantic_threshold})"
            else:
                is_duplicate = False
                reason = f"Similaire mais ANCIEN (similarité: {max_similarity:.3f}, mais > {threshold}s)"
        else:
            reason = f"Suffisamment différent (similarité max: {max_similarity:.3f} < {self.semantic_threshold})"

        logger.info(f"\n{'─'*80}")
        logger.info(f"{'❌ DOUBLON DÉTECTÉ' if is_duplicate else '✅ INSIGHT UNIQUE'}")
        logger.info(f"Raison: {reason}")
        logger.info(f"Insight le plus similaire: #{most_similar_index}")
        logger.info(f"Score max: {max_similarity:.3f}")
        logger.info(f"{'🔬'*40}\n")

        analysis = {
            "is_duplicate": is_duplicate,
            "reason": reason,
            "similarity_score": max_similarity,
            "most_similar_index": most_similar_index,
            "method": "semantic_embeddings",
            "threshold_used": self.semantic_threshold
        }

        return is_duplicate, analysis
    
    async def check_duplicate(
        self,
        new_insight: str,
        insights_history: List[str],
        timestamps_history: List[float],
        time_threshold_seconds: int = None
    ) -> tuple[bool, Dict]:
        """
        Vérifie si un insight est un doublon avec l'IA
        
        Args:
            new_insight: Nouvel insight à vérifier
            insights_history: Liste des insights précédents
            timestamps_history: Timestamps correspondants
            time_threshold_seconds: Seuil temporel (défaut: config)
        
        Returns:
            Tuple (is_duplicate: bool, analysis: dict)
        """
        if not insights_history:
            return False, {"reason": "Aucun historique"}
        
        threshold = time_threshold_seconds or self.time_threshold
        current_time = datetime.now().timestamp()
        
        # Préparer l'historique avec ancienneté
        insights_with_time = []
        for i, insight in enumerate(insights_history[-5:]):
            actual_index = len(insights_history) - 5 + i
            
            if actual_index >= 0 and actual_index < len(timestamps_history):
                timestamp = timestamps_history[actual_index]
            else:
                timestamp = current_time - 100  # Fallback
            
            time_elapsed = current_time - timestamp
            minutes_ago = int(time_elapsed / 60)
            seconds_ago = int(time_elapsed % 60)
            
            time_display = f"{minutes_ago}min {seconds_ago}s" if minutes_ago > 0 else f"{seconds_ago}s"
            
            insights_with_time.append({
                "insight": insight,
                "time_ago": time_display,
                "seconds_elapsed": time_elapsed,
                "can_ignore_if_similar": time_elapsed > threshold
            })
        
        # Construire l'historique formaté
        insights_history_str = ""
        for i, item in enumerate(insights_with_time, 1):
            marker = " ⏰ [ANCIEN - peut ignorer si similaire]" if item["can_ignore_if_similar"] else " 🔥 [RÉCENT]"
            insights_history_str += f"{i}. {item['insight']} (il y a {item['time_ago']}){marker}\n"
        
        # Construire le prompt
        prompt = self._build_prompt(new_insight, insights_history_str, threshold)
        
        try:
            # Appel à l'IA
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            
            is_dup = result.get("is_duplicate", False)
            reason = result.get("reason", "Raison non fournie")
            similarity = result.get("similarity_score", 0.0)
            time_factor = result.get("time_factor", "unknown")
            
            analysis = {
                "is_duplicate": is_dup,
                "reason": reason,
                "similarity_score": similarity,
                "time_factor": time_factor
            }
            
            # Logs détaillés
            logger.info(f"\n{'─'*80}")
            logger.info(f"[ANTI-DOUBLON IA] 🤖 RÉSULTAT DE L'ANALYSE")
            logger.info(f"{'─'*80}")
            logger.info(f"Decision: {'❌ DOUBLON' if is_dup else '✅ UNIQUE'}")
            logger.info(f"Raison: {reason}")
            logger.info(f"Score similarité: {similarity:.2f} / 1.0")
            logger.info(f"Facteur temporel: {time_factor}")
            logger.info(f"{'─'*80}\n")
            
            return is_dup, analysis
            
        except Exception as e:
            logger.error(f"\n{'='*80}")
            logger.error(f"[ANTI-DOUBLON IA] ❌ ERREUR LORS DE L'ANALYSE")
            logger.error(f"{'='*80}")
            logger.error(f"Erreur: {str(e)}")
            logger.error(f"Type: {type(e).__name__}")
            logger.error(f"{'='*80}\n")
            
            # Fallback
            logger.info("[ANTI-DOUBLON IA] 🔄 Fallback sur méthode textuelle simple")
            return self._fallback_check(new_insight, insights_history), {"reason": "Fallback utilisé"}
    
    def _build_prompt(self, new_insight: str, insights_history: str, threshold: int) -> str:
        """Construit le prompt pour l'IA"""
        return f"""Tu es un expert en analyse de redondance d'insights commerciaux avec conscience temporelle.

HISTORIQUE DES INSIGHTS RÉCENTS (avec ancienneté) :
{insights_history}

NOUVEL INSIGHT À VÉRIFIER :
"{new_insight}"

⏰ RÈGLE TEMPORELLE IMPORTANTE :
Les insights marqués "⏰ [ANCIEN]" (plus de {threshold} secondes) peuvent être considérés comme NON-DOUBLONS même s'ils sont similaires, car :
- La conversation a évolué depuis
- Le contexte a changé
- C'est un rappel utile pour le commercial

Les insights marqués "🔥 [RÉCENT]" doivent être comparés strictement.

CRITÈRES DE DOUBLON (pour insights RÉCENTS uniquement) :
- Même concept commercial traité
- Même action recommandée
- Information déjà donnée sous une formulation différente
- Même contexte/situation détectée

CRITÈRES DE NON-DOUBLON :
- L'insight précédent similaire est ANCIEN (⏰)
- Apporte une nuance nouvelle ou un angle différent
- Traite d'un aspect complémentaire du même sujet
- Basé sur une évolution récente de la conversation
- Action différente même si le sujet est proche

Réponds UNIQUEMENT avec un JSON dans ce format exact :
{{
  "is_duplicate": true ou false,
  "reason": "Explication courte (1 phrase) de ta décision incluant l'aspect temporel si pertinent",
  "similarity_score": 0.0 à 1.0,
  "time_factor": "recent" ou "old" (si un insight similaire existe)
}}

IMPORTANT : 
- Privilégie "is_duplicate": false si l'insight similaire le plus proche est marqué ⏰ [ANCIEN]
- Sois strict uniquement sur les insights 🔥 [RÉCENT]"""
    
    def _fallback_check(self, new_insight: str, insights_history: List[str]) -> bool:
        """Méthode de fallback simple basée sur similarité textuelle"""
        logger.info(f"\n{'─'*80}")
        logger.info(f"[FALLBACK] 🔄 ANALYSE TEXTUELLE SIMPLE")
        logger.info(f"{'─'*80}")
        
        # Similarité simple (peut être améliorée)
        new_words = set(new_insight.lower().split())
        
        for idx, old_insight in enumerate(insights_history[-3:]):
            old_words = set(old_insight.lower().split())
            
            intersection = new_words.intersection(old_words)
            union = new_words.union(old_words)
            
            similarity = len(intersection) / len(union) if union else 0
            
            logger.info(f"\nComparaison #{idx+1}:")
            logger.info(f"  Insight ancien: {old_insight[:60]}...")
            logger.info(f"  Similarité: {similarity:.2f}")
            
            if similarity > 0.7:
                logger.info(f"  ❌ DOUBLON: Similarité trop élevée ({similarity:.2f} > 0.7)")
                logger.info(f"{'─'*80}\n")
                return True
        
        logger.info(f"\n✅ Aucun doublon détecté avec la méthode fallback")
        logger.info(f"{'─'*80}\n")
        return False
