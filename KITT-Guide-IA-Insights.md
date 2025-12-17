# KITT - Guide Complet des Indicateurs Sales

**Guide pour Intelligence Artificielle - Version Optimisée**

---

## SOMMAIRE

1. [Indicateurs Temps Réel (Pendant l'Appel)](#1-indicateurs-temps-réel)
2. [Indicateurs Post-Appel (Analyse Finale)](#2-indicateurs-post-appel)
3. [Métriques d'Équipe (Manager)](#3-métriques-équipe)
4. [Structures de Vente](#4-structures-de-vente)
5. [Guide d'Utilisation](#5-guide-utilisation)
6. [Corrélations et Data Insights](#6-corrélations)

---

## 1. INDICATEURS TEMPS RÉEL

**Contexte** : Ces indicateurs s'affichent en direct pendant l'appel pour guider le commercial en temps réel.

### 1.1 Talking Ratio (Ratio de Parole)

**Définition** : Pourcentage du temps où le commercial parle vs le prospect écoute.

**Formule** :
```
Talking Ratio = (Temps de parole commercial / Temps total appel) × 100
```

**Interprétation** :
- **Idéal** : 40-45% (le commercial écoute 55-60% du temps)
- **Acceptable** : 45-55%
- **Critique** : >60% (monologue, pas de découverte)

**KITT Alert** : Si le ratio dépasse 55%, KITT alerte : "⚠️ Vous parlez trop - laissez-les s'exprimer"

---

### 1.2 Questions Ouvertes

**Définition** : Nombre de questions ouvertes posées (Comment, Pourquoi, Quoi, Quel, Décrivez-moi).

**Formule** :
```
Questions Ouvertes = Count(questions débutant par mots-clés ouverts)
```

**Benchmarks** :
- **Excellent** : 8-12 questions (appel 30 min)
- **Bon** : 5-7 questions
- **Insuffisant** : <5 questions

**Exemples détectés par KITT** :
- "Comment gérez-vous actuellement..."
- "Pourquoi avez-vous choisi cette solution ?"
- "Quels sont vos principaux défis ?"
- "Décrivez-moi votre processus actuel"

**Data KITT** : Commerciaux avec +7 questions ouvertes par call → Score moyen 17/20 vs 13/20 pour les autres (+30%)

---

### 1.3 Temps par Phase de l'Appel

**Définition** : Répartition du temps entre Discovery, Pitch et Closing.

**Distribution idéale (appel discovery 30min)** :
- **Discovery** : 40-50% (12-15 min)
- **Pitch** : 30-40% (9-12 min)
- **Closing** : 10-20% (3-6 min)

**Anti-pattern** : Discovery <30% = Pitch trop rapide sans comprendre le besoin = Taux de closing -25%

---

### 1.4 Objections Détectées

**Définition** : KITT détecte les objections en temps réel et évalue la gestion.

**Objections fréquentes trackées** :
- **Prix** : "C'est trop cher", "On n'a pas le budget"
- **Timing** : "Pas le bon moment", "On verra l'année prochaine"
- **Concurrent** : "On a déjà un outil", "On travaille avec X"
- **Décision** : "Je dois en parler à...", "Je réfléchis"

**KITT Coaching** : Quand une objection est détectée, KITT suggère : "🎯 Objection prix détectée - Reformulez puis parlez ROI"

---

## 2. INDICATEURS POST-APPEL

**Contexte** : Ces métriques sont calculées après l'appel pour une analyse complète de la performance.

### 2.1 Score Global (/100)

**Définition** : Note globale de performance basée sur 5 critères pondérés.

**Formule** :
```
Score = (Discovery × 25%) + (Questions × 20%) + (Objections × 20%) + (Pitch × 15%) + (Closing × 20%)
```

**Échelle de notation** :
- **90-100** : Excellent (deal hautement probable)
- **75-89** : Très bon (bon momentum commercial)
- **60-74** : Correct (des améliorations possibles)
- **45-59** : Faible (revoir la méthodologie)
- **<45** : Critique (coaching urgent requis)

**Objectif Équipe** : 80% des calls >75/100 → Équipe performante

---

### 2.2 Phase Discovery (/100)

**Définition** : Qualité de la phase de découverte et compréhension du besoin client.

**Critères évalués (chacun sur 20 points)** :
1. **Contexte actuel** : Outils utilisés, process, organisation
2. **Pain points** : Problèmes identifiés et quantifiés (temps perdu, coût)
3. **Objectifs business** : KPIs visés, résultats attendus
4. **Décideurs & Budget** : Qui décide, budget alloué, timeline
5. **Urgence** : Pourquoi maintenant, événement déclencheur

**Timing optimal** : Discovery = 40-50% du temps total de l'appel

---

### 2.3 Questions Ouvertes (/100)

**Définition** : Évaluation de la quantité ET qualité des questions posées.

**Formule** :
```
Score Questions = (Quantité × 50%) + (Qualité × 50%)
```

**Quantité (sur 50)** :
- 0-3 questions = 10 pts
- 4-6 questions = 30 pts
- 7-9 questions = 45 pts
- 10+ questions = 50 pts

**Qualité (sur 50)** :
- Pertinence par rapport au contexte (+10)
- Creusement (follow-up questions) (+15)
- Écoute active (reformulation) (+15)
- Découverte profonde (SPIN, MEDDIC) (+10)

---

### 2.4 Gestion des Objections (/100)

**Définition** : Pourcentage d'objections bien gérées selon la méthode en 4 étapes.

**Formule** :
```
Score Objections = (Objections bien gérées / Objections totales) × 100
```

**Méthode 4 étapes (chaque étape = 25 pts)** :
1. **Reformulation** : "Si je comprends bien, vous trouvez que..."
2. **Empathie** : "Je comprends cette préoccupation..."
3. **Argument de valeur** : ROI chiffré, cas client, bénéfice concret
4. **Validation** : "Est-ce que cela répond à votre préoccupation ?"

---

### 2.5 Qualité du Pitch (/100)

**Définition** : Pertinence et personnalisation de la présentation solution.

**Critères (chacun sur 20 pts)** :
- **Personnalisation** : Lien direct avec pain points évoqués
- **ROI quantifié** : Gains chiffrés (temps, argent, productivité)
- **Social proof** : Cas clients similaires, témoignages
- **Différenciation** : Avantages vs concurrence mentionnée
- **Démo/Preuve** : Screenshot, vidéo, ou proposition de démo

---

### 2.6 Closing / Next Steps (/100)

**Définition** : Capacité à conclure avec un engagement concret du prospect.

**Évaluation** : Basée sur la clarté et la faisabilité du next step proposé.

---

### 2.7 Next Steps Planifiés (Ratio)

**Définition** : Pourcentage d'appels se terminant avec une action future concrète et datée.

**Formule** :
```
Next Steps Ratio = (Calls avec next step / Total calls) × 100
```

**Exemples de Next Steps valides** :
- RDV démo agendé (date + heure confirmées)
- Envoi proposition sous 48h avec rappel prévu
- Trial démarré avec point de suivi J+7
- Appel décideur planifié
- Démo technique avec équipe IT

**Objectif** : 80% minimum. Un appel sans next step = opportunité qui meurt.

---

## 3. MÉTRIQUES ÉQUIPE

**Contexte** : Vue manager pour le pilotage de l'équipe commerciale.

### 3.1 Streak Équipe

**Définition** : Nombre de jours consécutifs où l'équipe atteint son objectif quotidien.

**Formule** :
```
Streak = Count(jours consécutifs avec objectif atteint)
```

**Exemple concret** :
- Objectif équipe : 15 calls >75/100 par jour
- Lundi : 16 calls ✓ → Streak = 1
- Mardi : 18 calls ✓ → Streak = 2
- Mercredi : 14 calls ✗ → Streak RESET à 0
- Jeudi : 17 calls ✓ → Streak = 1 (redémarre)

---

### 3.2 Progression vs Objectifs Mensuels

**Définition** : Suivi temps réel de 4 métriques clés configurables par le manager.

**Métriques trackées (modifiables)** :
- **RDV qualifiés** : 15/20 (75%) - découvertes confirmées
- **Appels du mois** : 950/1200 (79%) - volume d'activité
- **Deals / Ventes** : 3/5 (60%) - objectif signature
- **Next Step Ratio** : 65%/80% - qualité de closing

---

### 3.3 Leaderboard (Classement Équipe)

**Définition** : Classement des commerciaux basé sur score moyen mensuel (scrollable jusqu'à 20 membres).

**Informations affichées par membre** :
- Score moyen sur 30 jours (/100)
- Streak personnel actuel (jours)
- Évolution vs mois dernier (+3, -2, etc.)
- Badges : 🏆 Top Performer, 🔥 Streak Master, 🚀 Meilleure Progression

**Gamification** : Crée émulation saine + identifie top performers pour partage best practices

---

### 3.4 Compétences Équipe (Heatmap)

**Définition** : Vue d'ensemble des forces/faiblesses de l'équipe par compétence.

**5 Compétences trackées** :
- **Questions ouvertes** : 65% (↑ +2% vs mois dernier)
- **Gestion objections** : 52% (↓ -3%) - FOCUS PRIORITAIRE
- **Pitch** : 72% (↑ +4%)
- **Closing** : 81% (↑ +6%) - EXCELLENT
- **Next Steps planifiés** : 68% (↑ +3%)

---

### 3.5 Défis de la Semaine (Éditable)

**Définition** : 3 challenges hebdomadaires définis par le manager pour l'équipe.

**Exemples de défis** :
- **Défi 1** : Réduire Talking Ratio - 68% → 60% (12/15 personnes ont atteint)
- **Défi 2** : 30 questions ouvertes cette semaine - Plus que 8 ! (22/30)
- **Défi 3** : 80% Next Steps - Encore +15% (65% actuel)

**Note Manager** : Les défis sont éditables chaque semaine pour s'adapter aux priorités business

---

## 4. STRUCTURES DE VENTE

**Contexte** : KITT détecte automatiquement l'application des méthodologies de vente reconnues.

### 4.1 SPIN Selling

**Créateur** : Neil Rackham

**Description** : Méthodologie pour découverte approfondie. KITT détecte les 4 types de questions.

**Les 4 composantes** :

#### S - Situation
**Objectif** : Comprendre le contexte actuel

**Exemples de questions** :
- "Quel outil utilisez-vous actuellement ?"
- "Depuis combien de temps ?"
- "Combien d'utilisateurs ?"

---

#### P - Problème
**Objectif** : Identifier les difficultés

**Exemples de questions** :
- "Quelles sont les limites de votre outil actuel ?"
- "Qu'est-ce qui vous frustre ?"

---

#### I - Implication
**Objectif** : Creuser les conséquences

**Exemples de questions** :
- "Combien de temps perdez-vous par semaine ?"
- "Quel impact sur vos résultats ?"
- "Et si ça continue ?"

---

#### N - Need-Payoff
**Objectif** : Faire verbaliser la valeur de la solution

**Exemples de questions** :
- "Si vous économisiez 5h/semaine, que feriez-vous ?"
- "Quel serait l'impact ?"

---

### 4.2 MEDDIC (Qualification Complexe)

**Description** : Framework de qualification pour deals complexes B2B. KITT vérifie que les 6 critères sont couverts.

**Les 6 composantes** :

#### M - Metrics
**Définition** : ROI quantifié, KPIs attendus

**Questions clés** :
- "Quels sont vos objectifs chiffrés ?"
- "Quel ROI attendez-vous ?"

---

#### E - Economic Buyer
**Définition** : Décideur final identifié

**Questions clés** :
- "Qui valide le budget final ?"
- "Puis-je échanger avec lui/elle ?"

---

#### D - Decision Criteria
**Définition** : Critères de choix clarifiés

**Questions clés** :
- "Sur quels critères allez-vous choisir ?"
- "Qu'est-ce qui est rédhibitoire ?"

---

#### D - Decision Process
**Définition** : Processus de validation connu

**Questions clés** :
- "Quelles sont les étapes de validation ?"
- "Timeline ?"

---

#### I - Identify Pain
**Définition** : Douleur identifiée et urgente

**Questions clés** :
- "Quel est votre problème #1 aujourd'hui ?"
- "Pourquoi maintenant ?"

---

#### C - Champion
**Définition** : Ambassadeur interne identifié

**Questions clés** :
- "Qui va nous aider en interne ?"
- "Qui croit au projet ?"

---

### 4.3 BANT (Qualification Rapide)

**Origine** : Framework IBM classique

**Description** : Qualification rapide en 4 critères simples.

**Les 4 composantes** :

#### B - Budget
**Définition** : Budget alloué ou disponible

**Questions clés** :
- "Avez-vous un budget prévu ?"
- "Dans quelle fourchette ?"

---

#### A - Authority
**Définition** : Interlocuteur a le pouvoir de décision

**Questions clés** :
- "Êtes-vous décisionnaire ?"
- "Qui d'autre doit valider ?"

---

#### N - Need
**Définition** : Besoin réel identifié

**Questions clés** :
- "Quel problème cherchez-vous à résoudre ?"
- "Depuis quand ?"

---

#### T - Timeline
**Définition** : Échéance de décision claire

**Questions clés** :
- "Quand souhaitez-vous démarrer ?"
- "Date limite de décision ?"

---

### 4.4 SPICED (Approche Moderne)

**Origine** : Winning by Design

**Description** : Framework moderne, plus centré prospect que BANT.

**Les 6 composantes** :
- **S - Situation** : Comprendre le contexte actuel en profondeur
- **P - Pain** : Identifier et quantifier la douleur
- **I - Impact** : Mesurer les conséquences du problème
- **C - Critical Event** : Événement déclencheur d'urgence
- **E - Economic Buyer** : Identifier le décideur budget
- **D - Decision Criteria** : Critères de choix finaux

---

## 5. GUIDE UTILISATION

### Pour les Commerciaux

**Avant l'appel** :
- Préparez vos questions SPIN ou MEDDIC selon le type d'appel

**Pendant l'appel** :
- Suivez les alertes KITT (talking ratio, questions, objections) pour ajuster en temps réel

**Après l'appel** :
- Analysez votre score détaillé
- Identifiez 1-2 axes d'amélioration maximum

**Chaque semaine** :
- Comparez vos performances vs semaine N-1
- Objectif : +2-3 points/semaine

**Chaque mois** :
- Identifiez votre compétence la plus faible
- Travaillez-la spécifiquement

---

### Pour les Managers

**Quotidien** :
- Vérifiez le streak équipe
- Si cassé → identifier la cause (membre, volume)

**Hebdomadaire** :
- 1-on-1 avec membres sous-performants
- Utilisez insights KITT pour coaching ciblé

**Mensuel** :
- Analysez heatmap compétences
- Organisez formations sur les skills <60%

**Best Practice** :
- Créez une bibliothèque "Golden Calls" (18+/20)
- Accessible à toute l'équipe

---

## 6. CORRÉLATIONS ET DATA INSIGHTS

**Source** : Basé sur l'analyse de milliers d'appels par KITT

### Corrélations Statistiques Clés

| Indicateur | Impact sur Closing |
|------------|-------------------|
| **Talking Ratio <45%** | +22% de taux de closing |
| **7+ Questions Ouvertes** | +15% de taux de closing, Score moyen 17/20 vs 13/20 |
| **Objections bien gérées >80%** | +18% de taux de closing |
| **Next Step défini** | +40% de chances de closer le deal dans les 30 jours |
| **Discovery >40% du temps** | +25% de taux de closing |
| **Streak >7 jours** | Score moyen +8 points vs baseline |
| **Application SPIN complet** | +30% de taux de closing vs discovery non structurée |
| **MEDDIC complété** | +45% de taux de closing sur deals complexes |

---

## CONCLUSION

Ces indicateurs sont des leviers d'amélioration concrets et actionnables. KITT analyse chaque appel en temps réel pour fournir des insights précis au moment opportun.

**Principes clés** :
- Utiliser ces métriques comme une boussole, pas comme un jugement
- Chaque commercial a des forces et faiblesses différentes
- KITT aide à identifier les axes d'amélioration et à progresser continuellement
- L'adoption des méthodologies de vente (SPIN, MEDDIC, BANT, SPICED) combinée au coaching temps réel de KITT maximise les performances commerciales

---

**Pour toute question, contactez votre Customer Success Manager**

*KITT - Version 2.0 - Décembre 2025*
