"""
Module web_ai_compliance_scanner.py
Audit technique déterministe RGPD + AI-Readiness (GEO) + Lead Enrichment.

Effectue :
- Analyse du robots.txt pour tous les crawlers IA (GPTBot, OAI-SearchBot, PerplexityBot, etc.)
- Détection et validation de /llms.txt et /llms-full.txt
- Détection de /.well-known/openapi.json et /.well-known/ai-plugin.json
- Extraction Schema.org JSON-LD (Organization, WebSite, etc.)
- Détection des pages légales obligatoires (Mentions Légales, CGU, Privacy)
- Vérification de la présence du SIRET, TVA, Directeur de publication et Hébergeur
- Détection des trackers tiers (Google Analytics, Meta Pixel, Hotjar, TikTok, etc.)
- Lead enrichment : emails de contact, profils sociaux, stack technique
- Calcul des scores RGPD (sur 100), AI Readiness (sur 100) et plan d'action commercial
"""

import os
import re
import json
import logging
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, List, Optional, Set
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("WebAIComplianceScanner")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "data")
SIGNATURES_FILE = os.path.join(DATA_DIR, "compliance_signatures.json")


def load_compliance_signatures() -> Dict[str, Any]:
    """Charge la base de connaissances et signatures de conformité."""
    if os.path.exists(SIGNATURES_FILE):
        with open(SIGNATURES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "ai_crawlers": [],
        "gdpr_trackers": [],
        "scoring_weights": {"rgpd": {}, "ai_search": {}}
    }


def normalize_domain_url(raw_target: str) -> str:
    """Normalise une URL ou un domaine en URL HTTPs propre."""
    target = raw_target.strip()
    if not target.startswith("http://") and not target.startswith("https://"):
        target = "https://" + target
    parsed = urlparse(target)
    netloc = parsed.netloc or parsed.path
    # Retirer les éventuels ports ou paths résiduels
    netloc = netloc.split("/")[0]
    return f"https://{netloc}"


