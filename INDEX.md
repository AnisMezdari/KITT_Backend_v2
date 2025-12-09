# 📚 KITT Backend - Documentation Complète

## Table des Matières

### 🚀 Pour Démarrer

1. **[QUICKSTART.md](QUICKSTART.md)** ⭐ **Commencez ici !**
   - Installation en 3 minutes
   - Test rapide
   - Commandes utiles
   - Troubleshooting de base

2. **[README.md](README.md)**
   - Vue d'ensemble du projet
   - Architecture générale
   - Installation détaillée
   - Tests et développement

### 🏗️ Architecture & Technique

3. **[ARCHITECTURE.md](ARCHITECTURE.md)**
   - Diagrammes détaillés
   - Flux de traitement
   - Modules et responsabilités
   - Points d'extension

4. **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)**
   - Migration depuis version monolithique
   - Compatibilité API
   - Avantages de la refactorisation
   - Checklist post-migration

### 📦 Structure du Projet

```
kitt_backend/
│
├── 📄 Documentation
│   ├── INDEX.md                 ← Vous êtes ici
│   ├── QUICKSTART.md            ← Démarrage rapide
│   ├── README.md                ← Documentation principale
│   ├── ARCHITECTURE.md          ← Architecture détaillée
│   └── MIGRATION_GUIDE.md       ← Guide de migration
│
├── 🔧 Configuration
│   ├── .env.example             ← Template de configuration
│   ├── requirements.txt         ← Dépendances Python
│   └── config/
│       └── settings.py          ← Configuration centralisée
│
├── 🚀 Application
│   └── main.py                  ← Point d'entrée FastAPI
│
├── 🌐 API Routes
│   └── api/
│       ├── calls.py             ← Gestion des sessions
│       ├── audio.py             ← Traitement audio + insights
│       ├── insights.py          ← Historique des insights
│       └── summary.py           ← Résumés d'appels
│
├── 🧠 Coeur Applicatif
│   └── core/
│       └── call_manager.py      ← Gestionnaire de sessions
│
├── ⚙️ Services Métier
│   └── services/
│       ├── transcription.py     ← Service Whisper
│       ├── context_analyzer.py  ← Analyse de contexte
│       ├── duplicate_detector.py ← Détection doublons IA
│       ├── coaching.py          ← Génération d'insights
│       └── summary.py           ← Génération de résumés
│
└── 📊 Modèles de Données
    └── models/
        ├── schemas.py           ← Schemas Pydantic
        └── profiles.py          ← Profils clients
```

---

## 🎯 Guides par Cas d'Usage

### Je débute avec le projet

1. Lire [QUICKSTART.md](QUICKSTART.md) (10 min)
2. Installer et tester (5 min)
3. Explorer la doc interactive: http://localhost:8000/docs

### Je veux comprendre l'architecture

1. Lire [ARCHITECTURE.md](ARCHITECTURE.md) (20 min)
2. Examiner les diagrammes de flux
3. Explorer le code source avec les commentaires

### Je migre depuis l'ancienne version

1. Lire [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) (15 min)
2. Suivre la checklist étape par étape
3. Tester la compatibilité API

### Je veux ajouter une fonctionnalité

1. Lire la section "Points d'Extension" dans [ARCHITECTURE.md](ARCHITECTURE.md)
2. Créer un nouveau service dans `services/`
3. L'exposer via une route dans `api/`
4. Tester avec `/docs`

### Je rencontre un problème

1. Consulter "Troubleshooting" dans [QUICKSTART.md](QUICKSTART.md)
2. Vérifier les logs détaillés
3. Consulter les exemples de logs

---

## 📖 Sections Clés de la Documentation

### Configuration

**Fichiers**:
- `.env` (à créer depuis `.env.example`)
- `config/settings.py`

**Variables principales**:
```bash
OPENAI_API_KEY=sk-...           # Obligatoire
SILENCE_THRESHOLD=620.0         # Seuil de détection silence
MIN_INSIGHT_INTERVAL=1          # Intervalle min entre insights (sec)
LOG_LEVEL=INFO                  # Niveau de logs
```

