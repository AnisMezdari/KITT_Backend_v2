"""
Service de pré-filtrage de pertinence pour insights
Détermine si un insight devrait être généré AVANT d'appeler l'IA
"""
import logging
from typing import List, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class RelevanceFilter:
    """
    Filtre de pertinence pour optimiser la génération d'insights

    Objectif : Ne générer un insight que quand il y a vraiment quelque chose d'intéressant
    """

    def __init__(self):
        # Mots-clés de "moments clés" (haute priorité)
        self.key_moments = {
            "pain_point": ["problème", "difficulté", "galère", "compliqué", "frustrant", "perd", "manque"],
            "objection": ["cher", "trop", "déjà", "pas besoin", "pas sûr", "réfléchir", "voir"],
            "buy_signal": ["intéressant", "comment", "quand", "combien", "essayer", "tester", "démo"],
            "decision": ["décide", "budget", "validation", "équipe", "décision", "timing"],
            "impact": ["€", "euros", "heures", "jours", "coûte", "économie", "gagner"],
        }

        # Patterns de "bruit" (faible priorité)
        self.noise_patterns = [
            "bonjour", "merci", "d'accord", "ok", "oui", "non", "hum", "euh",
            "voilà", "donc", "alors", "bon", "bien"
        ]

    def calculate_relevance_score(
        self,
        messages: List[Dict],
        pillar_progress: Dict,
        last_insight_time: float,
        conversation_phase: str
    ) -> Tuple[int, Dict]:
        """
        Calcule un score de pertinence (0-100) pour déterminer si un insight devrait être généré

        Returns:
            (score, analysis_details)
        """
        score = 0
        analysis = {
            "reasons": [],
            "triggers": [],
            "should_generate": False
        }

        if not messages:
            return 0, analysis

        # Analyser les 3 derniers messages
        recent_text = " ".join([m['content'].lower() for m in messages[-3:]]).strip()

        if not recent_text or len(recent_text) < 10:
            analysis["reasons"].append("Texte trop court ou vide")
            return 0, analysis

        # 1. DÉTECTION DE MOMENTS CLÉS (+40 points)
        key_moment_detected = False
        for moment_type, keywords in self.key_moments.items():
            if any(kw in recent_text for kw in keywords):
                score += 40
                key_moment_detected = True
                analysis["triggers"].append(f"Moment clé: {moment_type}")
                logger.info(f"[RELEVANCE] 🎯 Moment clé détecté: {moment_type}")
                break

        # 2. PROGRESSION DES PILIERS (+30 points si pilier non commencé abordé)
        uncovered_pillars = [
            p_id for p_id, p_data in pillar_progress.items()
            if p_data["status"] == "not_started"
        ]

        if uncovered_pillars:
            # Vérifier si un pilier non couvert est abordé
            pillar_keywords = {
                1: ["utilisez", "processus", "actuellement", "comment"],
                2: ["problème", "difficulté", "perd", "manque"],
                3: ["combien", "coûte", "impact", "€", "heures"],
                4: ["décide", "budget", "timing", "validation"],
                5: ["démo", "essai", "tester", "suite", "rendez-vous"]
            }

            for p_id in uncovered_pillars:
                if any(kw in recent_text for kw in pillar_keywords.get(p_id, [])):
                    score += 30
                    analysis["triggers"].append(f"Pilier {p_id} (non couvert) abordé")
                    logger.info(f"[RELEVANCE] 📊 Pilier {p_id} non couvert abordé")
                    break

        # 3. LONGUEUR ET RICHESSE DU CONTENU (+20 points)
        word_count = len(recent_text.split())
        if word_count > 30:  # Échange substantiel
            score += 20
            analysis["triggers"].append(f"Échange substantiel ({word_count} mots)")
        elif word_count > 15:
            score += 10
            analysis["triggers"].append(f"Échange moyen ({word_count} mots)")

        # 4. NOUVEAUTÉ PAR RAPPORT AU DERNIER INSIGHT (+15 points)
        time_since_last = datetime.now().timestamp() - last_insight_time if last_insight_time > 0 else 999
        if time_since_last > 60:  # Plus d'1 minute
            score += 15
            analysis["triggers"].append(f"Temps écoulé: {int(time_since_last)}s")
        elif time_since_last > 30:
            score += 8

        # 5. PHASE DE CONVERSATION (+10 points pour phases critiques)
        if conversation_phase in ["discovery", "negotiation", "closing"]:
            score += 10
            analysis["triggers"].append(f"Phase critique: {conversation_phase}")

        # 6. PÉNALITÉS POUR BRUIT (-20 points)
        noise_count = sum(1 for pattern in self.noise_patterns if pattern in recent_text)
        if noise_count > 3:
            score -= 20
            analysis["reasons"].append(f"Trop de bruit ({noise_count} patterns)")

        # 7. QUESTIONS DU COMMERCIAL (+15 points - bon signe de discovery)
        question_marks = recent_text.count("?")
        if question_marks >= 2:
            score += 15
            analysis["triggers"].append(f"{question_marks} questions posées")

        # Limiter le score à 100
        score = min(100, max(0, score))

        # Décision finale
        analysis["should_generate"] = score >= 60 or key_moment_detected
        analysis["reasons"].append(f"Score final: {score}/100")

        logger.info(f"[RELEVANCE] 📊 Score de pertinence: {score}/100")
        logger.info(f"[RELEVANCE] 🎯 Triggers: {', '.join(analysis['triggers']) if analysis['triggers'] else 'Aucun'}")
        logger.info(f"[RELEVANCE] ✅ Génération recommandée: {'OUI' if analysis['should_generate'] else 'NON'}")

        return score, analysis

    def should_generate_insight(
        self,
        messages: List[Dict],
        pillar_progress: Dict,
        last_insight_time: float,
        conversation_phase: str,
        min_score: int = 60
    ) -> Tuple[bool, int, Dict]:
        """
        Détermine si un insight devrait être généré

        Returns:
            (should_generate, score, analysis)
        """
        score, analysis = self.calculate_relevance_score(
            messages,
            pillar_progress,
            last_insight_time,
            conversation_phase
        )

        should_generate = score >= min_score

        return should_generate, score, analysis
