"""
Module compta_manager.py
Gestionnaire officiel de comptabilité et de fiscalité Micro-Entreprise BNC (France)
dédié aux revenus perçus via la place de marché Apify Store (Virements SEPA).

Conformité :
- Livre des Recettes officiel (Art. 286 du Code Général des Impôts)
- Calcul des cotisations URSSAF (Prestations de Services BNC ~21.2% + CFP 0.2%)
- Déclaration d'Impôt sur le Revenu (Formulaire 2042-C-PRO) :
  * Case 5HQ (Régime classique BNC avec abattement forfaitaire de 34%)
  * Case 5TE (Option pour le Versement Libératoire de l'IR à 2.2%)
- Règles de territorialité TVA (Prestations de services immatérielles B2B - Art. 259 B du CGI)
"""

import os
import sys
import csv
import argparse
from datetime import datetime
from typing import Dict, Any, List

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPTA_DIR = os.path.join(ROOT_DIR, "compta_impots")
CSV_PATH = os.path.join(COMPTA_DIR, "livre_des_recettes.csv")

# Taux officiels en vigueur (Micro-BNC prestations de services)
URSSAF_COTISATIONS_RATE = 0.212  # 21.2% cotisations sociales
URSSAF_CFP_RATE = 0.002         # 0.2% contribution formation professionnelle
VERSEMENT_LIBERATOIRE_RATE = 0.022  # 2.2% impôt sur le revenu si option versement libératoire
ABATTEMENT_BNC = 0.34           # 34% abattement forfaitaire pour frais professionnels (Case 5HQ)
PLAFOND_FRANCHISE_TVA_SERVICES = 39100.0  # Seuil de franchise en base de TVA
PLAFOND_MICRO_BNC = 77700.0     # Seuil de chiffre d'affaires micro-BNC

CSV_HEADERS = [
    "Date_Encaissement",
    "Reference_Virement",
    "Nom_Client",
    "Pays_Client",
    "Nature_Prestation",
    "Mode_Reglement",
    "Montant_Brut_EUR",
    "Frais_Plateforme_EUR",
    "Montant_Net_Encaisse_EUR"
]


def ensure_livre_recettes_exists():
    """Initialise le fichier CSV officiel s'il n'existe pas encore."""
    os.makedirs(COMPTA_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(CSV_HEADERS)
            # Exemple initial pré-rempli pour guider l'utilisateur
            writer.writerow([
                "2026-10-15",
                "APIFY-PAYOUT-OCT26-01",
                "Apify Inc. (Marketplace Store)",
                "USA",
                "Redevances logicielles - Location Actor eu-b2b-compliance-ai-auditor",
                "Virement bancaire SEPA",
                "450.00",
                "90.00",
                "360.00"
            ])


def add_recette(
    date_encaissement: str,
    reference: str,
    client: str,
    pays: str,
    nature: str,
    montant_brut: float,
    frais: float
):
    """Enregistre un nouveau virement perçu dans le Livre des Recettes."""
    ensure_livre_recettes_exists()
    montant_net = round(montant_brut - frais, 2)

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            date_encaissement,
            reference,
            client,
            pays,
            nature,
            "Virement bancaire SEPA",
            f"{montant_brut:.2f}",
            f"{frais:.2f}",
            f"{montant_net:.2f}"
        ])

    print(f"Recette enregistrée avec succès : +{montant_net:.2f} € nets (Réf: {reference})")


def load_recettes(year: int = None) -> List[Dict[str, Any]]:
    """Lit les recettes enregistrées depuis le fichier CSV officiel."""
    ensure_livre_recettes_exists()
    recettes = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            try:
                date_str = row.get("Date_Encaissement", "")
                row_year = int(date_str.split("-")[0]) if "-" in date_str else None
                if year is None or row_year == year:
                    recettes.append({
                        "date": date_str,
                        "reference": row.get("Reference_Virement"),
                        "client": row.get("Nom_Client"),
                        "pays": row.get("Pays_Client"),
                        "nature": row.get("Nature_Prestation"),
                        "mode": row.get("Mode_Reglement"),
                        "brut": float(row.get("Montant_Brut_EUR", 0)),
                        "frais": float(row.get("Frais_Plateforme_EUR", 0)),
                        "net": float(row.get("Montant_Net_Encaisse_EUR", 0)),
                        "year": row_year
                    })
            except Exception as e:
                continue
    return recettes


