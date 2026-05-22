#!/usr/bin/env python3
"""
TaskCLI - Gestionnaire de tâches en ligne de commande
Description: Application CLI pour gérer des tâches avec SQLite, priorités et échéances.
"""

import argparse
import sqlite3
import os
import sys
from datetime import datetime, date
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

 
#  Configuration

DB_PATH = os.path.join(os.path.expanduser("~"), ".taskcli.db")
console = Console()

PRIORITIES = {"haute": 1, "moyenne": 2, "basse": 3}
PRIORITY_COLORS = {1: "red", 2: "yellow", 3: "green"}
PRIORITY_LABELS = {1: "🔴 Haute", 2: "🟡 Moyenne", 3: "🟢 Basse"}
STATUS_COLORS = {"en_cours": "cyan", "terminée": "green", "annulée": "dim"}
STATUS_LABELS = {"en_cours": "⏳ En cours", "terminée": "✅ Terminée", "annulée": "❌ Annulée"}


 
#  Base de données

def get_connection():
    """Retourne une connexion SQLite avec row_factory pour accès par colonne."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crée la table des tâches si elle n'existe pas."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                titre       TEXT    NOT NULL,
                description TEXT    DEFAULT '',
                priorite    INTEGER DEFAULT 2,       -- 1=haute, 2=moyenne, 3=basse
                statut      TEXT    DEFAULT 'en_cours',
                echeance    TEXT    DEFAULT NULL,    -- format YYYY-MM-DD
                categorie   TEXT    DEFAULT 'général',
                cree_le     TEXT    DEFAULT (date('now'))
            )
        """)
        conn.commit()

 
#  CRUD

def add_task(titre, description="", priorite="moyenne", echeance=None, categorie="général"):
    """Ajoute une nouvelle tâche."""
    p = PRIORITIES.get(priorite.lower(), 2)
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (titre, description, priorite, echeance, categorie) VALUES (?, ?, ?, ?, ?)",
            (titre, description, p, echeance, categorie)
        )
        conn.commit()
        task_id = cursor.lastrowid
    console.print(f"[green]✅ Tâche #{task_id} ajoutée :[/] [bold]{titre}[/]")


def list_tasks(statut=None, priorite=None, categorie=None, sort_by="priorite"):
    """Affiche toutes les tâches sous forme de tableau."""
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if statut:
        query += " AND statut = ?"
        params.append(statut)
    if priorite:
        query += " AND priorite = ?"
        params.append(PRIORITIES.get(priorite.lower(), 2))
    if categorie:
        query += " AND categorie = ?"
        params.append(categorie)

    sort_map = {"priorite": "priorite", "date": "echeance", "id": "id", "creation": "cree_le"}
    order_col = sort_map.get(sort_by, "priorite")
    query += f" ORDER BY {order_col} ASC"

    with get_connection() as conn:
        tasks = conn.execute(query, params).fetchall()

    if not tasks:
        console.print(Panel("[dim]Aucune tâche trouvée.[/]", border_style="dim"))
        return

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white on grey23",
        border_style="grey50",
        expand=True
    )
    table.add_column("ID", style="dim", width=4)
    table.add_column("Titre", min_width=20)
    table.add_column("Priorité", width=13)
    table.add_column("Statut", width=14)
    table.add_column("Catégorie", width=12)
    table.add_column("Échéance", width=12)

    today = date.today()
    for t in tasks:
        ech = t["echeance"] or "-"
        ech_color = "white"
        if t["echeance"]:
            d = date.fromisoformat(t["echeance"])
            if d < today and t["statut"] == "en_cours":
                ech_color = "red"
                ech = f"⚠ {ech}"
            elif d == today:
                ech_color = "yellow"

        table.add_row(
            str(t["id"]),
            t["titre"],
            PRIORITY_LABELS.get(t["priorite"], "?"),
            f"[{STATUS_COLORS[t['statut']]}]{STATUS_LABELS[t['statut']]}[/]",
            t["categorie"],
            f"[{ech_color}]{ech}[/]"
        )

    total = len(tasks)
    done = sum(1 for t in tasks if t["statut"] == "terminée")
    console.print(table)
    console.print(f"[dim]{total} tâche(s) · {done} terminée(s) · {total - done} en cours[/]\n")


