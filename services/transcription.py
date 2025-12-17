"""
Service de transcription audio via Deepgram (ultra-rapide <300ms)
"""
import logging
import tempfile
import os
import asyncio
from datetime import datetime
import numpy as np
import soundfile as sf
from deepgram import DeepgramClient

from config.settings import (
    DEEPGRAM_API_KEY,
    AUDIO_SAMPLE_RATE,
    AUDIO_SUBTYPE,
    SILENCE_THRESHOLD_MIC,
    MIN_AMPLITUDE_MIC,
    MIN_AUDIO_LENGTH_MIC,
    SILENCE_THRESHOLD_BROWSER,
    MIN_AMPLITUDE_BROWSER,
    MIN_AUDIO_LENGTH_BROWSER,
    MIN_TRANSCRIPTION_LENGTH,
    UNWANTED_PATTERNS
)

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service gérant la transcription audio via Deepgram"""

    def __init__(self):
        # ⚡ Deepgram - Transcription ultra-rapide (<300ms vs 1.5-3s pour Whisper)
        if not DEEPGRAM_API_KEY or DEEPGRAM_API_KEY == "YOUR_DEEPGRAM_API_KEY_HERE":
            raise ValueError(
                "❌ DEEPGRAM_API_KEY manquante !\n"
                "Obtiens ta clé gratuite sur: https://console.deepgram.com/signup\n"
                "Puis ajoute-la dans le fichier .env"
            )

        # ✅ CORRECTION: api_key comme paramètre nommé (deepgram-sdk v5.x)
        self.deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.subtype = AUDIO_SUBTYPE

        logger.info("✅ TranscriptionService initialisé avec Deepgram")
    
    @staticmethod
    def detect_speech_start_time(audio_data: np.ndarray, role: str) -> float:
        """
        Détecte le moment où la parole commence dans l'audio

        Analyse l'audio échantillon par échantillon pour trouver le premier moment
        où l'amplitude dépasse le seuil de silence, indiquant le début de la parole.

        Args:
            audio_data: Array numpy de l'audio
            role: "CLIENT" ou "COMMERCIAL" pour utiliser les bons seuils

        Returns:
            float: Temps en secondes où la parole commence
                   float('inf') si aucune parole détectée
        """
        if len(audio_data) == 0:
            return float('inf')

        # Choisir le seuil selon la source
        threshold = SILENCE_THRESHOLD_BROWSER if role == "CLIENT" else SILENCE_THRESHOLD_MIC

        # Parcourir l'audio pour trouver le premier échantillon > seuil
        for i, sample in enumerate(audio_data):
            if abs(sample) > threshold:
                # Convertir l'index en secondes
                time_seconds = i / AUDIO_SAMPLE_RATE
                logger.debug(f"[SPEECH_DETECTION] {role}: Parole détectée à {time_seconds:.3f}s")
                return time_seconds

        # Aucune parole détectée
        logger.debug(f"[SPEECH_DETECTION] {role}: Aucune parole détectée (silence complet)")
        return float('inf')

    @staticmethod
    def is_silence(
        audio_data: np.ndarray,
        role: str,
        threshold: float = None,
        min_amplitude: int = None,
        min_audio_length: int = None
    ) -> bool:
        """
        Détecte si l'audio est du silence COMPLET

        ✅ LOGIQUE AND (plus permissive): Rejette SEULEMENT si TOUS les critères indiquent un silence
        Utilise 3 critères configurables selon la source audio:
        1. RMS (Root Mean Square) - Niveau sonore moyen
        2. Amplitude maximale - Pic de volume
        3. Durée minimale - Longueur de l'échantillon

        Args:
            audio_data: Array numpy de l'audio
            role: "CLIENT" (navigateur) ou "COMMERCIAL" (micro)
            threshold: Seuil RMS (optionnel, utilise config si None)
            min_amplitude: Amplitude min (optionnel, utilise config si None)
            min_audio_length: Durée min (optionnel, utilise config si None)

        Les seuils sont différents selon la source:
        - CLIENT (navigateur): Plus sensible (audio souvent plus faible)
        - COMMERCIAL (micro): Seuils adaptés pour micro direct

        Note: Utilise des seuils bas pour détecter uniquement le silence absolu.
        Deepgram est excellent pour gérer l'audio faible, donc on préfère envoyer l'audio
        plutôt que de le rejeter par excès de prudence.
        """
        if len(audio_data) == 0:
            return True

        # Seuils réduits de 50% pour ne détecter QUE le silence absolu
        # On laisse Deepgram gérer l'audio faible (il est très performant)
        if role == "CLIENT":
            # Audio du navigateur → seuils très sensibles
            threshold = (threshold or SILENCE_THRESHOLD_BROWSER) * 0.5
            min_amplitude = (min_amplitude or MIN_AMPLITUDE_BROWSER) * 0.5
            min_audio_length = (min_audio_length or MIN_AUDIO_LENGTH_BROWSER) * 0.5
        else:
            # Audio du micro → seuils réduits
            threshold = (threshold or SILENCE_THRESHOLD_MIC) * 0.5
            min_amplitude = (min_amplitude or MIN_AMPLITUDE_MIC) * 0.5
            min_audio_length = (min_audio_length or MIN_AUDIO_LENGTH_MIC) * 0.5

        # Calcul du RMS (niveau sonore moyen)
        audio_float = audio_data.astype(np.float32)
        rms = np.sqrt(np.mean(audio_float ** 2))

        # Amplitude maximale
        max_amplitude = np.max(np.abs(audio_data))

        # ✅ LOGIQUE AND: Rejette SEULEMENT si TOUS les critères indiquent un silence absolu
        # Cela évite de rejeter des phrases douces ou courtes
        is_silent = (
            rms < threshold and
            max_amplitude < min_amplitude and
            len(audio_data) < min_audio_length
        )

        # Log détaillé pour debug
        if is_silent:
            logger.debug(
                f"[SILENCE ABSOLU {role}] RMS={rms:.2f} (seuil={threshold:.1f}), "
                f"Max={max_amplitude:.0f} (seuil={min_amplitude:.0f}), "
                f"Samples={len(audio_data)} (min={int(min_audio_length)})"
            )
        else:
            logger.debug(
                f"[AUDIO DÉTECTÉ {role}] RMS={rms:.2f}, Max={max_amplitude:.0f}, Samples={len(audio_data)}"
            )

        return is_silent
    
    @staticmethod
    def detect_repetitions(text: str, max_consecutive: int = 4, max_total_ratio: float = 0.35) -> bool:
        """
        Détecte si un mot est répété excessivement (hallucination de Whisper)

        Deux types de détection :
        1. Répétitions CONSÉCUTIVES : "projet projet projet projet" (4+ fois)
        2. Répétitions DISPERSÉES : "projet" apparaît 20 fois dans 30 mots (> 35%)

        Args:
            text: Texte à vérifier
            max_consecutive: Nombre maximum de répétitions consécutives (défaut: 4)
            max_total_ratio: Ratio maximum d'un mot dans le texte (défaut: 0.35 = 35%)

        Returns:
            True si hallucination détectée, False sinon
        """
        if not text:
            return False

        words = text.strip().split()

        # Ignorer les textes très courts (< 5 mots)
        if len(words) < 5:
            return False

        # 1. DÉTECTION RÉPÉTITIONS CONSÉCUTIVES
        for i in range(len(words)):
            count = 1
            current_word = words[i].lower()

            # Compter les répétitions consécutives
            for j in range(i + 1, min(i + max_consecutive + 10, len(words))):
                if words[j].lower() == current_word:
                    count += 1
                else:
                    break

            # Si plus de max_consecutive répétitions consécutives
            if count > max_consecutive:
                logger.warning(
                    f"[FILTER] Hallucination - Répétitions consécutives détectées: "
                    f"'{current_word}' répété {count} fois de suite - Texte rejeté: {text[:100]}..."
                )
                return True

        # 2. 🆕 DÉTECTION RÉPÉTITIONS DISPERSÉES (nouveau !)
        # Compter la fréquence de chaque mot (mots > 3 caractères seulement)
        from collections import Counter

        # Filtrer les mots courts (ok de répéter "le", "de", "un", etc.)
        significant_words = [w.lower() for w in words if len(w) > 3]

        if len(significant_words) < 5:
            return False

        word_counts = Counter(significant_words)

        # Vérifier si un mot dépasse le ratio maximum
        for word, count in word_counts.items():
            ratio = count / len(significant_words)

            # Si un mot représente > 35% du texte → hallucination !
            if ratio > max_total_ratio and count > 5:
                logger.warning(
                    f"[FILTER] Hallucination - Répétitions dispersées détectées: "
                    f"'{word}' apparaît {count} fois sur {len(significant_words)} mots ({ratio*100:.1f}%) - "
                    f"Texte rejeté: {text[:100]}..."
                )
                return True

        return False

    @staticmethod
    def detect_youtube_hallucination(text: str) -> bool:
        """
        🆕 Détecte les hallucinations YouTube typiques de Whisper

        Whisper hallucine souvent du contenu YouTube sur du bruit de fond navigateur.
        Cette fonction détecte de manière agressive ces patterns.

        Returns:
            True si hallucination YouTube détectée, False sinon
        """
        if not text or len(text.strip()) < 10:
            return False

        text_lower = text.lower()

        # Mots-clés suspects (hallucinations YouTube typiques)
        youtube_keywords = [
            "youtube", "chaîne", "chaine", "vidéo", "video",
            "abonné", "abonnez", "like", "pouce bleu",
            "commentaire", "partage", "partagez",
            "épisode", "episode", "tutoriel", "tuto",
            "diffusion", "streaming", "live",
            "regarder", "visionner", "visionnage"
        ]

        # Compter combien de mots suspects apparaissent
        suspect_count = sum(1 for keyword in youtube_keywords if keyword in text_lower)

        # Si 2+ mots suspects → probablement une hallucination YouTube
        if suspect_count >= 2:
            logger.warning(
                f"[FILTER] Hallucination - Contenu YouTube suspect détecté "
                f"({suspect_count} mots-clés: vidéo/chaîne/etc.) - "
                f"Texte rejeté: {text[:100]}..."
            )
            return True

        # Patterns spécifiques très suspects
        youtube_phrases = [
            "chaîne youtube",
            "cette vidéo",
            "dans cette vidéo",
            "vidéo de l'équipe",
            "tour de la chaîne",
            "abonnez-vous",
            "mettez un like",
            "lâchez un pouce bleu"
        ]

        for phrase in youtube_phrases:
            if phrase in text_lower:
                logger.warning(
                    f"[FILTER] Hallucination - Phrase YouTube détectée: '{phrase}' - "
                    f"Texte rejeté: {text[:100]}..."
                )
                return True

        return False

    @staticmethod
    def clean_transcription(text: str) -> str:
        """
        Nettoie les transcriptions parasites

        Filtre les patterns indésirables configurés dans UNWANTED_PATTERNS,
        vérifie la longueur minimale MIN_TRANSCRIPTION_LENGTH,
        et détecte les hallucinations (répétitions excessives + YouTube)
        """
        if not text:
            return ""

        text_lower = text.lower()

        # 1. Vérifier les patterns indésirables (configurables)
        for pattern in UNWANTED_PATTERNS:
            if pattern.lower() in text_lower:
                logger.debug(f"[FILTER] Transcription rejetée (pattern: '{pattern}'): {text}")
                return ""

        # 2. Vérifier la longueur minimale (configurable)
        if len(text.strip()) < MIN_TRANSCRIPTION_LENGTH:
            logger.debug(f"[FILTER] Transcription trop courte ({len(text.strip())} < {MIN_TRANSCRIPTION_LENGTH}): {text}")
            return ""

        # 3. 🆕 Détecter les hallucinations YouTube (NOUVEAU - très agressif)
        if TranscriptionService.detect_youtube_hallucination(text):
            logger.warning(f"[FILTER] Hallucination YouTube détectée - Transcription rejetée: {text[:100]}...")
            return ""

        # 4. 🆕 Détecter les hallucinations (répétitions excessives)
        # max_consecutive=4 : "projet projet projet projet" → rejet
        # max_total_ratio=0.35 : "projet" × 20 dans 30 mots (67%) → rejet
        if TranscriptionService.detect_repetitions(text, max_consecutive=4, max_total_ratio=0.35):
            logger.warning(f"[FILTER] Hallucination répétition détectée - Transcription rejetée: {text[:100]}...")
            return ""

        # 5. 🆕 Nettoyer les espaces multiples et caractères parasites
        text = " ".join(text.split())  # Normaliser les espaces

        return text
    
    async def transcribe_audio(self, audio_array: np.ndarray, role: str) -> str:
        """
        Transcrit un array audio via Deepgram (ultra-rapide <300ms)

        Args:
            audio_array: Array numpy contenant l'audio
            role: Rôle (CLIENT ou COMMERCIAL) pour les logs et seuils de silence

        Returns:
            Texte transcrit et nettoyé
        """
        # Utiliser les seuils adaptés selon la source (CLIENT=navigateur, COMMERCIAL=micro)
        if self.is_silence(audio_array, role):
            logger.debug(f"[TRANSCRIPTION DEEPGRAM] {role}: Silence détecté")
            return ""

        tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp_file.name
        tmp_file.close()

        try:
            # Écrire l'audio dans un fichier temporaire
            sf.write(tmp_path, audio_array, self.sample_rate, subtype=self.subtype)

            # ⚡ DEEPGRAM - Transcription ultra-rapide
            with open(tmp_path, "rb") as audio_file:
                buffer_data = audio_file.read()

            # ✅ CORRECTION: request comme bytes directement (pas de dictionnaire)
            response = await asyncio.to_thread(
                self.deepgram.listen.v1.media.transcribe_file,
                request=buffer_data,  # Bytes directement
                model="nova-2",  # Modèle le plus récent et performant
                language="fr",   # Français
                smart_format=True,  # Formatage automatique
                punctuate=True,  # Ponctuation
                diarize=False  # Pas de diarisation
            )

            # Parser la réponse Deepgram
            text = ""
            if response and response.results:
                channels = response.results.channels
                if channels and len(channels) > 0:
                    alternatives = channels[0].alternatives
                    if alternatives and len(alternatives) > 0:
                        text = alternatives[0].transcript.strip()

            # Nettoyage et filtrage
            text = self.clean_transcription(text)

            if text:
                # Log avec horodatage
                timestamp = datetime.now().strftime("%H:%M:%S")
                logger.info(f"[TRANSCRIPTION DEEPGRAM] [{timestamp}] {role}: {text}")

            return text

        except Exception as e:
            logger.error(f"[TRANSCRIPTION DEEPGRAM] Erreur {role}: {e}")
            return ""
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    async def transcribe_parallel(
        self,
        client_audio: np.ndarray,
        commercial_audio: np.ndarray
    ) -> tuple[str, str]:
        """
        Transcrit les deux audios en parallèle
        
        Returns:
            Tuple (client_text, commercial_text)
        """
        client_text, commercial_text = await asyncio.gather(
            self.transcribe_audio(client_audio, "CLIENT"),
            self.transcribe_audio(commercial_audio, "COMMERCIAL")
        )
        
        return client_text, commercial_text
