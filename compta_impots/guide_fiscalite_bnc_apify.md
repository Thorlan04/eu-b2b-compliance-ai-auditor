# Guide Fiscal & Comptable : Monétiser un Actor Apify en Micro-Entreprise BNC (France)

Ce guide officiel détaille comment encaisser et déclarer les revenus générés par la location ou l'utilisation pay-per-result de votre Actor **Apify Store** sur votre compte bancaire français en toute conformité avec l'URSSAF et la Direction Générale des Finances Publiques (DGFIP).

---

## 1. Fonctionnement des Virements SEPA Apify

1. **Entité payeuse** : Apify Inc. (société basée aux États-Unis avec entité européenne selon les flux).
2. **Type de virement** : Virement bancaire SEPA direct en Euros (€) vers votre IBAN français (`FR76...`).
3. **Fréquence** : Mensuelle (à chaque fin de mois dès que vos revenus de location / runs atteignent le seuil minimum de payout).
4. **Commission Marketplace** : Apify prélève sa commission de distribution (environ 20%) et vous verse le montant net directement sur votre compte.

---

## 2. Statut Juridique Recommandé : Micro-Entreprise BNC

- **Catégorie d'activité** : BNC (Bénéfices Non Commerciaux) / Prestations de services informatiques & concessions de droits sur logiciels.
- **Code APE habituel** : 
  - `62.01Z` : Programmation informatique
  - `62.02A` : Conseil en systèmes et logiciels informatiques
- **Plafond de Chiffre d'Affaires** : 77 700 € / an (au-delà, passage en déclaration contrôlée).

---

## 3. Déclaration Mensuelle ou Trimestrielle à l'URSSAF

À chaque échéance sur votre espace `autoentrepreneur.urssaf.fr` :
1. Rubrique : **Prestations de services BNC**.
2. Montant à déclarer : **Le montant net encaissé** sur votre compte bancaire (ou brut si mandat d'intermédiation transparent).
3. Taux de cotisations sociales : **~21,2 %** + **0,2 %** (Contribution à la Formation Professionnelle CFP), soit environ **21,4 %**.
4. Aucune démarche complexe : le prélèvement automatique s'effectue sur votre compte bancaire professionnel.

---

## 4. Déclaration Annuelle d'Impôt sur le Revenu (Formulaire 2042-C-PRO)

Lors de votre déclaration de revenus au printemps :

### Option A : Régime de Droit Commun (Sans versement libératoire)
- Inscrivez votre chiffre d'affaires annuel total dans la **CASE 5HQ** (*Régime spécial BNC - Revenus imposables*).
- **L'avantage fiscal de l'abattement forfaitaire BNC** : L'administration fiscale applique automatiquement un **abattement de 34 %** pour frais professionnels. Vous n'êtes imposé que sur **66 %** de vos recettes !

### Option B : Versement Libératoire de l'IR (Si option activée)
- Inscrivez votre chiffre d'affaires dans la **CASE 5TE** (*Auto-entrepreneurs ayant opté pour le versement libératoire de l'impôt sur le revenu - BNC*).
- Vous avez déjà payé votre impôt tout au long de l'année à hauteur de **2,2 %** auprès de l'URSSAF. Ce montant est non soumis au barème progressif.

---

## 5. Régime de TVA & Facturation B2B Internationale

### Client situé aux USA (Apify Inc.) :
- La prestation immatérielle est réputée située hors de l'Union Européenne en vertu de l'**Article 259 B du Code Général des Impôts (CGI)**.
- **Aucune TVA française n'est applicable**.
- Mention légale sur vos justificatifs :  
  `"TVA non applicable - Art. 259 B du CGI (Prestation de services immatérielle B2B fournie à un assujetti établi hors de l'Union Européenne)"`.

### Franchise en base de TVA :
- Si votre chiffre d'affaires global annuel est inférieur à **36 800 €** (seuil de tolérance à **39 100 €**), vous bénéficiez de la franchise en base de TVA.
- Mention complémentaire : `"TVA non applicable, art. 293 B du CGI"`.

---

## 6. Utilisation du Module Automatique `src/compta_manager.py`

Le projet inclut un outil en ligne de commande pour tenir à jour votre Livre des Recettes officiel et calculer instantanément vos cases fiscales :

### 1. Enregistrer un virement reçu d'Apify :
```bash
python -m src.compta_manager add --date 2026-11-01 --ref "APIFY-NOV26-01" --gross 500.00 --fee 100.00 --desc "Location mensuelle Actor Apify Store"
```

### 2. Afficher votre tableau de bord fiscal (URSSAF + Cases 5HQ/5TE) :
```bash
python -m src.compta_manager report --year 2026
```

### 3. Fichier officiel consultable par l'administration :
Le fichier [`compta_impots/livre_des_recettes.csv`](file:///d:/robot%20apify/compta_impots/livre_des_recettes.csv) est automatiquement mis à jour et peut être présenté ou transmis à votre expert-comptable ou centre des impôts en 1 clic.