def show_task(task_id):
    """Affiche les détails d'une tâche."""
    with get_connection() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if not task:
        console.print(f"[red]Tâche #{task_id} introuvable.[/]")
        return

    p_color = PRIORITY_COLORS.get(task["priorite"], "white")
    text = Text()
    text.append(f"\nTitre      : ", style="dim")
    text.append(task["titre"], style="bold")
    text.append(f"\nDescription: ", style="dim")
    text.append(task["description"] or "(aucune)")
    text.append(f"\nPriorité   : ", style="dim")
    text.append(PRIORITY_LABELS.get(task["priorite"], "?"), style=p_color)
    text.append(f"\nStatut     : ", style="dim")
    text.append(STATUS_LABELS.get(task["statut"], task["statut"]))
    text.append(f"\nCatégorie  : ", style="dim")
    text.append(task["categorie"])
    text.append(f"\nÉchéance   : ", style="dim")
    text.append(task["echeance"] or "Aucune")
    text.append(f"\nCréée le   : ", style="dim")
    text.append(task["cree_le"])

    console.print(Panel(text, title=f"[bold]Tâche #{task_id}[/]", border_style=p_color))


def update_task(task_id, titre=None, description=None, priorite=None, echeance=None, categorie=None):
    """Met à jour les champs d'une tâche."""
    fields, params = [], []
    if titre:
        fields.append("titre = ?"); params.append(titre)
    if description is not None:
        fields.append("description = ?"); params.append(description)
    if priorite:
        fields.append("priorite = ?"); params.append(PRIORITIES.get(priorite.lower(), 2))
    if echeance:
        fields.append("echeance = ?"); params.append(echeance)
    if categorie:
        fields.append("categorie = ?"); params.append(categorie)

    if not fields:
        console.print("[yellow]Aucune modification spécifiée.[/]")
        return

    params.append(task_id)
    with get_connection() as conn:
        conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    console.print(f"[green]✅ Tâche #{task_id} mise à jour.[/]")


def complete_task(task_id):
    """Marque une tâche comme terminée."""
    with get_connection() as conn:
        conn.execute("UPDATE tasks SET statut = 'terminée' WHERE id = ?", (task_id,))
        conn.commit()
    console.print(f"[green]✅ Tâche #{task_id} marquée comme terminée.[/]")


def cancel_task(task_id):
    """Annule une tâche."""
    with get_connection() as conn:
        conn.execute("UPDATE tasks SET statut = 'annulée' WHERE id = ?", (task_id,))
        conn.commit()
    console.print(f"[yellow]❌ Tâche #{task_id} annulée.[/]")


def delete_task(task_id):
    """Supprime définitivement une tâche."""
    with get_connection() as conn:
        rows = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,)).rowcount
        conn.commit()
    if rows:
        console.print(f"[red]🗑  Tâche #{task_id} supprimée.[/]")
    else:
        console.print(f"[red]Tâche #{task_id} introuvable.[/]")


def show_stats():
    """Affiche des statistiques sur les tâches."""
    with get_connection() as conn:
        total     = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        en_cours  = conn.execute("SELECT COUNT(*) FROM tasks WHERE statut='en_cours'").fetchone()[0]
        terminees = conn.execute("SELECT COUNT(*) FROM tasks WHERE statut='terminée'").fetchone()[0]
        annulees  = conn.execute("SELECT COUNT(*) FROM tasks WHERE statut='annulée'").fetchone()[0]
        en_retard = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE statut='en_cours' AND echeance < date('now')"
        ).fetchone()[0]
        par_cat   = conn.execute(
            "SELECT categorie, COUNT(*) as n FROM tasks GROUP BY categorie ORDER BY n DESC"
        ).fetchall()

    pct = int(terminees / total * 100) if total else 0
    bar_fill = int(pct / 5)
    bar = "█" * bar_fill + "░" * (20 - bar_fill)

    console.print(Panel(
        f"[bold white]Progression : [{bar}] {pct}%[/]\n\n"
        f"  Total     : [bold]{total}[/]\n"
        f"  En cours  : [cyan]{en_cours}[/]\n"
        f"  Terminées : [green]{terminees}[/]\n"
        f"  Annulées  : [dim]{annulees}[/]\n"
        f"  En retard : [red]{en_retard}[/]\n",
        title="[bold]📊 Statistiques[/]",
        border_style="blue"
    ))

    if par_cat:
        console.print("[bold]Par catégorie :[/]")
        for row in par_cat:
            console.print(f"  [dim]·[/] {row['categorie']} : [bold]{row['n']}[/]")
    console.print()


def search_tasks(keyword):
    """Recherche des tâches par mot-clé dans le titre ou la description."""
    with get_connection() as conn:
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE titre LIKE ? OR description LIKE ? ORDER BY priorite ASC",
            (f"%{keyword}%", f"%{keyword}%")
        ).fetchall()

    if not tasks:
        console.print(f"[dim]Aucun résultat pour « {keyword} ».[/]")
        return

    console.print(f"[bold]{len(tasks)}[/] résultat(s) pour « [bold]{keyword}[/] » :")
    for t in tasks:
        p_color = PRIORITY_COLORS.get(t["priorite"], "white")
        console.print(
            f"  [dim]#{t['id']}[/] [{p_color}]●[/] {t['titre']} "
            f"[dim]({t['statut']})[/]"
        )
    console.print()

 
