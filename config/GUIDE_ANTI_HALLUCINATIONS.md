# 🛡️ GUIDE ANTI-HALLUCINATIONS WHISPER

Ce guide explique **toutes les solutions** pour réduire les hallucinations de Whisper dans vos transcriptions.

---

## 🔍 Pourquoi Whisper hallucine ?

Whisper invente parfois des mots ou phrases quand :
1. ❌ **Audio de mauvaise qualité** : Bruit de fond, volume trop faible
2. ❌ **Silences ou quasi-silences** : Whisper "comble" avec du texte inventé
3. ❌ **Prompt trop générique** : Whisper ne connaît pas le contexte
4. ❌ **Audio trop court** : Moins de 1 seconde, Whisper devine

---

## ✅ SOLUTION #1 : Améliorer le prompt Whisper (RECOMMANDÉ)

**Fichier** : `config/audio_config.yaml` (lignes 49-56)

### **Principe :**
Plus le prompt est **spécifique** avec des exemples de vocabulaire, moins Whisper hallucine.

### **Exemples :**

**❌ MAUVAIS (trop générique) :**
```yaml
prompt: "Conversation commerciale entre un vendeur et un client"
```

**✅ BON (avec vocabulaire) :**
```yaml
prompt: "Conversation commerciale professionnelle entre un commercial et un client en français. Vocabulaire typique: bonjour, entreprise, solution, produit, budget, tarif, devis, intéressé, besoin, service, démonstration, questions."
```

**🚀 EXCELLENT (avec noms propres et termes spécifiques) :**
```yaml
prompt: "Appel commercial pour KIT, une solution d'IA pour les commerciaux. Noms récurrents: Anis Mezdari, entreprise KITT. Vocabulaire: fonctionnalités, ROI, implémentation, insights temps réel, coaching, transcription, intelligence artificielle, IA."
```

### **Comment personnaliser :**

1. **Ajoute les noms propres** que tu utilises souvent :
   ```
   Noms récurrents: [Ton nom], [Nom de ton entreprise], [Nom de tes produits]
   ```

2. **Ajoute ton vocabulaire métier** :
   ```
   Vocabulaire: [mots techniques], [termes récurrents], [expressions typiques]
   ```

3. **Teste et ajuste** : Regarde les logs de transcription et ajoute les mots qui reviennent

---

## ✅ SOLUTION #2 : Augmenter les seuils de silence

**Fichier** : `config/audio_config.yaml` (lignes 8-38)

### **Principe :**
Plus les seuils sont **stricts**, moins Whisper reçoit d'audio avec du bruit de fond.

### **Seuils actuels :**

**Microphone (COMMERCIAL) :**
```yaml
microphone:
  rms_threshold: 620.0      # Niveau sonore moyen
  min_amplitude: 1000       # Volume maximum requis
  min_audio_length: 8000    # Durée minimale (~0.18s)
```

**Navigateur/CLIENT (audio partagé) :**
```yaml
browser:
  rms_threshold: 550.0      # Plus sensible que le micro
  min_amplitude: 900        # Plus sensible que le micro
  min_audio_length: 8000
```

### **Comment ajuster :**

**Si tu as DES HALLUCINATIONS** → Augmente les seuils :
```yaml
browser:
  rms_threshold: 650.0      # Plus strict (600-700)
  min_amplitude: 1200       # Plus strict (1000-1500)
  min_audio_length: 10000   # Ignorer clips très courts
```

**Si des VRAIES PAROLES sont COUPÉES** → Réduis les seuils :
```yaml
browser:
  rms_threshold: 450.0      # Plus sensible
  min_amplitude: 700        # Plus sensible
```

### **Comment tester les seuils :**

1. Active les logs DEBUG temporairement :
   ```bash
   # Dans .env
   LOG_LEVEL=DEBUG
   ```

2. Lance une session et regarde les logs :
   ```bash
   tail -f logs/kitt_main.log | grep "SILENCE"
   ```

3. Tu verras :
   ```
   [SILENCE CLIENT] RMS=234.56 (seuil=550), Max=678 (seuil=900), Samples=12450
   ```

4. **Si le CLIENT parle vraiment mais est filtré** → RMS et Max sont > seuils → Réduis les seuils
5. **Si Whisper hallucine** → RMS et Max sont < 300 → Augmente les seuils

---

## ✅ SOLUTION #3 : Filtrer les transcriptions courtes

**Fichier** : `config/audio_config.yaml` (ligne 75)

### **Principe :**
Les transcriptions très courtes (< 5 caractères) sont souvent des hallucinations.