### Routes API

| Endpoint | Description | Documentation |
|----------|-------------|---------------|
| `GET /` | Info API | [main.py](main.py) |
| `GET /health` | Santé serveur | [main.py](main.py) |
| `POST /calls/start` | Démarrer session | [api/calls.py](api/calls.py) |
| `POST /audio/{id}` | Traiter audio | [api/audio.py](api/audio.py) |
| `GET /calls/{id}/insights` | Historique | [api/insights.py](api/insights.py) |
| `POST /resume/{id}` | Résumé client | [api/summary.py](api/summary.py) |

### Services

| Service | Responsabilité | Fichier |
|---------|----------------|---------|
| TranscriptionService | Whisper, audio | [services/transcription.py](services/transcription.py) |
| ContextAnalyzer | Phase, pain points | [services/context_analyzer.py](services/context_analyzer.py) |
| DuplicateDetector | Anti-doublons IA | [services/duplicate_detector.py](services/duplicate_detector.py) |
| CoachingService | Insights temps réel | [services/coaching.py](services/coaching.py) |
| SummaryService | Résumés structurés | [services/summary.py](services/summary.py) |

### Modèles

| Modèle | Usage | Fichier |
|--------|-------|---------|
| ClientProfile | Enum profils | [models/schemas.py](models/schemas.py) |
| ClientPersonality | Personnalité client | [models/schemas.py](models/schemas.py) |
| CallConfig | Config appel | [models/schemas.py](models/schemas.py) |
| PROFILE_TEMPLATES | Templates profils | [models/profiles.py](models/profiles.py) |

---

## 🔥 Fonctionnalités Clés

### 1. Contexte Structuré Enrichi
- **Fenêtre**: 24 messages maximum
- **Phase**: Détection automatique (intro, discovery, etc.)
- **Pain Points**: Extraction automatique
- **Topics**: Tracking des sujets couverts

**Voir**: [services/context_analyzer.py](services/context_analyzer.py)

### 2. Anti-Doublon IA avec Fenêtre Temporelle
- **IA**: GPT-4o-mini pour analyse sémantique
- **Temporal**: Insights > 60s non considérés comme doublons
- **Fallback**: Système de secours en cas d'erreur IA

**Voir**: [services/duplicate_detector.py](services/duplicate_detector.py)

### 3. Insights en Temps Réel
- **Modèle**: Fine-tuned GPT-4o-mini
- **Types**: Alert 🔴, Opportunity 🔵, Progression 🟢
- **Format**: Titre + Action recommandée

**Voir**: [services/coaching.py](services/coaching.py)

### 4. Transcription Parallèle
- **Modèle**: Whisper
- **Performance**: ~300-500ms pour 2 fichiers
- **Nettoyage**: Suppression automatique des parasites

**Voir**: [services/transcription.py](services/transcription.py)

### 5. Résumés Dual-Focus
- **Client**: Besoins, objections, pain points
- **Commercial**: Performance, points forts/faibles
- **Format**: JSON structuré

**Voir**: [services/summary.py](services/summary.py)

---

## 🎓 Concepts Avancés

### Contexte Structuré

Le `CallManager` maintient un **contexte structuré** qui évolue en temps réel:

```python
{
  "phase": "negotiation",              # Phase actuelle
  "pain_points": ["Onboarding lent"],  # Pain points identifiés
  "topics_covered": ["pricing", "roi"], # Sujets déjà traités
  "messages": [...],                   # Fenêtre limitée (24 msg)
  "full_transcript": [...]             # Historique complet
}
```

**Avantage**: Le modèle d'IA comprend mieux le contexte pour générer des insights pertinents.

### Fenêtre Temporelle

Le `DuplicateDetector` utilise une **fenêtre temporelle intelligente**:

```
Insight A (15s ago)  → 🔥 RÉCENT  → Comparaison stricte
Insight B (90s ago)  → ⏰ ANCIEN  → Peut être similaire
```

