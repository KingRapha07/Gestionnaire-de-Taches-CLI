#  TaskCLI — Gestionnaire de tâches en ligne de commande

Application CLI en Python pour gérer des tâches avec persistance SQLite, priorités, échéances et catégories.

##  Fonctionnalités

-  **CRUD complet** : ajouter, lister, afficher, modifier, supprimer des tâches
-  **Priorités** : haute / moyenne / basse
-  **Échéances** : détection automatique des tâches en retard
-  **Catégories** : organisation par domaine (travail, perso, etc.)
-  **Recherche** plein texte sur le titre et la description
-  **Statistiques** : progression, répartition par catégorie
-  **Persistance SQLite** : base de données locale dans `~/.taskcli.db`
-  **Interface riche** via `rich` (tableaux, couleurs, panels)

##  Installation

```bash

cd taskcli

# Installer les dépendances
pip install -r requirements.txt

# (Optionnel) Rendre exécutable directement
chmod +x task_manager.py
ln -s $(pwd)/task_manager.py /usr/local/bin/task
```

##  Utilisation

```bash
# Ajouter une tâche
python task_manager.py add "Finir le rapport" -p haute -e 2025-06-01 -c travail
python task_manager.py add "Réviser les cours" -p moyenne -c études

# Lister les tâches
python task_manager.py list
python task_manager.py list --statut en_cours --sort date
python task_manager.py list --priorite haute

# Voir les détails d'une tâche
python task_manager.py show 1

# Marquer comme terminée
python task_manager.py done 1

# Modifier une tâche
python task_manager.py update 2 --titre "Nouveau titre" --priorite basse

# Rechercher
python task_manager.py search "rapport"

# Statistiques
python task_manager.py stats

# Supprimer
python task_manager.py delete 5
```

##  Structure du projet

```
taskcli/
├── task_manager.py   # Code principal (CLI + BDD + logique)
├── requirements.txt  # Dépendances Python
└── README.md
```

##  Technologies

| Outil | Rôle |
|-------|------|
| Python 3.10+ | Langage principal |
| SQLite3 | Base de données embarquée |
| argparse | Parsing des arguments CLI |
| rich | Affichage terminal enrichi |

##  Architecture

```
main()
  └─ init_db()           # Création de la table si inexistante
  └─ build_parser()      # Définition des sous-commandes argparse
  └─ dispatch commande
       ├─ add_task()     # INSERT INTO tasks
       ├─ list_tasks()   # SELECT avec filtres dynamiques
       ├─ show_task()    # SELECT par id
       ├─ update_task()  # UPDATE champs sélectifs
       ├─ complete_task()# UPDATE statut='terminée'
       ├─ delete_task()  # DELETE
       ├─ search_tasks() # SELECT LIKE
       └─ show_stats()   # COUNT + GROUP BY
```


