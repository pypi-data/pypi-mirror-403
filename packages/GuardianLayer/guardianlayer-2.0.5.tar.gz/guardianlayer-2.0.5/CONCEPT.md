# GuardianLayer : La Vision - Meta-Cognition pour Agents IA

Ce document résume le concept innovant derrière **GuardianLayer** : transformer une simple surveillance de boucle en une véritable couche de **conscience de soi (Self-Awareness)** pour les agents autonomes.

## 🧠 Le Concept : Meta-Cognition

La plupart des agents IA fonctionnent en "boucle ouverte". GuardianLayer ferme cette boucle en ajoutant une couche de réflexion entre le "cerveau" (LLM) et ses "mains" (Outils/MCP).

### 1. Surveillance Multi-Niveaux (LoopDetector)
Contrairement aux garde-fous classiques qui comptent simplement les itérations (A-A-A), GuardianLayer comprend la structure des cycles :
- **Répétition Immédiate** : A → A
- **Cycles Courts** : A → B → A
- **Complexité de Graphe** : A → B → C → A

### 2. Conscience des Outils (ReflexionLayer)
GuardianLayer devient un **Middleware pour MCP (Model Context Protocol)** :
- **Ingestion Dynamique** : Il demande aux serveurs MCP leurs schémas (`list_tools`) et les garde en cache.
- **Validation en Amont** : Il vérifie les arguments *avant* de solliciter les outils, économisant temps et ressources.

### 3. Apprentissage Long-Terme (Experience Layer)
C'est la pièce maîtresse pour transformer l'IA :
- **Journal d'Incidents** : Mémorise les échecs récurrents sur plusieurs jours/sessions.
- **Auto-Correction du Prompt** : Injecte dynamiquement des règles de sécurité dans le prompt de l'IA basées sur ses erreurs passées ("*Attention, tu as échoué 5 fois sur cet outil cette semaine en oubliant le paramètre X*").
- **Awareness Statistique** : Calcule un score de fiabilité pour chaque outil.

## 🚀 Pourquoi c'est une "Killer Feature" ?

- **Agnostique** : Fonctionne avec n'importe quel LLM et n'importe quel serveur MCP.
- **Léger & Déterministe** : C'est un script (système expert) et non une autre IA, garantissant rapidité et prédictibilité.
- **Fiabilité Industrielle** : Rend les agents IA assez robustes pour la production en évitant les "hallucinations d'outils" et les boucles infinies coûteuses.

## 🛠️ Futur Roadmap & Améliorations Techniques

### ⚡ Performance & Flexibilité
- **Optimisation par Hachage** : Remplacer la comparaison JSON lourde par des empreintes numériques (Hash) pour une détection de boucle instantanée.
- **Registre de Schémas Universel** : Passer d'outils "en dur" à un annuaire dynamique où n'importe quel service (MCP ou autre) peut s'inscrire.

### 🛡️ Résilience & Fiabilité (Stability)
- **Circuit Breaker (Disjoncteur)** : Bloquer préventivement les outils en panne pour éviter que l'IA ne s'épuise sur des erreurs réseau.
- **Tests Automatisés (Zero-Regression)** : Mise en place d'une batterie de tests (`pytest`) simulant des "IA folles" pour valider la solidité du bouclier en quelques millisecondes.

### 📊 Métriques & Preuve de Valeur
- **Dashboard de Sécurité** : Suivi en temps réel des boucles évitées, des tokens sauvés et de la fiabilité par outil.
- **Observabilité** : Comprendre exactement pourquoi un agent échoue sur un outil spécifique via des logs structurés.

---
*Note: GuardianLayer ne bloque pas forcément l'IA, il lui murmure qu'elle se trompe pour qu'elle puisse se corriger elle-même.*
