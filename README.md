# KITT Backend - Version Refactorisée

Backend modulaire et scalable pour le système de coaching commercial en temps réel KITT.

## 🏗️ Architecture

```
kitt_backend/
├── api/                    # Routes FastAPI modulaires
│   ├── calls.py           # Gestion des sessions
│   ├── audio.py           # Traitement audio + insights
│   ├── insights.py        # Historique des insights
│   └── summary.py         # Résumés d'appels
│
├── core/                   # Coeur applicatif
│   └── call_manager.py    # Gestionnaire de sessions
│
├── services/               # Services métier
│   ├── transcription.py   # Transcription Whisper
│   ├── context_analyzer.py # Analyse de contexte
│   ├── duplicate_detector.py # Détection doublons IA
│   ├── coaching.py        # Génération insights
│   └── summary.py         # Génération résumés
│
├── models/                 # Modèles de données
│   ├── schemas.py         # Schemas Pydantic
│   └── profiles.py        # Profils clients
│
├── config/                 # Configuration
│   └── settings.py        # Variables centralisées
│
├── main.py                 # Application FastAPI
└── requirements.txt        # Dépendances
```

## ✨ Fonctionnalités

- ✅ **Contexte structuré enrichi** (24 messages, phase, pain points)
- ✅ **Transcription parallèle** (Whisper)
- ✅ **Insights temps réel** (modèle fine-tuné)
- ✅ **Anti-doublon IA** avec fenêtre temporelle (60s)
- ✅ **2 modes de résumé** (client + commercial)
- ✅ **Historique complet** des insights avec stats
- ✅ **Architecture modulaire** facilement extensible

## 🚀 Installation

```bash
# Cloner le repo
cd kitt_backend

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et ajouter votre OPENAI_API_KEY
```

## ⚙️ Configuration

Fichier `.env`:

```env
OPENAI_API_KEY=sk-...
SILENCE_THRESHOLD=620.0
MIN_INSIGHT_INTERVAL=1
LOG_LEVEL=INFO
```

## 🎯 Démarrage

```bash
# Depuis le dossier kitt_backend/
python main.py

# Ou avec uvicorn directement
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera disponible sur http://localhost:8000

## 📚 Documentation API

Documentation interactive disponible sur:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Endpoints Principaux

### Sessions d'appels

```http
POST   /calls/start                    # Démarrer une session
POST   /calls/{session_id}/end         # Terminer une session
GET    /calls/{session_id}/state       # État de la session
```

### Audio & Insights

```http
POST   /audio/{session_id}             # Traiter audio + générer insight
```

### Historique

```http
GET    /calls/{session_id}/insights    # Historique complet des insights
```

### Résumés

```http
POST   /resume/{session_id}            # Résumé focus CLIENT
POST   /summary/{session_id}           # Résumé focus COMMERCIAL
```

## 🧪 Tests

```bash
# Test de santé
curl http://localhost:8000/health

# Démarrer une session
curl -X POST http://localhost:8000/calls/start \
  -H "Content-Type: application/json"

# Traiter de l'audio
curl -X POST http://localhost:8000/audio/{session_id} \
  -F "client_audio=@client.wav" \
  -F "commercial_audio=@commercial.wav"
```

## 📊 Logs

Les logs détaillés incluent:
- ✅ Transcriptions audio
- ✅ Phase de conversation détectée
- ✅ Insights générés
- ✅ Analyse anti-doublon avec raison
- ✅ Décisions IA expliquées

## 🔒 Sécurité

- ✅ CORS configuré
- ✅ Validation Pydantic
- ✅ Gestion d'erreurs robuste
- ✅ Clés API en environnement

## 🛠️ Développement

### Ajouter un nouveau service

1. Créer le fichier dans `services/`
2. Implémenter la classe de service
3. L'importer dans `services/__init__.py`
4. L'utiliser dans les routes appropriées

### Ajouter une nouvelle route

1. Créer le fichier dans `api/`
2. Définir le router FastAPI
3. L'importer et l'inclure dans `main.py`

## 📈 Performance

- **Transcription parallèle**: ~200-500ms pour 2 audios
- **Génération insight**: ~300-800ms
- **Détection doublon IA**: ~200-500ms
- **Résumé complet**: ~1-3s

## 🐛 Troubleshooting

### Erreur "OpenAI API key not found"
- Vérifier que `.env` existe et contient `OPENAI_API_KEY`

### Erreur "Session non trouvée"
- La session a expiré ou n'a pas été créée avec `/calls/start`

### Logs trop verbeux
- Modifier `LOG_LEVEL=WARNING` dans `.env`

## 📝 License

Propriétaire KITT

## 👥 Contributeurs

- Architecture refactorisée v3.1
- Services modulaires
- Anti-doublon IA
- Documentation complète
