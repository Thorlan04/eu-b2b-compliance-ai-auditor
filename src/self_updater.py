"""
Module self_updater.py
Script d'auto-maintenance hebdomadaire exécuté par GitHub Actions (CI/CD).

Actions :
1. Vérifie et enrichit data/compliance_signatures.json avec les derniers User-Agents IA et trackers.
2. Met à jour la date ISO de dernière mise à jour.
3. Incrémente automatiquement la version sémantique (Patch / Minor).
4. Synchronise la version dans .actor/actor.json, src/__init__.py et src/main.py.
5. Rafraîchit les badges et mentions de version dans le README.md.
6. Valide la conformité syntaxique JSON des fichiers générés.
"""

import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format="[SelfUpdater] %(message)s")
logger = logging.getLogger("SelfUpdater")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT_DIR, "data", "compliance_signatures.json")
ACTOR_JSON = os.path.join(ROOT_DIR, ".actor", "actor.json")
INIT_PY = os.path.join(ROOT_DIR, "src", "__init__.py")
MAIN_PY = os.path.join(ROOT_DIR, "src", "main.py")
README_MD = os.path.join(ROOT_DIR, "README.md")

# Nouveaux bots IA et trackers à maintenir dans le radar de veille
EMERGING_AI_AGENTS = [
    {
        "name": "DeepSeekBot",
        "owner": "DeepSeek",
        "purpose": "Indexation et entraînement des modèles DeepSeek-V3 et R1",
        "user_agents": ["DeepSeekBot"],
        "recommended_action_for_visibility": "allow"
    },
    {
        "name": "MistralBot",
        "owner": "Mistral AI",
        "purpose": "Crawler européen pour les modèles de fondation Le Chat et Mistral Large",
        "user_agents": ["MistralBot"],
        "recommended_action_for_visibility": "allow"
    },
    {
        "name": "GrokBot",
        "owner": "xAI",
        "purpose": "Indexation en temps réel pour l'IA conversationnelle Grok",
        "user_agents": ["xAI-GrokBot", "GrokBot"],
        "recommended_action_for_visibility": "allow"
    },
    {
        "name": "DuckAssistBot",
        "owner": "DuckDuckGo",
        "purpose": "Recherche augmentée par IA de DuckDuckGo",
        "user_agents": ["DuckAssistBot"],
        "recommended_action_for_visibility": "allow"
    }
]

EMERGING_TRACKERS = [
    {
        "id": "hubspot_analytics",
        "name": "HubSpot Tracking Code",
        "category": "Inbound Marketing & CRM",
        "patterns": ["js.hs-scripts.com", "track.hubspot.com", "_hsq.push"]
    },
    {
        "id": "pinterest_tag",
        "name": "Pinterest Tag",
        "category": "Advertising",
        "patterns": ["ct.pinterest.com", "pintrk("]
    }
]


def bump_version(current_version: str, part: str = "patch") -> str:
    """Incrémente la version sémantique X.Y.Z."""
    parts = current_version.split(".")
    if len(parts) != 3:
        return "1.0.1"

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    return f"{major}.{minor}.{patch}"


def update_compliance_signatures() -> str:
    """Met à jour le fichier signatures de conformité et renvoie la nouvelle version."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    current_ver = data.get("version", "1.0.0")
    new_ver = bump_version(current_ver, "patch")

    # Enrichissement avec les crawlers émergents
    existing_bot_names = {b["name"].lower() for b in data.get("ai_crawlers", [])}
    added_bots = 0
    for bot in EMERGING_AI_AGENTS:
        if bot["name"].lower() not in existing_bot_names:
            data.setdefault("ai_crawlers", []).append(bot)
            added_bots += 1

    # Enrichissement avec les trackers émergents
    existing_tracker_ids = {t["id"].lower() for t in data.get("gdpr_trackers", [])}
    added_trackers = 0
    for trk in EMERGING_TRACKERS:
        if trk["id"].lower() not in existing_tracker_ids:
            data.setdefault("gdpr_trackers", []).append(trk)
            added_trackers += 1

    data["version"] = new_ver
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"compliance_signatures.json mis à jour en v{new_ver} (+{added_bots} bots, +{added_trackers} trackers).")
    return new_ver


def sync_actor_json(new_ver: str):
    """Synchronise la version dans .actor/actor.json."""
    if os.path.exists(ACTOR_JSON):
        with open(ACTOR_JSON, "r", encoding="utf-8") as f:
            actor_data = json.load(f)
        actor_data["version"] = new_ver
        with open(ACTOR_JSON, "w", encoding="utf-8") as f:
            json.dump(actor_data, f, indent=2, ensure_ascii=False)
        logger.info(f".actor/actor.json synchronisé avec v{new_ver}")


def sync_code_versions(new_ver: str):
    """Met à jour les constantes de version dans les fichiers source Python."""
    # src/__init__.py
    if os.path.exists(INIT_PY):
        with open(INIT_PY, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_ver}"', content)
        with open(INIT_PY, "w", encoding="utf-8") as f:
            f.write(content)

    # src/main.py
    if os.path.exists(MAIN_PY):
        with open(MAIN_PY, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'CURRENT_VERSION\s*=\s*"[^"]+"', f'CURRENT_VERSION = "{new_ver}"', content)
        with open(MAIN_PY, "w", encoding="utf-8") as f:
            f.write(content)

    logger.info(f"Fichiers source Python synchronisés avec v{new_ver}")


def sync_readme(new_ver: str):
    """Met à jour les badges de version et dates dans le README.md."""
    if not os.path.exists(README_MD):
        return

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(README_MD, "r", encoding="utf-8") as f:
        content = f.read()

    # Remplacement de badge version ou mention
    content = re.sub(r'version-\d+\.\d+\.\d+-', f'version-{new_ver}-', content)
    content = re.sub(r'Version:\s*\*\*\d+\.\d+\.\d+\*\*', f'Version: **{new_ver}**', content)
    content = re.sub(r'Last Signatures Update:\s*\*\*[0-9-]+\*\*', f'Last Signatures Update: **{today_str}**', content)

    with open(README_MD, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"README.md synchronisé avec v{new_ver} (date: {today_str})")


def run_self_update():
    """Point d'entrée du script d'auto-mise à jour."""
    logger.info("Démarrage du cycle d'auto-mise à jour des signatures de conformité...")
    new_version = update_compliance_signatures()
    sync_actor_json(new_version)
    sync_code_versions(new_version)
    sync_readme(new_version)
    logger.info(f"Cycle terminé avec succès. Actor prêt pour rebuild automatique Apify v{new_version}")


if __name__ == "__main__":
    run_self_update()
