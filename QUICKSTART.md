# 🚀 Démarrage Rapide KITT Backend

## Installation en 3 Minutes

### 1. Pré-requis
```bash
python --version  # Python 3.9+
pip --version     # pip 21.0+
```

### 2. Installation
```bash
cd kitt_backend
pip install -r requirements.txt --break-system-packages
```

### 3. Configuration
```bash
cp .env.example .env
nano .env  # Ajouter votre OPENAI_API_KEY
```

### 4. Lancement
```bash
python main.py
```

✅ Le serveur est prêt sur http://localhost:8000

---

## Test Rapide (2 minutes)

### 1. Vérifier la santé
```bash
curl http://localhost:8000/health
```

Résultat attendu:
```json
{
  "status": "healthy",
  "version": "3.1-refactored",
  "active_calls": 0
}
```

### 2. Démarrer une session
```bash
curl -X POST http://localhost:8000/calls/start \
  -H "Content-Type: application/json" \
  | jq
```

Résultat attendu:
```json
{
  "call_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "created_at": "2025-12-07T14:30:00",
  "conversation_phase": "introduction"
}
```

### 3. Récupérer le call_id
```bash
# Copier le call_id du résultat précédent
export CALL_ID="123e4567-e89b-12d3-a456-426614174000"
```

### 4. Tester avec de l'audio de test
```bash
# Créer des fichiers audio de test (silence)
python -c "
import numpy as np
import soundfile as sf
audio = np.zeros(44100, dtype=np.int16)
sf.write('test_client.wav', audio, 44100)
sf.write('test_commercial.wav', audio, 44100)
"

# Envoyer à l'API
curl -X POST http://localhost:8000/audio/$CALL_ID \
  -F "client_audio=@test_client.wav" \
  -F "commercial_audio=@test_commercial.wav" \
  | jq
```

### 5. Voir l'état de la session
```bash
curl http://localhost:8000/calls/$CALL_ID/state | jq
```

### 6. Terminer la session
```bash
curl -X POST http://localhost:8000/calls/$CALL_ID/end | jq
```

---

## Structure de Projet

```
kitt_backend/
├── main.py              ← Point d'entrée
├── requirements.txt     ← Dépendances
├── .env                 ← Configuration (à créer)
│
├── api/                 ← Routes FastAPI
│   ├── calls.py         # Sessions
│   ├── audio.py         # Audio + insights
│   ├── insights.py      # Historique
│   └── summary.py       # Résumés
│
├── core/                ← Logique métier
│   └── call_manager.py  # Gestion sessions
│
├── services/            ← Services indépendants
│   ├── transcription.py
│   ├── context_analyzer.py
│   ├── duplicate_detector.py
│   ├── coaching.py
│   └── summary.py
│
├── models/              ← Modèles de données
│   ├── schemas.py
│   └── profiles.py
│
└── config/              ← Configuration
    └── settings.py
```

---

## Commandes Utiles

### Développement
```bash
# Mode développement avec rechargement auto
python main.py

# Ou avec uvicorn directement
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Logs détaillés
uvicorn main:app --reload --log-level debug
```

### Production
```bash
# Avec plusieurs workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Avec HTTPS
uvicorn main:app --host 0.0.0.0 --port 443 \
  --ssl-keyfile=/path/to/key.pem \
  --ssl-certfile=/path/to/cert.pem
```

### Tests
```bash
# Test unitaire d'un service
python -c "
from services import TranscriptionService
service = TranscriptionService()
print('✓ TranscriptionService OK')
"

# Test de tous les imports
python -c "
from main import app
from services import *
from models import *
print('✓ Tous les imports OK')
"
```

---

## Endpoints Principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Informations API |
| GET | `/health` | Santé du serveur |
| GET | `/docs` | Documentation interactive |
| POST | `/calls/start` | Démarrer session |
| POST | `/calls/{id}/end` | Terminer session |
| GET | `/calls/{id}/state` | État session |
| POST | `/audio/{id}` | Traiter audio |
| GET | `/calls/{id}/insights` | Historique insights |
| POST | `/resume/{id}` | Résumé client |
| POST | `/summary/{id}` | Résumé commercial |

---

## Documentation Interactive

Une fois le serveur démarré:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Ces interfaces permettent de:
- ✅ Voir tous les endpoints
- ✅ Tester directement l'API
- ✅ Voir les schémas de données
- ✅ Générer du code client

---

## Variables d'Environnement

Dans `.env`:

```bash
# Obligatoire
OPENAI_API_KEY=sk-...

# Optionnel (avec valeurs par défaut)
SILENCE_THRESHOLD=620.0
MIN_INSIGHT_INTERVAL=1
LOG_LEVEL=INFO
```

---

## Troubleshooting

### Erreur: "OpenAI API key not found"
```bash
# Vérifier le .env
cat .env | grep OPENAI_API_KEY

# Créer si manquant
echo "OPENAI_API_KEY=sk-..." > .env
```

### Erreur: "Module not found"
```bash
# Réinstaller les dépendances
pip install -r requirements.txt --break-system-packages
```

### Erreur: "Port 8000 already in use"
```bash
# Trouver et tuer le process
lsof -ti:8000 | xargs kill -9

# Ou utiliser un autre port
uvicorn main:app --port 8001
```

### Logs trop verbeux
```bash
# Dans .env
LOG_LEVEL=WARNING
```

---

## Prochaines Étapes

1. ✅ **Tester avec audio réel**: Remplacer les fichiers de test
2. ✅ **Explorer les insights**: Voir `/calls/{id}/insights`
3. ✅ **Générer des résumés**: Tester `/resume/{id}`
4. ✅ **Lire la doc complète**: `README.md`, `ARCHITECTURE.md`
5. ✅ **Consulter les exemples**: Dossier `examples/` (à créer)

---

## Support & Ressources

- 📚 Documentation complète: `README.md`
- 🏗️ Architecture détaillée: `ARCHITECTURE.md`
- 🔄 Guide de migration: `MIGRATION_GUIDE.md`
- 📊 Exemples de logs: `EXEMPLE_LOGS_ANTI_DOUBLON.txt`

---

## Développement

### Ajouter un nouveau service

1. Créer `services/my_service.py`
2. Implémenter la classe
3. Importer dans `services/__init__.py`
4. Utiliser dans les routes

### Ajouter une nouvelle route

1. Créer `api/my_route.py`
2. Définir le router
3. Importer dans `main.py`
4. `app.include_router(my_route.router)`

### Modifier la configuration

1. Ajouter dans `config/settings.py`
2. Importer où nécessaire: `from config.settings import MY_VAR`

---

## Performance

Temps typiques (sur MacBook M1):
- ✅ Transcription audio (2 fichiers): ~300-500ms
- ✅ Génération insight: ~400-800ms
- ✅ Détection doublon IA: ~200-500ms
- ✅ Résumé complet: ~1-3s

**Total pour un cycle complet**: ~1-2 secondes

---

🎉 **Vous êtes prêt !** Le backend KITT est opérationnel.
