# Guide de Migration - Version Refactorisée

## 🔄 Migration depuis backend_kitt_complete_v3.py

### Changements Principaux

#### 1. Structure de Fichiers

**Avant** (monolithique):
```
backend_kitt_complete_v3.py  # 1600+ lignes
```

**Après** (modulaire):
```
kitt_backend/
├── api/          # Routes (4 fichiers)
├── core/         # CallManager
├── services/     # Services métier (5 fichiers)
├── models/       # Modèles de données
├── config/       # Configuration
└── main.py       # Application
```

#### 2. Imports

**Avant**:
```python
# Tout dans un fichier
from backend_kitt_complete_v3 import app
```

**Après**:
```python
# Imports modulaires
from kitt_backend.main import app
from kitt_backend.services import TranscriptionService
from kitt_backend.models import CallConfig
```

#### 3. Configuration

**Avant**:
```python
# Variables éparpillées
SILENCE_THRESHOLD = 620.0
MIN_INSIGHT_INTERVAL = 1
```

**Après**:
```python
# Centralisé dans config/settings.py
from config.settings import SILENCE_THRESHOLD, MIN_INSIGHT_INTERVAL
```

### Compatibilité API

✅ **AUCUN CHANGEMENT** dans les endpoints !

Tous les endpoints existants fonctionnent exactement pareil :
- `POST /calls/start`
- `POST /audio/{session_id}`
- `GET /calls/{session_id}/state`
- `POST /resume/{session_id}`
- etc.

### Migration Étape par Étape

#### Étape 1: Installer la nouvelle version

```bash
cd /path/to/project
git clone kitt_backend/  # ou copier le dossier
cd kitt_backend
pip install -r requirements.txt
```

#### Étape 2: Copier la configuration

```bash
# Copier votre .env actuel
cp /old/path/.env ./kitt_backend/.env
```

#### Étape 3: Arrêter l'ancien serveur

```bash
# Trouver le process
ps aux | grep backend_kitt

# Tuer le process
kill <PID>
```

#### Étape 4: Démarrer le nouveau serveur

```bash
cd kitt_backend
python main.py

# Ou avec uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Étape 5: Vérifier le fonctionnement

```bash
# Test de santé
curl http://localhost:8000/health

# Devrait retourner: {"status": "healthy", "version": "3.1-refactored"}
```

### Avantages de la Nouvelle Architecture

#### 1. Maintenabilité

**Avant**: Modifier la transcription = chercher dans 1600 lignes
**Après**: Ouvrir `services/transcription.py` (150 lignes)

#### 2. Tests

**Avant**: Difficile de tester une fonction isolée
**Après**: Chaque service est testable indépendamment

```python
# Tester uniquement la transcription
from services import TranscriptionService

service = TranscriptionService()
result = await service.transcribe_audio(audio, "CLIENT")
```

#### 3. Réutilisabilité

**Avant**: Tout est couplé
**Après**: Services réutilisables

```python
# Utiliser le détecteur de doublons ailleurs
from services import DuplicateDetector

detector = DuplicateDetector()
is_dup = await detector.check_duplicate(...)
```

#### 4. Scalabilité

**Avant**: Ajouter une fonctionnalité = modifier le gros fichier
**Après**: Ajouter un nouveau service = créer un fichier

```bash
# Ajouter un nouveau service
touch services/notification.py
```

### Nouveautés Exclusives à la Version Refactorisée

#### 1. Configuration Centralisée

```python
# config/settings.py
# Modifier un paramètre ici = effet partout
MAX_CONTEXT_MESSAGES = 24  # Était codé en dur avant
TIME_THRESHOLD_DUPLICATE = 60
```

#### 2. Logging Amélioré

```python
# Chaque service a son logger
logger = logging.getLogger(__name__)
```

Filtrer par service:
```bash
# Logs uniquement du service de transcription
uvicorn main:app --reload 2>&1 | grep "transcription"
```

#### 3. Typage Strict

```python
# Avant: types implicites
def process(data):
    ...

# Après: types explicites partout
async def process(data: np.ndarray, role: str) -> str:
    ...
```

### Points d'Attention

#### 1. Imports Relatifs

**Avant**:
```python
from backend_kitt_complete_v3 import active_calls
```

**Après**:
```python
from api.calls import get_active_calls
active_calls = get_active_calls()
```

#### 2. Variables Globales

Les `active_calls` sont maintenant accessibles via fonction:
```python
# Dans les routes
from api.calls import get_active_calls
active_calls = get_active_calls()
```

#### 3. Configuration

Les variables d'environnement sont chargées automatiquement depuis `config/settings.py`

### Rollback en Cas de Problème

Si vous rencontrez un problème:

```bash
# 1. Arrêter le nouveau serveur
# Ctrl+C ou kill <PID>

# 2. Redémarrer l'ancien
cd /old/path
uvicorn backend_kitt_complete_v3:app --reload
```

Aucune perte de données : les sessions sont en mémoire donc se réinitialisent de toute façon.

### Support

En cas de problème:
1. Vérifier les logs détaillés
2. Comparer avec l'ancienne version
3. Tous les endpoints sont identiques
4. Seule l'organisation interne a changé

### Checklist Post-Migration

- [ ] Le serveur démarre sans erreur
- [ ] `GET /health` retourne `{"status": "healthy"}`
- [ ] `POST /calls/start` crée une session
- [ ] `POST /audio/{session_id}` traite l'audio
- [ ] Les logs sont lisibles
- [ ] Les insights sont générés
- [ ] L'anti-doublon IA fonctionne
- [ ] Les résumés fonctionnent

### Performance

La version refactorisée a les **mêmes performances** que l'ancienne :
- Même modèle fine-tuné
- Même logique de traitement
- Mêmes appels API
- Juste mieux organisé !

### Prochaines Étapes Recommandées

1. **Tests unitaires**: Ajouter `tests/` pour chaque service
2. **CI/CD**: Intégrer GitHub Actions
3. **Monitoring**: Ajouter Prometheus/Grafana
4. **Cache**: Ajouter Redis pour les sessions
5. **Documentation**: Générer docs avec Sphinx