**Avantage**: Rappels pertinents autorisés après un certain temps.

### Architecture Modulaire

Chaque **service est indépendant** et **testable** isolément:

```python
# Tester uniquement la transcription
from services import TranscriptionService
service = TranscriptionService()
result = await service.transcribe_audio(audio, "CLIENT")
```

**Avantage**: Développement, tests et maintenance simplifiés.

---

## 📊 Métriques & Performance

### Temps de Réponse Typiques

| Opération | Temps | Endpoint |
|-----------|-------|----------|
| Transcription (x2) | 300-500ms | `/audio/{id}` |
| Génération insight | 400-800ms | `/audio/{id}` |
| Détection doublon | 200-500ms | `/audio/{id}` |
| Résumé complet | 1-3s | `/resume/{id}` |

### Limites de Contexte

| Paramètre | Valeur | Configurable |
|-----------|--------|--------------|
| Messages en contexte | 24 | ✅ `MAX_CONTEXT_MESSAGES` |
| Insights en cache | 5 | ✅ `MAX_INSIGHTS_CACHE` |
| Seuil temporel | 60s | ✅ `TIME_THRESHOLD_DUPLICATE` |
| Intervalle min insights | 1s | ✅ `MIN_INSIGHT_INTERVAL` |

---

## 🛠️ Développement

### Commandes Essentielles

```bash
# Lancer le serveur
python main.py

# Tests manuels
curl http://localhost:8000/health

# Logs filtrés
uvicorn main:app --reload 2>&1 | grep "ANTI-DOUBLON"

# Linter
flake8 .

# Type checking
mypy .
```

### Structure d'un Service

```python
class MyService:
    """Description du service"""
    
    def __init__(self):
        """Initialisation"""
        self.config = ...
    
    async def do_something(self, param: str) -> str:
        """Méthode principale"""
        try:
            result = await asyncio.to_thread(...)
            return result
        except Exception as e:
            logger.error(f"Erreur: {e}")
            return self._fallback()
    
    def _fallback(self) -> str:
        """Méthode de secours"""
        return "default"
```

### Ajout d'un Endpoint

```python
# api/my_route.py
from fastapi import APIRouter

router = APIRouter(prefix="/my", tags=["my"])

@router.get("/")
async def my_endpoint():
    return {"message": "Hello"}

# main.py
from api import my_route
app.include_router(my_route.router)
```

---

## 🔒 Sécurité & Production

### Variables Sensibles
- ✅ Stocker dans `.env` (jamais commit)
- ✅ Utiliser secrets managers en production
- ✅ Chiffrer en transit (HTTPS)

### CORS
- ✅ Configuré pour localhost en dev
- ⚠️ Restreindre en production

### Rate Limiting
- ⚠️ À implémenter pour production
- Recommandation: 100 req/min par IP

### Monitoring
- Logs structurés (JSON)
- Métriques (Prometheus)
- Alertes (PagerDuty, Sentry)

---

## 📞 Support

### Problèmes Courants

1. **"OpenAI API key not found"**
   → Vérifier `.env`

2. **"Session non trouvée"**
   → Appeler `/calls/start` d'abord

3. **"Port already in use"**
   → `kill $(lsof -ti:8000)`

### Ressources

- 📚 Docs complètes dans ce dossier
- 🌐 API interactive: http://localhost:8000/docs
- 📝 Logs détaillés dans le terminal

---

## 🎉 Conclusion

Cette architecture **modulaire**, **scalable** et **maintenable** permet:

- ✅ Ajout facile de nouvelles fonctionnalités
- ✅ Tests unitaires par service
- ✅ Déploiement flexible
- ✅ Maintenance simplifiée
- ✅ Collaboration d'équipe efficace

**Prochaines étapes recommandées**:
1. Lire [QUICKSTART.md](QUICKSTART.md)
2. Installer et tester
3. Explorer le code source
4. Contribuer ! 🚀

---

**Version**: 3.1-refactored  
**Dernière mise à jour**: Décembre 2025  
**Auteur**: KITT Team
