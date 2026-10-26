"""
Point d'entrée principal de l'Actor Apify: eu-b2b-compliance-ai-auditor
Exécuté lors des lancements clients sur Apify Store ou automatisations (Make, n8n, Zapier).
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from apify import Actor

from src.official_registries import query_french_registry
from src.web_ai_compliance_scanner import WebAIComplianceScanner, normalize_domain_url
from src.self_healing_parser import build_self_healed_report, call_gemini_healing_assistant

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("EUComplianceAuditorActor")

CURRENT_VERSION = "1.0.3"


async def process_single_target(
    target: str,
    verify_registry: bool,
    check_ai: bool,
    check_gdpr: bool,
    gemini_key: str = None,
    timeout: int = 25
) -> Dict[str, Any]:
    """Traite un domaine, URL, nom d'entreprise ou SIREN/SIRET avec auto-guérison intégrée."""
    target_clean = str(target).strip()
    logger.info(f"==> Démarrage de l'audit pour la cible : {target_clean}")

    # 1. Étape Registre Officiel Français / Européen
    registry_info: Dict[str, Any] = {}
    if verify_registry:
        try:
            registry_info = query_french_registry(target_clean, timeout=timeout)
            if registry_info.get("found"):
                logger.info(f"Registre officiel validé : {registry_info.get('company_name')} (SIREN {registry_info.get('siren')})")
            else:
                logger.info(f"Aucune correspondance exacte registre pour '{target_clean}'")
        except Exception as e:
            logger.warning(f"Erreur tolérée lors de la requête registre : {e}")

    # 2. Étape Scan Web Compliance & AI Readiness
    # Détermination de l'URL cible
    candidate_url = target_clean
    if registry_info.get("found") and not ("." in target_clean or "://" in target_clean):
        # Si la cible était un SIREN ou un nom pur, essayer de déduire un domaine ou scanner
        candidate_url = f"https://www.{clean_string_to_domain(registry_info.get('company_name', ''))}.fr"

    scanner = WebAIComplianceScanner(candidate_url, timeout=timeout)
    domain_audited = scanner.domain

    try:
        # Exécution de l'audit web complet
        web_audit = scanner.run_full_audit(registry_info=registry_info)
        robots_data = web_audit["robots_data"]
        llms_data = web_audit["llms_data"]
        web_data = web_audit["web_data"]
        scores = web_audit["scores"]
        action_plan = web_audit["action_plan"]

        # Réconciliation des données d'entreprise
        legal = web_data.get("legal_analysis", {})
        final_company_name = (
            registry_info.get("company_name")
            or legal.get("company_name")
            or domain_audited.capitalize()
        )
        final_siren = registry_info.get("siren") or legal.get("siren_detected")
        final_siret = registry_info.get("siret") or legal.get("siret_detected")
        final_vat = registry_info.get("vat_number") or legal.get("vat_detected")

        final_item = {
            "target_input": target_clean,
            "domain": domain_audited,
            "company_name": final_company_name,
            "siren": final_siren,
            "siret": final_siret,
            "vat_number": final_vat,
            "naf_ape_code": registry_info.get("naf_ape_code"),
            "naf_label": registry_info.get("naf_label"),
            "official_address": registry_info.get("official_address"),
            "administrative_status": registry_info.get("administrative_status") or "A",
            "leaders": registry_info.get("leaders", []),
            "rgpd_compliance_score": scores.get("rgpd_compliance_score", 0),
            "ai_search_readiness_score": scores.get("ai_search_readiness_score", 0),
            "global_compliance_grade": scores.get("global_compliance_grade", "C"),
            "llms_txt_status": llms_data,
            "robots_ai_rules": robots_data.get("ai_crawlers_rules", {}),
            "schema_org_types": web_data.get("schema_org_types", []),
            "public_emails": web_data.get("emails", []),
            "social_profiles": web_data.get("socials", {}),
            "tech_stack": web_data.get("tech_stack", []),
            "detected_trackers": web_data.get("trackers", []),
            "audit_action_plan": action_plan,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "auditor_version": CURRENT_VERSION
        }
        return final_item

    except Exception as exc:
        logger.error(f"Incident survenue pour {target_clean}: {exc}. Activation de l'auto-guérison.")
        # Appel du module d'auto-guérison pour ne JAMAIS perdre le résultat client
        gemini_res = None
        if gemini_key:
            gemini_res = call_gemini_healing_assistant(str(exc), target_clean, gemini_key)

        healed_item = build_self_healed_report(
            target_input=target_clean,
            domain=domain_audited or target_clean,
            error_context=str(exc),
            registry_data=registry_info,
            gemini_data=gemini_res,
            raw_text=f"{target_clean} {str(exc)}"
        )
        healed_item["scanned_at"] = datetime.now(timezone.utc).isoformat()
        healed_item["auditor_version"] = CURRENT_VERSION
        return healed_item


def clean_string_to_domain(name: str) -> str:
    """Transforme un nom de société en identifiant de domaine simplifié."""
    import re
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
    return cleaned[:15] if cleaned else "entreprise"


async def main():
    async with Actor:
        # 1. Récupération des inputs fournis par l'utilisateur ou l'API Apify
        actor_input = await Actor.get_input() or {}

        targets: List[str] = actor_input.get("targets", [
            "https://www.doctolib.fr",
            "794598813",
            "Mirakl"
        ])
        verify_registry = actor_input.get("verify_official_registry", True)
        check_ai = actor_input.get("check_ai_readiness", True)
        check_gdpr = actor_input.get("check_gdpr_legal", True)
        gemini_key = actor_input.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        timeout = int(actor_input.get("timeout_per_target_seconds", 30))

        logger.info(f"Démarrage eu-b2b-compliance-ai-auditor v{CURRENT_VERSION}")
        logger.info(f"Nombre de cibles à auditer : {len(targets)}")

        results_count = 0
        for target in targets:
            if not target or not str(target).strip():
                continue

            report = await process_single_target(
                target=target,
                verify_registry=verify_registry,
                check_ai=check_ai,
                check_gdpr=check_gdpr,
                gemini_key=gemini_key,
                timeout=timeout
            )

            # Pousse le résultat dans le Dataset Apify officiel
            await Actor.push_data(report)
            results_count += 1
            logger.info(f"Rapport sauvegardé avec succès pour : {report.get('domain')} (Grade: {report.get('global_compliance_grade')})")

        logger.info(f"Audit terminé avec succès. {results_count} rapport(s) délivré(s) et facturés.")


if __name__ == "__main__":
    asyncio.run(main())
