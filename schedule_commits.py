"""
Programa commits automaticos para hoy, cada ~30 minutos.
Ejecuta: python schedule_commits.py
Necesita: git configurado con user.name y user.email
"""

import random
import subprocess
import sys
import time
from datetime import datetime, timedelta

REPO = r"C:\Users\Alvaro\github-limpio\worldcup-2026"

COMMITS = [
    {
        "files": ["src/historical_data.py", "data/historical.db"],
        "messages": [
            "feat: add historical World Cup data (2014-2022)",
            "feat: add historical WC database with past editions",
            "feat: seed historical data for 2014, 2018, 2022",
        ],
        "desc": "historical_data.py + historical.db",
    },
    {
        "files": ["src/generate_report.py", "docs/index.html"],
        "messages": [
            "feat: add static HTML report with Plotly",
            "feat: generate comparison report as HTML",
            "feat: add Plotly report for WC comparison",
        ],
        "desc": "generate_report.py + docs/index.html",
    },
    {
        "files": ["dashboard/app.py", "requirements.txt"],
        "messages": [
            "feat: add Dash interactive dashboard",
            "feat: add Dash app for WC data exploration",
            "feat: add dashboard with Plotly Dash",
        ],
        "desc": "dashboard/app.py + requirements.txt",
    },
    {
        "files": [
            "api/server.py",
            "api/static/index.html",
        ],
        "messages": [
            "feat: add Flask REST API with frontend",
            "feat: add API + HTML frontend for WC data",
            "feat: add Flask API serving WC data as JSON",
        ],
        "desc": "api/ completo",
    },
    {
        "files": ["README.md"],
        "messages": [
            "chore: update README with dashboard links",
            "chore: update README with new project sections",
            "docs: update README with 3 visualization options",
        ],
        "desc": "README.md humanizado",
    },
]


def run(cmd, cwd=REPO):
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    return result.returncode == 0


def make_commit(commit_info):
    msg = random.choice(commit_info["messages"])

    for f in commit_info["files"]:
        run(f'git add "{f}"')

    ok = run(f'git commit -m "{msg}"')
    if ok:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"  [{now}] COMMIT OK: {msg}")
        print(f"            Archivos: {commit_info['desc']}")
    else:
        print(f"  [!] No hubo cambios para commitear ({commit_info['desc']})")
    return ok


def wait_until(target_time):
    now = datetime.now()
    diff = (target_time - now).total_seconds()
    if diff > 0:
        hrs = int(diff // 3600)
        mins = int((diff % 3600) // 60)
        print(f"  Esperando {hrs}h {mins}m hasta las {target_time.strftime('%H:%M')}...")
        while datetime.now() < target_time:
            time.sleep(10)


def main():
    now = datetime.now()
    print("=" * 55)
    print("  SCHEDULER DE COMMITS - worldcup-2026")
    print("=" * 55)
    print(f"  Ahora: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Repo:  {REPO}")
    print()

    # Empezar desde las 18:00 de hoy, o desde ahora si ya paso
    today_18 = now.replace(hour=18, minute=0, second=0, microsecond=0)
    if now < today_18:
        start = today_18
        print("  Iniciando a las 18:00 (quedan ~{} min)".format(
            int((start - now).total_seconds() // 60)
        ))
    else:
        # Si ya paso las 18:00, empezar en 5 min desde ahora
        start = now + timedelta(minutes=5)
        print(f"  Ya paso las 18:00, empiezo a las {start.strftime('%H:%M')}")
    print()

    # Slots cada 30 min con variacion natural (0-5 min)
    schedule = []
    for i, commit in enumerate(COMMITS):
        jitter = timedelta(minutes=random.randint(0, 5))
        slot = start + timedelta(minutes=30 * i) + jitter
        schedule.append((slot, commit))

    print("  Cronograma:")
    for slot, commit in schedule:
        print(f"    {slot.strftime('%H:%M')} - {commit['desc']}")
    print()

    # Ejecutar cada commit en su momento
    for i, (slot, commit) in enumerate(schedule):
        print(f"\n--- Commit {i+1}/{len(COMMITS)} ---")
        wait_until(slot)
        make_commit(commit)

        # Pausa entre commits (1-3 min)
        if i < len(COMMITS) - 1:
            pause = random.randint(60, 180)
            print(f"  Pausa de {pause // 60}m {pause % 60}s antes del siguiente...")

    print("\n" + "=" * 55)
    print("  TODOS LOS COMMITS REALIZADOS")
    print("=" * 55)
    print("  Revisa con: git log --oneline -6")


if __name__ == "__main__":
    main()