class WebAIComplianceScanner:
    def __init__(self, target_url: str, timeout: int = 20):
        self.base_url = normalize_domain_url(target_url)
        parsed = urlparse(self.base_url)
        self.domain = parsed.netloc
        self.timeout = timeout
        self.signatures = load_compliance_signatures()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 (compatible; EUB2BAuditor/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
        })

    def safe_get(self, url: str) -> Optional[requests.Response]:
        """Exécute une requête GET résiliente avec fallback HTTPS -> HTTP."""
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True, verify=True)
            return resp
        except requests.exceptions.SSLError:
            try:
                # Fallback sans vérification SSL si le certificat est expiré/mal configuré
                resp = self.session.get(url, timeout=self.timeout, allow_redirects=True, verify=False)
                return resp
            except Exception as e:
                logger.warning(f"Failed SSL fallback for {url}: {e}")
                return None
        except Exception as e:
            logger.warning(f"Failed GET {url}: {e}")
            return None

    def scan_robots_txt(self) -> Dict[str, Any]:
        """Analyse le fichier robots.txt et extrait les règles pour chaque crawler IA."""
        robots_url = urljoin(self.base_url, "/robots.txt")
        resp = self.safe_get(robots_url)
        ai_rules: Dict[str, str] = {}
        all_disallowed = False

        if not resp or resp.status_code != 200:
            return {
                "exists": False,
                "url": robots_url,
                "status_code": resp.status_code if resp else None,
                "ai_crawlers_rules": {c["name"]: "allowed_by_default" for c in self.signatures.get("ai_crawlers", [])},
                "disallows_all_crawlers": False
            }

        content = resp.text
        lines = content.splitlines()
        current_user_agents: List[str] = []
        rules_by_agent: Dict[str, List[str]] = {}

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().lower()
                val = val.strip()

                if key == "user-agent":
                    current_user_agents.append(val.lower())
                elif key in ("disallow", "allow"):
                    for agent in current_user_agents:
                        if agent not in rules_by_agent:
                            rules_by_agent[agent] = []
                        rules_by_agent[agent].append(f"{key}:{val}")
            else:
                current_user_agents = []

        # Analyse des crawlers IA répertoriés
        for crawler in self.signatures.get("ai_crawlers", []):
            crawler_name = crawler["name"]
            matched_status = "allowed"

            # Vérification directe du bot
            agent_keys = [a.lower() for a in crawler.get("user_agents", [crawler_name])]
            bot_directives = []
            for ak in agent_keys:
                if ak in rules_by_agent:
                    bot_directives.extend(rules_by_agent[ak])

            if bot_directives:
                is_disallowed = any(d.startswith("disallow:/") or d == "disallow: " or d == "disallow:" for d in bot_directives)
                is_explicitly_blocked = any(d in ("disallow:/", "disallow: /") for d in bot_directives)
                matched_status = "blocked" if is_explicitly_blocked else "restricted"
            else:
                # Vérifie si l'agent universel '*' bloque tout
                star_rules = rules_by_agent.get("*", [])
                if any(r in ("disallow:/", "disallow: /") for r in star_rules):
                    matched_status = "blocked_by_wildcard"
                else:
                    matched_status = "allowed"

            ai_rules[crawler_name] = matched_status

        return {
            "exists": True,
            "url": robots_url,
            "status_code": 200,
            "ai_crawlers_rules": ai_rules,
            "disallows_all_crawlers": any(r in ("disallow:/", "disallow: /") for r in rules_by_agent.get("*", []))
        }

    def scan_llms_txt(self) -> Dict[str, Any]:
        """Vérifie l'existence et la conformité de /llms.txt et /llms-full.txt."""
        llms_url = urljoin(self.base_url, "/llms.txt")
        resp = self.safe_get(llms_url)

        has_llms = False
        is_valid_markdown = False
        has_title = False
        summary_preview = None

        if resp and resp.status_code == 200 and len(resp.text.strip()) > 10:
            # Vérifier que ce n'est pas une fausse page 404 HTML
            content = resp.text
            if not ("<!doctype html" in content.lower() or "<html" in content.lower()):
                has_llms = True
                has_title = "# " in content
                is_valid_markdown = has_title or "> " in content or "- [" in content
                summary_preview = content[:250].strip()

        # Test /llms-full.txt
        llms_full_url = urljoin(self.base_url, "/llms-full.txt")
        resp_full = self.safe_get(llms_full_url)
        has_llms_full = bool(resp_full and resp_full.status_code == 200 and len(resp_full.text.strip()) > 20 and not "<html" in resp_full.text.lower())

        return {
            "has_llms_txt": has_llms,
            "llms_txt_url": llms_url if has_llms else None,
            "is_valid_markdown": is_valid_markdown,
            "has_markdown_title": has_title,
            "has_llms_full_txt": has_llms_full,
            "llms_full_url": llms_full_url if has_llms_full else None,
            "preview": summary_preview
        }

    def scan_api_readiness(self) -> Dict[str, Any]:
        """Vérifie la présence de points de terminaison d'API ouverts pour agents IA."""
        endpoints = [
            "/.well-known/openapi.json",
            "/.well-known/openapi.yaml",
            "/.well-known/ai-plugin.json",
            "/openapi.json",
            "/api-docs"
        ]
        found_endpoints = []
        for ep in endpoints:
            u = urljoin(self.base_url, ep)
            r = self.safe_get(u)
            if r and r.status_code == 200 and len(r.text.strip()) > 20:
                if not "<html" in r.text.lower() or "swagger" in r.text.lower() or "openapi" in r.text.lower():
                    found_endpoints.append(ep)

        return {
            "has_ai_api_spec": len(found_endpoints) > 0,
            "detected_endpoints": found_endpoints
        }

    def scan_web_pages(self) -> Dict[str, Any]:
        """Scanne la page d'accueil et localise la page mentions légales / confidentialité."""
        resp = self.safe_get(self.base_url)
        if not resp:
            return {
                "reachable": False,
                "homepage_html": "",
                "legal_pages": [],
                "emails": [],
                "socials": {},
                "tech_stack": [],
                "schema_org_types": [],
                "trackers": []
            }

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # 1. Extraction Schema.org JSON-LD
        schema_types: List[str] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if script.string:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        st = data.get("@type")
                        if st:
                            schema_types.append(st if isinstance(st, str) else str(st))
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("@type"):
                                schema_types.append(str(item.get("@type")))
            except Exception:
                pass

        # 2. Détection Tech Stack
        tech_stack: Set[str] = set()
        html_lower = html.lower()
        if "wp-content" in html_lower or "wordpress" in html_lower:
            tech_stack.add("WordPress")
        if "cdn.shopify.com" in html_lower or "shopify" in html_lower:
            tech_stack.add("Shopify")
        if "webflow" in html_lower:
            tech_stack.add("Webflow")
        if "_next" in html_lower or "__next" in html_lower:
            tech_stack.add("Next.js")
        if "nuxt" in html_lower:
            tech_stack.add("Nuxt.js")
        if "prestashop" in html_lower:
            tech_stack.add("PrestaShop")
        if "tailwind" in html_lower:
            tech_stack.add("Tailwind CSS")
        if "cloudflare" in html_lower or resp.headers.get("server", "").lower().find("cloudflare") != -1:
            tech_stack.add("Cloudflare")
        if "react" in html_lower:
            tech_stack.add("React")
        if "vue" in html_lower:
            tech_stack.add("Vue.js")

        # 3. Détection Trackers RGPD
        detected_trackers: Set[str] = set()
        for tracker in self.signatures.get("gdpr_trackers", []):
            t_name = tracker["name"]
            for pattern in tracker.get("patterns", []):
                if pattern.lower() in html_lower:
                    detected_trackers.add(t_name)
                    break

        # 4. Extraction Lead Enrichment (Emails & Réseaux Sociaux)
        emails: Set[str] = set()
        # Regex emails
        found_raw_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html)
        for em in found_raw_emails:
            em_clean = em.lower().strip(".")
            # Filtrer les fausses extensions graphiques ou frameworks
            if not any(em_clean.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js"]):
                emails.add(em_clean)

        # Liens mailto:
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.startswith("mailto:"):
                clean_mail = href.replace("mailto:", "").split("?")[0].strip().lower()
                if "@" in clean_mail:
                    emails.add(clean_mail)

        # Réseaux sociaux
        socials: Dict[str, str] = {}
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if "linkedin.com/company" in href or "linkedin.com/in/" in href:
                socials["linkedin"] = href
            elif "twitter.com/" in href or "x.com/" in href:
                if not "share" in href:
                    socials["twitter_x"] = href
            elif "github.com/" in href and not "github.com/login" in href:
                socials["github"] = href
            elif "youtube.com/" in href:
                socials["youtube"] = href
            elif "instagram.com/" in href:
                socials["instagram"] = href

        # 5. Localisation des pages légales
        legal_candidates = []
        legal_keywords = [
            "mentions-legales", "mentions_legales", "legal", "mentions",
            "confidentialite", "politique-de-confidentialite", "privacy",
            "cgu", "cgv", "terms"
        ]

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            text = a_tag.get_text().strip().lower()
            href_lower = href.lower()

            if any(k in href_lower for k in legal_keywords) or any(k in text for k in ["mentions légales", "confidentialité", "données personnelles", "legal notice"]):
                full_legal_url = urljoin(self.base_url, href)
                # S'assurer que le lien reste sur le même domaine
                if urlparse(full_legal_url).netloc == self.domain:
                    if full_legal_url not in legal_candidates:
                        legal_candidates.append(full_legal_url)

        # Scanner la page légale principale pour SIRET / Hébergeur / Directeur publication
        legal_analysis = self.analyze_legal_page(legal_candidates)

        return {
            "reachable": True,
            "homepage_url": self.base_url,
            "legal_pages_found": legal_candidates,
            "legal_analysis": legal_analysis,
            "emails": sorted(list(emails)),
            "socials": socials,
            "tech_stack": sorted(list(tech_stack)),
            "schema_org_types": sorted(list(set(schema_types))),
            "trackers": sorted(list(detected_trackers))
        }

    def analyze_legal_page(self, legal_urls: List[str]) -> Dict[str, Any]:
        """Analyse le contenu des pages légales trouvées pour vérifier la conformité stricte."""
        res: Dict[str, Any] = {
            "has_legal_page": len(legal_urls) > 0,
            "scanned_legal_url": None,
            "siret_detected": None,
            "siren_detected": None,
            "vat_detected": None,
            "publication_director_found": False,
            "web_host_found": False,
            "host_name": None
        }

        if not legal_urls:
            return res

        target_url = legal_urls[0]
        res["scanned_legal_url"] = target_url
        resp = self.safe_get(target_url)
        if not resp or resp.status_code != 200:
            return res

        text = resp.text
        text_lower = text.lower()

        # Détection SIRET (14 chiffres) ou SIREN (9 chiffres)
        siret_match = re.search(r"\b\d{3}\s?\d{3}\s?\d{3}\s?\d{5}\b", text)
        if siret_match:
            res["siret_detected"] = re.sub(r"\s", "", siret_match.group(0))

        siren_match = re.search(r"\b\d{3}\s?\d{3}\s?\d{3}\b", text)
        if siren_match:
            clean_siren = re.sub(r"\s", "", siren_match.group(0))
            if not res["siret_detected"]:
                res["siren_detected"] = clean_siren

        # Détection TVA Intracommunautaire
        vat_match = re.search(r"\bFR\s?[0-9A-Z]{2}\s?\d{3}\s?\d{3}\s?\d{3}\b", text, re.IGNORECASE)
        if vat_match:
            res["vat_detected"] = re.sub(r"\s", "", vat_match.group(0)).upper()

        # Détection Directeur de la publication
        if any(term in text_lower for term in [
            "directeur de la publication", "directrice de la publication",
            "responsable de la publication", "directeur de publication",
            "responsable de publication"
        ]):
            res["publication_director_found"] = True

        # Détection Hébergeur
        hosts = [
            ("OVH", ["ovh", "ovhcloud"]),
            ("AWS (Amazon Web Services)", ["amazon web services", "aws"]),
            ("Vercel", ["vercel"]),
            ("Scaleway", ["scaleway"]),
            ("Infomaniak", ["infomaniak"]),
            ("Google Cloud", ["google cloud", "google ireland"]),
            ("Microsoft Azure", ["azure", "microsoft corporation"]),
            ("Hostinger", ["hostinger"]),
            ("o2switch", ["o2switch"]),
            ("Cloudflare", ["cloudflare"])
        ]
        for host_label, keywords in hosts:
            if any(k in text_lower for k in keywords):
                res["web_host_found"] = True
                res["host_name"] = host_label
                break

        if not res["web_host_found"] and "hébergeur" in text_lower or "hebergement" in text_lower or "hébergé par" in text_lower:
            res["web_host_found"] = True
            res["host_name"] = "Hébergeur mentionné"

        return res

    def calculate_scores(
        self,
        robots_data: Dict[str, Any],
        llms_data: Dict[str, Any],
        api_data: Dict[str, Any],
        web_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calcule les scores déterministes RGPD et AI-Readiness selon le barème officiel."""
        legal = web_data.get("legal_analysis", {})
        trackers = web_data.get("trackers", [])

        # 1. Calcul Score RGPD (0-100)
        rgpd_score = 0
        if legal.get("has_legal_page"):
            rgpd_score += 25
        if legal.get("siret_detected") or legal.get("siren_detected"):
            rgpd_score += 25
        if legal.get("vat_detected"):
            rgpd_score += 15
        if legal.get("web_host_found"):
            rgpd_score += 15

        # Tracker hygiene : pénalité si trackers publicitaires agressifs chargés direct
        if len(trackers) == 0:
            rgpd_score += 20
        elif len(trackers) <= 2:
            rgpd_score += 10
        else:
            rgpd_score += 5

        rgpd_score = min(100, max(0, rgpd_score))

        # 2. Calcul Score AI-Readiness (GEO) (0-100)
        ai_score = 0
        if llms_data.get("has_llms_txt"):
            ai_score += 30
        if llms_data.get("has_llms_full_txt"):
            ai_score += 10

        # Vérification des bots de recherche conversationnelle (OAI-SearchBot, PerplexityBot, Claude-Web)
        ai_rules = robots_data.get("ai_crawlers_rules", {})
        search_bots_allowed = True
        for b in ["OAI-SearchBot", "PerplexityBot", "Claude-Web"]:
            status = ai_rules.get(b, "allowed")
            if "block" in status:
                search_bots_allowed = False
                break

        if search_bots_allowed:
            ai_score += 25

        if len(web_data.get("schema_org_types", [])) > 0:
            ai_score += 20
        if api_data.get("has_ai_api_spec"):
            ai_score += 15

        ai_score = min(100, max(0, ai_score))

        # 3. Note globale
        overall = int((rgpd_score * 0.5) + (ai_score * 0.5))
        if overall >= 90:
            grade = "A+"
        elif overall >= 80:
            grade = "A"
        elif overall >= 65:
            grade = "B"
        elif overall >= 50:
            grade = "C"
        elif overall >= 35:
            grade = "D"
        else:
            grade = "F"

        return {
            "rgpd_compliance_score": rgpd_score,
            "ai_search_readiness_score": ai_score,
            "overall_score": overall,
            "global_compliance_grade": grade
        }

    def generate_action_plan(
        self,
        scores: Dict[str, Any],
        robots_data: Dict[str, Any],
        llms_data: Dict[str, Any],
        web_data: Dict[str, Any],
        registry_data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Génère un plan d'action commercial B2B clair, prêt à être proposé par une agence."""
        actions: List[str] = []
        legal = web_data.get("legal_analysis", {})

        # Actions RGPD & Légal
        if not legal.get("has_legal_page"):
            actions.append("CRITIQUE LÉGAL: Créer immédiatement une page dédiée 'Mentions Légales' accessible depuis le footer (Obligation Art. 6 LCEN, sanction jusqu'à 375 000 €).")
        else:
            if not legal.get("siret_detected") and not legal.get("siren_detected"):
                siret_text = f"(Numéro officiel: {registry_data.get('siret')})" if registry_data and registry_data.get("siret") else ""
                actions.append(f"NON-CONFORMITÉ LÉGALE: Faire figurer le numéro SIREN/SIRET sur la page des mentions légales {siret_text}.")

            if not legal.get("web_host_found"):
                actions.append("OBLIGATION LCEN: Ajouter le nom, raison sociale et adresse de l'hébergeur du site dans les mentions légales.")

            if not legal.get("vat_detected"):
                vat_text = f"(TVA calculée: {registry_data.get('vat_number')})" if registry_data and registry_data.get("vat_number") else ""
                actions.append(f"MENTIONS FISCALES: Ajouter le numéro de TVA intracommunautaire {vat_text} dans les mentions légales.")

        trackers = web_data.get("trackers", [])
        if len(trackers) > 0:
            actions.append(f"AUDIT COOKIES RGPD: {len(trackers)} tracker(s) tiers détecté(s) ({', '.join(trackers)}). S'assurer de la présence d'une CMP (Bannière Axeptio/Didomi/Cookiebot) bloquant ces scripts avant consentement explicite.")

        # Actions AI Readiness (GEO)
        if not llms_data.get("has_llms_txt"):
            actions.append("LEVIER CROISSANCE GEO (AI-SEARCH): Déployer le fichier '/llms.txt' à la racine du domaine pour que Perplexity, SearchGPT et Claude indexent avec précision vos produits et offres.")

        ai_rules = robots_data.get("ai_crawlers_rules", {})
        for bot, status in ai_rules.items():
            if "block" in status and bot in ["OAI-SearchBot", "PerplexityBot"]:
                actions.append(f"VISIBILITÉ AI ENGINE: Débloquer '{bot}' dans robots.txt pour permettre à votre marque d'apparaître comme source citée dans les réponses IA conversationnelles.")

        if len(web_data.get("schema_org_types", [])) == 0:
            actions.append("STRUCTURED DATA: Implémenter le balisage Schema.org JSON-LD 'Organization' et 'WebSite' afin de consolider le Knowledge Graph de l'entreprise.")

        if not actions:
            actions.append("EXCELLENCE CONFORME: Site parfaitement aligné avec les standards légaux français/européens et optimisé pour le référencement IA (GEO).")

        return actions

    def run_full_audit(self, registry_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Exécute l'audit complet et renvoie le rapport unifié."""
        robots_data = self.scan_robots_txt()
        llms_data = self.scan_llms_txt()
        api_data = self.scan_api_readiness()
        web_data = self.scan_web_pages()

        scores = self.calculate_scores(robots_data, llms_data, api_data, web_data)
        action_plan = self.generate_action_plan(scores, robots_data, llms_data, web_data, registry_info)

        return {
            "domain": self.domain,
            "base_url": self.base_url,
            "robots_data": robots_data,
            "llms_data": llms_data,
            "api_data": api_data,
            "web_data": web_data,
            "scores": scores,
            "action_plan": action_plan
        }
