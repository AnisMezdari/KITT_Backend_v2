"""
Service de transcription audio via Whisper
"""
import logging
import tempfile
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import numpy as np
import soundfile as sf
import openai

from config.settings import (
    WHISPER_MODEL,
    AUDIO_SAMPLE_RATE,
    AUDIO_SUBTYPE,
    SILENCE_THRESHOLD_MIC,
    MIN_AMPLITUDE_MIC,
    MIN_AUDIO_LENGTH_MIC,
    SILENCE_THRESHOLD_BROWSER,
    MIN_AMPLITUDE_BROWSER,
    MIN_AUDIO_LENGTH_BROWSER,
    WHISPER_LANGUAGE,
    WHISPER_PROMPT,
    WHISPER_TEMPERATURE,
    MIN_TRANSCRIPTION_LENGTH,
    UNWANTED_PATTERNS
)

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service gérant la transcription audio"""
    
    def __init__(self):
        self.model = WHISPER_MODEL
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.subtype = AUDIO_SUBTYPE
    
    @staticmethod
    def is_silence(
        audio_data: np.ndarray,
        role: str,
        threshold: float = None,
        min_amplitude: int = None,
        min_audio_length: int = None
    ) -> bool:
        """
        Détecte si l'audio est du silence

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
        - COMMERCIAL (micro): Plus strict (audio direct, plus fort)
        """
        if len(audio_data) == 0:
            return True

        # Choisir les seuils selon la source audio
        if role == "CLIENT":
            # Audio du navigateur → seuils sensibles
            threshold = threshold or SILENCE_THRESHOLD_BROWSER
            min_amplitude = min_amplitude or MIN_AMPLITUDE_BROWSER
            min_audio_length = min_audio_length or MIN_AUDIO_LENGTH_BROWSER
        else:
            # Audio du micro → seuils normaux
            threshold = threshold or SILENCE_THRESHOLD_MIC
            min_amplitude = min_amplitude or MIN_AMPLITUDE_MIC
            min_audio_length = min_audio_length or MIN_AUDIO_LENGTH_MIC

        # Calcul du RMS (niveau sonore moyen)
        audio_float = audio_data.astype(np.float32)
        rms = np.sqrt(np.mean(audio_float ** 2))

        # Amplitude maximale
        max_amplitude = np.max(np.abs(audio_data))

        # Vérification avec les seuils
        is_silent = (
            rms < threshold or
            max_amplitude < min_amplitude or
            len(audio_data) < min_audio_length
        )

        # Log détaillé pour debug
        if is_silent:
            logger.debug(
                f"[SILENCE {role}] RMS={rms:.2f} (seuil={threshold}), "
                f"Max={max_amplitude:.0f} (seuil={min_amplitude}), "
                f"Samples={len(audio_data)} (min={min_audio_length})"
            )

        return is_silent
    
    @staticmethod
    def clean_transcription(text: str) -> str:
        """
        Nettoie les transcriptions parasites

        Filtre les patterns indésirables configurés dans UNWANTED_PATTERNS
        et vérifie la longueur minimale MIN_TRANSCRIPTION_LENGTH
        """
        if not text:
            return ""

        text_lower = text.lower()

        # Vérifier les patterns indésirables (configurables)
        for pattern in UNWANTED_PATTERNS:
            if pattern.lower() in text_lower:
                logger.debug(f"[FILTER] Transcription rejetée (pattern: '{pattern}'): {text}")
                return ""

        # Vérifier la longueur minimale (configurable)
        if len(text.strip()) < MIN_TRANSCRIPTION_LENGTH:
            logger.debug(f"[FILTER] Transcription trop courte ({len(text.strip())} < {MIN_TRANSCRIPTION_LENGTH}): {text}")
            return ""

        return text
    
    async def transcribe_audio(self, audio_array: np.ndarray, role: str) -> str:
        """
        Transcrit un array audio via Whisper

        Args:
            audio_array: Array numpy contenant l'audio
            role: Rôle (CLIENT ou COMMERCIAL) pour les logs et seuils de silence

        Returns:
            Texte transcrit et nettoyé
        """
        # Utiliser les seuils adaptés selon la source (CLIENT=navigateur, COMMERCIAL=micro)
        if self.is_silence(audio_array, role):
            logger.debug(f"[TRANSCRIPTION] {role}: Silence détecté")
            return ""
        
        tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp_file.name
        tmp_file.close()
        
        try:
            # Écrire l'audio dans un fichier temporaire
            sf.write(tmp_path, audio_array, self.sample_rate, subtype=self.subtype)
            
            # Transcription asynchrone
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)
            
            # Ouvrir le fichier audio
            audio_file = open(tmp_path, "rb")
            
            # Appel à l'API Whisper avec paramètres configurables
            transcription_params = {
                "model": self.model,
                "file": audio_file,
                "language": WHISPER_LANGUAGE if WHISPER_LANGUAGE else None,
                "temperature": WHISPER_TEMPERATURE,
            }

            # Ajouter le prompt si configuré
            if WHISPER_PROMPT:
                transcription_params["prompt"] = WHISPER_PROMPT

            transcription = await loop.run_in_executor(
                executor,
                lambda: openai.audio.transcriptions.create(**transcription_params)
            )
            
            # Fermer le fichier
            audio_file.close()
            
            text = transcription.text.strip()
            text = self.clean_transcription(text)

            if text:
                # Log avec horodatage pour le fichier de transcription
                timestamp = datetime.now().strftime("%H:%M:%S")
                logger.info(f"[TRANSCRIPTION] [{timestamp}] {role}: {text}")
            
            return text
            
        except Exception as e:
            logger.error(f"[TRANSCRIPTION] Erreur {role}: {e}")
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
