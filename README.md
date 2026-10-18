# EU B2B Compliance & AI-Search Readiness Auditor 🚀

[![Apify Actor](https://img.shields.io/badge/Apify-Actor-blue?logo=apify)](https://apify.com)
[![Version](https://img.shields.io/badge/version-1.0.1-green.svg)](https://apify.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://docker.com)
[![Maintenance](https://img.shields.io/badge/Auto--Updated-Weekly-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Apache--2.0-yellow.svg)](LICENSE)

> **Autonomous AI-Search Engine (GEO) & EU Corporate Compliance Auditor.**  
> Scans any domain, company name, or SIREN/SIRET to verify official government registries, compute Intracommunity VAT, audit French/GDPR legal notices, and assess readiness for AI search crawlers (`llms.txt`, `Schema.org`, `OAI-SearchBot`, `PerplexityBot`, `ClaudeBot`).

---

## 💡 Why This Actor is Essential for B2B & Agencies

In 2026, corporate websites face two massive challenges:

1. **Stricter EU & French Legal Enforcement (LCEN / GDPR)**:
   - Websites operating in France without compliant legal notices (missing SIRET, missing web host, missing publication director) face administrative fines from DGCCRF up to **€375,000**.
   - Loading advertising cookies (Meta Pixel, Google Analytics, TikTok) before explicit user consent violates CNIL guidelines.
2. **The Shift from SEO to GEO (Generative Engine Optimization)**:
   - Over 40% of B2B discovery now happens on conversational engines (**ChatGPT Search**, **Perplexity**, **Claude**, **Gemini**).
   - If a company blocks `OAI-SearchBot` or lacks a standardized `/llms.txt`, it becomes **completely invisible** in AI-generated answers.

**This Actor provides marketing agencies, sales teams, and compliance officers with turn-key, actionable audits that can be monetized immediately.**

---

## ✨ Key Features

- 🏛️ **Official Government Registry Resolution**: Free, real-time query against the French national company database (`recherche-entreprises.api.gouv.fr`). Extracts legal denomination, 9-digit SIREN, 14-digit SIRET, NAF/APE code, official registered address, and active corporate officers.
- 🧮 **Mathematical Intracommunity VAT Computation**: Automatic calculation using the official French tax formula (`FR + [12 + 3 * (SIREN % 97)] % 97 + SIREN`) and Luhn algorithm validation.
- 🤖 **AI-Search (GEO) Engine Audit**:
  - Verifies `/llms.txt` and `/llms-full.txt` presence and markdown syntax.
  - Inspects `robots.txt` directives for major AI bots: `GPTBot`, `OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`, `ClaudeBot`, `Claude-Web`, `Google-Extended`, `Meta-ExternalAgent`, `Bytespider`, `DeepSeekBot`, `MistralBot`.
  - Detects `Schema.org` JSON-LD structured data (`Organization`, `WebSite`, `LocalBusiness`).
  - Checks for AI plugin / OpenAPI specifications (`/.well-known/openapi.json`).
- ⚖️ **GDPR & Legal Notice Scoring**:
  - Automatically locates legal notice pages (`/mentions-legales`, `/legal`, `/privacy`).
  - Checks for displayed SIREN/SIRET, publication director, and identified hosting provider (OVH, AWS, Scaleway, Vercel, Cloudflare, etc.).
  - Detects third-party tracking scripts loaded on initial page load.
- 🎯 **Lead Enrichment**: Extracts verified public contact emails, social profiles (LinkedIn, X/Twitter, GitHub, YouTube), and detected tech stack (WordPress, Shopify, Next.js, Webflow, Tailwind, etc.).
- 📋 **Commercial Pitch Action Plan**: Generates a bulleted, prioritized action plan ready to be attached to a client proposal or outreach email.
- 🛡️ **Self-Healing Runtime Architecture**: Built-in fallback heuristics and optional **Gemini 2.5 Flash** repair to guarantee a 100% success rate with zero crashes, even on blocked or ill-formed websites.

---

## 🚀 Quick Start (1-Click Test)

Run the Actor with pre-filled targets on Apify Console or via API:

### Input Example (`JSON`)

```json
{
  "targets": [
    "https://www.doctolib.fr",
    "794598813",
    "Mirakl"
  ],
  "audit_depth": "full_enterprise",
  "verify_official_registry": true,
  "check_ai_readiness": true,
  "check_gdpr_legal": true,
  "timeout_per_target_seconds": 30
}
```

---

## 📊 Output Dataset Example

Every item pushed to your Apify Dataset matches the following structured JSON schema:

```json
{
  "target_input": "https://www.doctolib.fr",
  "domain": "doctolib.fr",
  "company_name": "DOCTOLIB",
  "siren": "794598813",
  "siret": "79459881300077",
  "vat_number": "FR14794598813",
  "naf_ape_code": "62.01Z",
  "naf_label": "Programmation informatique",
  "official_address": "54 Quai Charles Pasqua, 92300 Levallois-Perret",
  "administrative_status": "A",
  "leaders": [
    "STANISLAS NIOX-CHATEAU (Président de SAS)",
    "GRANT THORNTON (Commissaire aux comptes titulaire)"
  ],
  "rgpd_compliance_score": 90,
  "ai_search_readiness_score": 85,
  "global_compliance_grade": "A",
  "llms_txt_status": {
    "has_llms_txt": true,
    "llms_txt_url": "https://doctolib.fr/llms.txt",
    "is_valid_markdown": true
  },
  "robots_ai_rules": {
    "OAI-SearchBot": "allowed",
    "PerplexityBot": "allowed",
    "ClaudeBot": "allowed",
    "Google-Extended": "allowed"
  },
  "schema_org_types": [
    "Organization",
    "WebSite"
  ],
  "public_emails": [
    "contact@doctolib.fr",
    "dpo@doctolib.fr"
  ],
  "social_profiles": {
    "linkedin": "https://www.linkedin.com/company/doctolib",
    "twitter_x": "https://twitter.com/doctolib"
  },
  "tech_stack": [
    "Cloudflare",
    "Next.js",
    "React"
  ],
  "detected_trackers": [
    "Google Analytics / GA4"
  ],
  "audit_action_plan": [
    "AUDIT COOKIES RGPD: 1 tracker tiers détecté (Google Analytics / GA4). S'assurer de la présence d'une bannière de consentement conforme CNIL.",
    "EXCELLENCE CONFORME: Site bien structuré pour le référencement génératif IA (GEO)."
  ],
  "scanned_at": "2026-10-18T09:00:00Z",
  "auditor_version": "1.0.0"
}
```

---

## ⚡ Automations & Workflow Integrations

### 1. Make.com (Integromat)
Trigger an audit automatically when a new lead enters your CRM (HubSpot, Pipedrive, Notion):
1. **Webhook / New Lead** -> 
2. **Apify Module: "Run Actor"** (`eu-b2b-compliance-ai-auditor`) -> 
3. **Gmail / Slack Module**: Send an automated audit report and pitch directly to your sales team!

### 2. n8n
```json
{
  "nodes": [
    {
      "parameters": {
        "actorId": "YOUR_USERNAME/eu-b2b-compliance-ai-auditor",
        "input": {
          "targets": ["={{ $json.website_url }}"]
        }
      },
      "name": "Apify Auditor",
      "type": "n8n-nodes-base.apify"
    }
  ]
}
```

### 3. Zapier
Connect the Apify Zapier app: whenever a row is added to Google Sheets, trigger the Auditor and write back the `global_compliance_grade`, `vat_number`, and `audit_action_plan`.

---

## 🔄 Autonomous CI/CD & Self-Healing

- **Weekly GitHub Actions (`.github/workflows/auto_update_actor.yml`)**:  
  Every Monday at 04:00 UTC, the repository runs `src/self_updater.py` to scan for new AI crawlers and GDPR trackers, increments the semver build, and pushes changes to `main`.
- **Apify Git Integration**:  
  Each commit automatically triggers an Actor rebuild on Apify Store, maintaining the coveted **"Recently Updated"** badge and maximizing marketplace search rankings.
- **Fault-Tolerant Engine (`src/self_healing_parser.py`)**:  
  Handles HTTP 403, SSL certificate misconfigurations, and single-page apps without crashing, ensuring customers always receive billable data.

---

## 💰 Monetization Settings on Apify Store

To generate recurring monthly passive income:
- **Model**: Monthly Rental (**$29.00 - $79.00 / month**) or Pay-Per-Result (**$0.02 - $0.05 / result**).
- **Payouts**: Directly wired to your European/French bank account (**IBAN SEPA**) with zero currency conversion fees.
- **Accounting**: Pre-configured accounting module in `compta_impots/` with French Micro-Enterprise BNC support (Boxes 5HQ / 5TE).

---

## 📄 License

Licensed under the Apache License, Version 2.0.