#  CLI — parsing des arguments

def build_parser():
    parser = argparse.ArgumentParser(
        prog="task",
        description="TaskCLI – Gestionnaire de tâches en ligne de commande",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  task add "Finir le rapport" -p haute -e 2025-06-01 -c travail
  task list
  task list --statut en_cours --sort date
  task show 3
  task done 3
  task update 2 --titre "Nouveau titre" --priorite basse
  task delete 5
  task search "rapport"
  task stats
        """
    )
    sub = parser.add_subparsers(dest="commande")

    # add
    p_add = sub.add_parser("add", help="Ajouter une tâche")
    p_add.add_argument("titre", help="Titre de la tâche")
    p_add.add_argument("-d", "--description", default="", help="Description détaillée")
    p_add.add_argument("-p", "--priorite", choices=["haute","moyenne","basse"], default="moyenne")
    p_add.add_argument("-e", "--echeance", metavar="YYYY-MM-DD", help="Date d'échéance")
    p_add.add_argument("-c", "--categorie", default="général")

    # list
    p_list = sub.add_parser("list", help="Lister les tâches")
    p_list.add_argument("--statut", choices=["en_cours","terminée","annulée"])
    p_list.add_argument("--priorite", choices=["haute","moyenne","basse"])
    p_list.add_argument("--categorie")
    p_list.add_argument("--sort", choices=["priorite","date","id","creation"], default="priorite")

    # show
    p_show = sub.add_parser("show", help="Détails d'une tâche")
    p_show.add_argument("id", type=int)

    # done
    p_done = sub.add_parser("done", help="Marquer une tâche comme terminée")
    p_done.add_argument("id", type=int)

    # cancel
    p_cancel = sub.add_parser("cancel", help="Annuler une tâche")
    p_cancel.add_argument("id", type=int)

    # delete
    p_del = sub.add_parser("delete", help="Supprimer une tâche")
    p_del.add_argument("id", type=int)

    # update
    p_upd = sub.add_parser("update", help="Modifier une tâche")
    p_upd.add_argument("id", type=int)
    p_upd.add_argument("--titre")
    p_upd.add_argument("--description")
    p_upd.add_argument("--priorite", choices=["haute","moyenne","basse"])
    p_upd.add_argument("--echeance", metavar="YYYY-MM-DD")
    p_upd.add_argument("--categorie")

    # search
    p_search = sub.add_parser("search", help="Rechercher une tâche")
    p_search.add_argument("mot", help="Mot-clé à rechercher")

    # stats
    sub.add_parser("stats", help="Statistiques")

    return parser


def main():
    init_db()
    parser = build_parser()
    args = parser.parse_args()

    if not args.commande:
        console.print(Panel(
            "[bold]TaskCLI[/] – Gestionnaire de tâches\n\n"
            "  [cyan]task add[/] [dim]\"titre\"[/]    Ajouter une tâche\n"
            "  [cyan]task list[/]          Lister toutes les tâches\n"
            "  [cyan]task show[/] [dim]<id>[/]      Détails d'une tâche\n"
            "  [cyan]task done[/] [dim]<id>[/]      Marquer comme terminée\n"
            "  [cyan]task update[/] [dim]<id>[/]    Modifier une tâche\n"
            "  [cyan]task delete[/] [dim]<id>[/]    Supprimer une tâche\n"
            "  [cyan]task search[/] [dim]<mot>[/]   Rechercher\n"
            "  [cyan]task stats[/]         Statistiques\n\n"
            "  [dim]task --help  pour plus d'options[/]",
            title="[bold blue]📋 TaskCLI[/]",
            border_style="blue"
        ))
        return

    match args.commande:
        case "add":
            add_task(args.titre, args.description, args.priorite, args.echeance, args.categorie)
        case "list":
            list_tasks(args.statut, args.priorite, args.categorie, args.sort)
        case "show":
            show_task(args.id)
        case "done":
            complete_task(args.id)
        case "cancel":
            cancel_task(args.id)
        case "delete":
            delete_task(args.id)
        case "update":
            update_task(args.id, args.titre, args.description, args.priorite, args.echeance, args.categorie)
        case "search":
            search_tasks(args.mot)
        case "stats":
            show_stats()


if __name__ == "__main__":
    main()