def generate_fiscal_dashboard(year: int = None) -> str:
    """Génère le tableau de bord fiscal complet pour l'URSSAF et les Impôts (Cases 5HQ / 5TE)."""
    current_year = year or datetime.now().year
    recettes = load_recettes(current_year)

    total_brut = sum(r["brut"] for r in recettes)
    total_frais = sum(r["frais"] for r in recettes)
    total_net = sum(r["net"] for r in recettes)

    # En micro-entreprise de services, le CA déclaré correspond au montant encaissé
    ca_declare = total_net

    # Cotisations URSSAF
    cotisations_sociales = ca_declare * URSSAF_COTISATIONS_RATE
    cfp = ca_declare * URSSAF_CFP_RATE
    total_urssaf = cotisations_sociales + cfp

    # Impôts sur le revenu Déclaration 2042-C-PRO
    # Option 1: Régime classique (Case 5HQ)
    abattement_forfaitaire = ca_declare * ABATTEMENT_BNC
    revenu_net_imposable_5hq = ca_declare - abattement_forfaitaire

    # Option 2: Versement libératoire (Case 5TE)
    impot_versement_liberatoire = ca_declare * VERSEMENT_LIBERATOIRE_RATE

    reste_a_vivre_reel = ca_declare - total_urssaf

    lines = [
        "=" * 78,
        f"  TABLEAU DE BORD FISCAL & COMPTABLE MICRO-ENTREPRISE BNC - ANNÉE {current_year}",
        "=" * 78,
        f"Nombre de virements SEPA Apify comptabilisés : {len(recettes)}",
        f"Chiffre d'Affaires Brut (ventes Store)     : {total_brut:>10.2f} €",
        f"Commissions Marketplace Apify retenues      : -{total_frais:>9.2f} €",
        f"Chiffre d'Affaires Net Encaissé (sur compte): {total_net:>10.2f} €",
        "-" * 78,
        "1. DÉCLARATION URSSAF (Prestations de Services BNC) :",
        f"   -> Montant à déclarer (CA encaissé)      : {ca_declare:>10.2f} €",
        f"   -> Cotisations sociales (~21.2 %)        : {cotisations_sociales:>10.2f} €",
        f"   -> Formation professionnelle (CFP 0.2 %) : {cfp:>10.2f} €",
        f"   TOTAL PAYABLE À L'URSSAF                 : {total_urssaf:>10.2f} €",
        "-" * 78,
        "2. DÉCLARATION FISCALE ANNUELLE DES REVENUS (Formulaire 2042-C-PRO) :",
        "   [OPTION A] Régime Classique (Barème progressif de l'impôt sur le revenu) :",
        f"   -> À inscrire en CASE 5HQ                : {ca_declare:>10.2f} €",
        f"      (L'État appliquera automatiquement l'abattement forfaitaire BNC de 34 %)",
        f"      Base nette soumise à l'impôt           : {revenu_net_imposable_5hq:>10.2f} €",
        "",
        "   [OPTION B] Régime avec Versement Libératoire (si activé auprès de l'URSSAF) :",
        f"   -> À inscrire en CASE 5TE                : {ca_declare:>10.2f} €",
        f"      (Impôt libératoire déjà réglé à 2.2 % : {impot_versement_liberatoire:>10.2f} €)",
        "-" * 78,
        "3. SYNTHÈSE NETTE EN POCHE & SEUILS LÉGAUX :",
        f"   Reste à vivre net réel (après URSSAF)    : {reste_a_vivre_reel:>10.2f} €",
        f"   Plafond Franchise en base de TVA         : {ca_declare:>10.2f} € / {PLAFOND_FRANCHISE_TVA_SERVICES:.2f} €",
        f"   Statut TVA                              : {'Conforme (Exonération art. 293 B / 259 B du CGI)' if ca_declare <= PLAFOND_FRANCHISE_TVA_SERVICES else 'ALERTE : Seuil de TVA dépassé'}",
        "=" * 78
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compta BNC & Livre des Recettes Apify Store")
    subparsers = parser.add_subparsers(dest="action")

    # Commande report
    report_parser = subparsers.add_parser("report", help="Affiche le tableau de bord fiscal et les cases 5HQ/5TE")
    report_parser.add_argument("--year", type=int, default=datetime.now().year, help="Année fiscale (défaut: courante)")

    # Commande add
    add_parser = subparsers.add_parser("add", help="Enregistre un virement SEPA reçu d'Apify")
    add_parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="Date (YYYY-MM-DD)")
    add_parser.add_argument("--ref", type=str, required=True, help="Référence virement bancaire ou payout Apify")
    add_parser.add_argument("--client", type=str, default="Apify Inc.", help="Nom du payeur")
    add_parser.add_argument("--pays", type=str, default="USA", help="Pays du client")
    add_parser.add_argument("--nature", type=str, default="Redevance de logiciel Actor Apify Store", help="Nature prestation")
    add_parser.add_argument("--gross", type=float, required=True, help="Montant brut facturé (€)")
    add_parser.add_argument("--fee", type=float, default=0.0, help="Frais de plateforme Apify (€)")

    args = parser.parse_args()

    if args.action == "add":
        add_recette(
            date_encaissement=args.date,
            reference=args.ref,
            client=args.client,
            pays=args.pays,
            nature=args.nature,
            montant_brut=args.gross,
            frais=args.fee
        )
    else:
        # Par défaut affiche le rapport fiscal
        year = getattr(args, "year", datetime.now().year)
        print(generate_fiscal_dashboard(year))


if __name__ == "__main__":
    main()
