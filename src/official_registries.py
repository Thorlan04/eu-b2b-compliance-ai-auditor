"""
Module official_registries.py
Interrogation 100% gratuite et sans clé API du registre officiel français :
recherche-entreprises.api.gouv.fr

Fournit :
- Résolution SIREN / SIRET / Raison Sociale / NAF / Dirigeants / Adresse
- Validation mathématique Luhn pour SIREN (9 chiffres) et SIRET (14 chiffres)
- Calcul mathématique officiel de la TVA Intracommunautaire (FR + clé + SIREN)
"""

import re
import logging
from typing import Dict, Any, Optional, List
import requests

logger = logging.getLogger("OfficialRegistries")


def validate_luhn(number_str: str) -> bool:
    """
    Valide un numéro SIREN (9 chiffres) ou SIRET (14 chiffres) selon l'algorithme officiel de Luhn.
    """
    clean_num = re.sub(r"\D", "", number_str)
    if not clean_num or len(clean_num) not in (9, 14):
        return False

    total = 0
    parity = len(clean_num) % 2
    for i, char in enumerate(clean_num):
        digit = int(char)
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit

    return total % 10 == 0


def calculate_french_vat(siren: str) -> Optional[str]:
    """
    Calcule mathématiquement le numéro de TVA intracommunautaire officiel français.
    Formule officielle de l'Administration fiscale :
    Clé = [12 + 3 * (SIREN modulo 97)] modulo 97
    Numéro de TVA = FR + Clé (2 chiffres) + SIREN (9 chiffres)
    """
    clean_siren = re.sub(r"\D", "", siren)
    if len(clean_siren) != 9 or not clean_siren.isdigit():
        return None

    siren_int = int(clean_siren)
    key = (12 + 3 * (siren_int % 97)) % 97
    return f"FR{key:02d}{clean_siren}"


def clean_target_query(raw_query: str) -> str:
    """
    Extrait un terme de recherche pertinent à partir d'un domaine, d'une URL ou d'un nom d'entreprise.
    """
    text = raw_query.strip()
    # Si c'est déjà un numéro SIREN ou SIRET
    digits_only = re.sub(r"\D", "", text)
    if len(digits_only) in (9, 14):
        return digits_only

    # Si c'est une URL
    if "://" in text:
        text = text.split("://", 1)[1]
    text = text.split("/")[0]  # Récupère le domaine sans path
    text = re.sub(r"^www\.", "", text, flags=re.IGNORECASE)

    # Retire l'extension TLD (.fr, .com, .io, .ai, etc.)
    domain_parts = text.split(".")
    if len(domain_parts) > 1:
        text = domain_parts[0]

    return text.strip()


def query_french_registry(target: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Interroge l'API publique ouverte recherche-entreprises.api.gouv.fr.
    Ne requiert AUCUNE clé API ni authentification.
    Retourne un dictionnaire standardisé et exhaustif.
    """
    query = clean_target_query(target)
    api_url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {
        "q": query,
        "page": 1,
        "per_page": 1
    }
    headers = {
        "User-Agent": "eu-b2b-compliance-ai-auditor/1.0.0 (+https://apify.com/actors)",
        "Accept": "application/json"
    }

    result_payload: Dict[str, Any] = {
        "query_searched": query,
        "found": False,
        "company_name": None,
        "siren": None,
        "siret": None,
        "vat_number": None,
        "is_siren_luhn_valid": False,
        "is_siret_luhn_valid": False,
        "naf_ape_code": None,
        "naf_label": None,
        "official_address": None,
        "administrative_status": None,
        "date_creation": None,
        "leaders": [],
        "raw_registry_source": "https://recherche-entreprises.api.gouv.fr"
    }

    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=timeout)
        if response.status_code != 200:
            logger.warning(f"API gouv returned status {response.status_code} for query '{query}'")
            return result_payload

        data = response.json()
        results = data.get("results", [])
        if not results:
            logger.info(f"No company matched in gouv registry for query '{query}'")
            return result_payload

        record = results[0]
        siren = record.get("siren")
        siege = record.get("siege", {})
        siret = siege.get("siret") if siege else None

        # Extraction des dirigeants
        dirigeants = []
        for d in record.get("dirigeants", []):
            nom = f"{d.get('prenoms', '')} {d.get('nom', '')}".strip()
            if not nom:
                nom = d.get("denomination", "Personne Morale")
            qualite = d.get("qualite", "Dirigeant")
            dirigeants.append(f"{nom} ({qualite})")

        # Calcul TVA et validations
        vat_calculated = calculate_french_vat(siren) if siren else None
        siren_valid = validate_luhn(siren) if siren else False
        siret_valid = validate_luhn(siret) if siret else False

        # Adresse complète
        address = siege.get("adresse") or siege.get("geo_adresse")
        if not address and siege:
            address = f"{siege.get('numero_voie', '')} {siege.get('type_voie', '')} {siege.get('libelle_voie', '')}, {siege.get('code_postal', '')} {siege.get('libelle_commune', '')}".strip()

        result_payload.update({
            "found": True,
            "company_name": record.get("nom_complet") or record.get("nom_raison_sociale"),
            "siren": siren,
            "siret": siret,
            "vat_number": vat_calculated,
            "is_siren_luhn_valid": siren_valid,
            "is_siret_luhn_valid": siret_valid,
            "naf_ape_code": record.get("activite_principale"),
            "naf_label": record.get("libelle_activite_principale") or siege.get("libelle_activite_principale_entreprise"),
            "official_address": address,
            "administrative_status": record.get("etat_administratif"),  # "A" (actif) ou "C" (cessé)
            "date_creation": record.get("date_creation"),
            "leaders": dirigeants
        })
        return result_payload

    except Exception as exc:
        logger.error(f"Error querying French registry for query '{query}': {exc}")
        result_payload["error"] = str(exc)
        return result_payload