### **Valeur actuelle :**
```yaml
min_length: 3  # Accepte "oui", "non", etc.
```

### **Si tu as beaucoup d'hallucinations courtes :**
```yaml
min_length: 8  # Plus strict, rejette les mots isolés
```

⚠️ **Attention** : Tu perdras les "oui", "non", "d'accord" courts.

---

## ✅ SOLUTION #4 : Ajouter des patterns de filtrage

**Fichier** : `config/audio_config.yaml` (lignes 78-97)

### **Principe :**
Bloquer les phrases typiques que Whisper invente.

### **Patterns actuels :**
```yaml
unwanted_patterns:
  - "Bonjour à tous, et bienvenue"
  - "bienvenue dans cette nouvelle vidéo"
  - "sous-titres réalisés par"
  # etc.
```

### **Comment ajouter tes propres patterns :**

1. **Repère les hallucinations récurrentes** dans tes logs :
   ```bash
   grep "CLIENT:" logs/kitt_transcription.log | grep -i "phrase inventée"
   ```

2. **Ajoute-les au fichier** :
   ```yaml
   unwanted_patterns:
     - "ta phrase hallucinée récurrente ici"
     - "une autre phrase inventée"
   ```

---

## ✅ SOLUTION #5 : Vérifier la qualité audio source

### **Pour le MICROPHONE (COMMERCIAL) :**

1. **Vérifie le niveau d'entrée** :
   - Préférences Système → Son → Entrée
   - Le niveau doit être à **60-80%** (pas trop fort, pas trop faible)

2. **Teste ton micro** :
   ```bash
   # Dans Python
   python
   >>> import pyaudio
   >>> p = pyaudio.PyAudio()
   >>> for i in range(p.get_device_count()):
   ...     print(p.get_device_info_by_index(i))
   ```

### **Pour le NAVIGATEUR (CLIENT - audio partagé) :**

1. **Assure-toi de partager l'ONGLET avec le son** :
   - Pas tout l'écran
   - Coche bien "Partager l'audio de l'onglet"

2. **Vérifie que l'audio du client est audible** :
   - Augmente le volume de l'onglet partagé
   - Évite les échos et bruits de fond

---

## 📊 RÉSUMÉ DES SOLUTIONS PAR PRIORITÉ

| Priorité | Solution | Efficacité | Difficulté |
|----------|----------|------------|------------|
| 🥇 **1** | Améliorer le prompt Whisper | ⭐⭐⭐⭐⭐ | Facile |
| 🥈 **2** | Augmenter seuils de silence CLIENT | ⭐⭐⭐⭐ | Facile |
| 🥉 **3** | Vérifier qualité audio source | ⭐⭐⭐⭐ | Moyen |
| 4 | Ajouter patterns de filtrage | ⭐⭐⭐ | Facile |
| 5 | Augmenter min_length | ⭐⭐ | Facile |

---

## 🧪 PROTOCOLE DE TEST

1. **Avant chaque changement** :
   - Note 3 exemples d'hallucinations récentes
   - Note les valeurs actuelles (seuils, prompt)

2. **Applique UN changement à la fois**

3. **Teste avec 3-5 appels réels**

4. **Compare les résultats** :
   ```bash
   # Compte les hallucinations
   grep "CLIENT:" logs/kitt_transcription.log | grep -i "bonjour à tous"
   ```

5. **Garde ce qui marche**, annule ce qui ne marche pas

---

## 🎯 CONFIGURATION RECOMMANDÉE

Si tu ne sais pas par où commencer, utilise cette config :

```yaml
# audio_config.yaml

silence_detection:
  browser:
    rms_threshold: 600.0
    min_amplitude: 1000
    min_audio_length: 8000

whisper:
  language: "fr"
  prompt: "Appel commercial pour [TON ENTREPRISE]. Commercial: [TON NOM]. Vocabulaire: budget, solution, produit, tarif, devis, entreprise, service, démonstration, fonctionnalités, intéressé, besoin."
  temperature: 0.0

transcription_filtering:
  min_length: 5
  unwanted_patterns:
    - "Bonjour à tous, et bienvenue"
    - "bienvenue dans cette nouvelle vidéo"
    # Ajoute tes hallucinations récurrentes ici
```

---

## 📞 BESOIN D'AIDE ?

Si tu as encore des hallucinations après avoir appliqué ces solutions :

1. **Active les logs DEBUG** pour voir les valeurs RMS réelles
2. **Envoie un exemple de log** avec l'hallucination
3. **On ajustera ensemble** les paramètres optimaux

---

**✅ En résumé : Le PROMPT détaillé est LA solution la plus efficace !**
