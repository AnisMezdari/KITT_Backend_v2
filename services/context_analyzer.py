"""
Service d'analyse de contexte de conversation
"""
from typing import List, Dict
import logging
import asyncio
import openai

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """Analyse le contexte de la conversation"""
    
    @staticmethod
    def extract_key_concepts(text: str) -> str:
        """Extrait les concepts clés commerciaux d'un insight"""

        concept_patterns = {
            "pricing": ["prix", "cher", "coût", "budget", "roi", "tarif", "investissement", "€", "eur", "retour sur investissement"],
            "objection": ["objection", "frein", "hésitation", "doute", "réticent", "sceptique", "inquiet", "préoccupé"],
            "closing": ["closing", "signature", "contrat", "deal", "achat", "conclure", "signer"],
            "discovery": ["discovery", "découverte", "question", "besoin", "comprendre", "explorer"],
            "pain_point": ["pain point", "problème", "douleur", "difficulté", "challenge", "souffre"],
            "timing": ["timing", "moment", "urgence", "délai", "maintenant", "quand", "rapidement"],
            "decision": ["décision", "décideur", "validation", "approuver", "choisir"],
            "competitor": ["concurrent", "compétiteur", "alternative", "gong", "chorus", "salesloft"],
            "technical": ["technique", "intégration", "api", "crm", "salesforce", "hubspot", "setup", "webhook", "zapier"],
            "adoption": ["adoption", "changement", "résistance", "équipe", "onboarding", "formation"],
            "interest": ["intérêt", "intéressant", "curieux", "engagement", "attentif", "écoute"],
            "budget": ["budget", "financement", "allocation", "enveloppe", "ressources"],
            "team": ["équipe", "commerciaux", "vendeurs", "sales", "collaborateurs"],
            "demo": ["démo", "démonstration", "présentation", "montrer", "voir"],
            "timeline": ["timeline", "planning", "échéance", "roadmap", "calendrier"],
            "value": ["valeur", "bénéfice", "avantage", "gain", "impact"],
            "trust": ["confiance", "crédibilité", "preuve", "référence", "témoignage"],
            "qualification": ["qualification", "fit", "profil", "cible", "adapté"],
            "next_steps": ["prochaine étape", "next step", "suite", "après", "ensuite"],
            "engagement": ["engagement", "implication", "participation", "actif"],
            "tone": ["ton", "attitude", "comportement", "défensif", "agressif", "chaleureux"],
            # 🆕 NOUVEAUX CONCEPTS AJOUTÉS
            "roi": ["roi", "retour", "rentabilité", "bénéfice financier", "rentable"],
            "scalability": ["scalabilité", "croissance", "scale", "expansion", "grandir"],
            "support": ["support", "accompagnement", "aide", "assistance", "service client", "sav"],
            "security": ["sécurité", "rgpd", "compliance", "confidentialité", "protection", "données"],
            "performance": ["performance", "rapidité", "efficacité", "productivité", "vitesse"],
            "reporting": ["reporting", "rapport", "analytique", "dashboard", "métriques", "kpi"]
        }
        
        text_lower = text.lower()
        detected_concepts = []
        
        for concept, patterns in concept_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                detected_concepts.append(concept)
        
        if not detected_concepts:
            return "général"
        
        return ", ".join(detected_concepts)
    
    async def detect_conversation_phase_ai(self, messages: List[Dict]) -> str:
        """
        🆕 Détecte la phase actuelle avec IA (GPT-4o-mini)
        Plus précis que le pattern matching simple
        """
        if not messages:
            return "introduction"

        # Prendre les 8 derniers messages pour plus de contexte
        recent_messages = messages[-8:]
        recent_text = "\n".join([
            f"{'COMMERCIAL' if msg.get('role') == 'user' else 'CLIENT'}: {msg.get('content', '')}"
            for msg in recent_messages
        ])

        prompt = f"""Analyse cette conversation commerciale et détermine la phase actuelle de vente.

DERNIERS ÉCHANGES:
{recent_text}

Réponds UNIQUEMENT avec l'une de ces phases (un seul mot):
- introduction (prise de contact initial, présentations)
- discovery (découverte des besoins, questions sur les problèmes)
- presentation (présentation de la solution KITT, fonctionnalités)
- negotiation (discussion sur le prix, budget, ROI)
- closing (demande de démo, prochaines étapes, signature)

Phase:"""

        try:
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.0
            )

            phase = response.choices[0].message.content.strip().lower()

            # Validation
            valid_phases = ["introduction", "discovery", "presentation", "negotiation", "closing"]
            if phase in valid_phases:
                logger.info(f"[PHASE DETECTION IA] Phase détectée: {phase}")
                return phase
            else:
                logger.warning(f"[PHASE DETECTION IA] Phase invalide reçue: {phase}, fallback sur discovery")
                return "discovery"

        except Exception as e:
            logger.error(f"[PHASE DETECTION IA] Erreur: {e}, fallback sur méthode pattern matching")
            return self.detect_conversation_phase_fallback(messages)

    @staticmethod
    def detect_conversation_phase_fallback(messages: List[Dict]) -> str:
        """
        Méthode de fallback (pattern matching simple)
        Utilisée si l'IA échoue
        """
        if not messages:
            return "introduction"

        recent_text = " ".join([
            msg.get('content', '') for msg in messages[-5:]
        ]).lower()

        phase_patterns = {
            "introduction": ["bonjour", "présente", "appelle", "enchanté", "contact", "merci de prendre"],
            "discovery": ["besoin", "problème", "actuellement", "comment", "pourquoi", "qu'est-ce que",
                         "aujourd'hui", "équipe", "process", "difficultés"],
            "presentation": ["kitt", "solution", "fonctionne", "permet", "fonctionnalité", "propose",
                            "temps réel", "coaching", "analyse"],
            "negotiation": ["prix", "coût", "budget", "combien", "tarif", "investissement", "roi",
                           "offre", "package"],
            "closing": ["démo", "essai", "rendez-vous", "prochaine étape", "next step", "calendrier",
                       "disponible", "quand", "envoyer", "contrat"]
        }

        phase_scores = {}
        for phase, patterns in phase_patterns.items():
            score = sum(1 for pattern in patterns if pattern in recent_text)
            phase_scores[phase] = score

        if not phase_scores or max(phase_scores.values()) == 0:
            return "discovery"

        detected_phase = max(phase_scores.items(), key=lambda x: x[1])[0]
        return detected_phase
    
    @staticmethod
    def extract_pain_points(messages: List[Dict]) -> List[str]:
        """
        🆕 Extrait les pain points (CLIENT + COMMERCIAL)
        Amélioration: Capte aussi les pain points mentionnés par le commercial
        """
        pain_points = []

        pain_keywords = [
            "problème", "difficulté", "challenge", "galère", "compliqué",
            "perte de temps", "inefficace", "frustrant", "manque", "besoin",
            # 🆕 Patterns pour détection par commercial
            "vous avez dit", "vous mentionnez", "vous rencontrez", "vous faites face",
            "votre problème", "votre difficulté", "vous souffrez"
        ]

        for msg in messages:
            # ✅ Accepter CLIENT (assistant) ET COMMERCIAL (user)
            content = msg.get('content', '').lower()
            sentences = content.split('.')

            for sentence in sentences:
                if any(keyword in sentence for keyword in pain_keywords):
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 20 and clean_sentence not in pain_points:
                        pain_points.append(clean_sentence[:150])

        return pain_points[-5:]
    
    @staticmethod
    def get_phase_label(phase: str) -> str:
        """Retourne le label français d'une phase"""
        phase_labels = {
            "introduction": "Introduction / Prise de contact",
            "discovery": "Découverte des besoins",
            "presentation": "Présentation de la solution",
            "negotiation": "Négociation / Discussion budget",
            "closing": "Closing / Prochaines étapes"
        }
        return phase_labels.get(phase, phase)
