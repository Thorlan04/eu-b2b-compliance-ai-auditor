# Guide Express (5 Minutes) : Connecter, Monétiser & Encaisser vos Revenus Apify

Ce guide pas-à-pas vous accompagne de la mise en ligne de votre robot jusqu'à la réception de votre premier virement SEPA sur votre compte bancaire français.

---

## ⏱️ Étape 1 : Créer votre Dépôt GitHub (1 min)

1. Rendez-vous sur votre compte **GitHub** ([github.com/new](https://github.com/new)).
2. Créez un nouveau dépôt nommé : `eu-b2b-compliance-ai-auditor` (Public ou Privé).
3. Ouvrez un terminal dans `D:\robot apify` et poussez le code :
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit eu-b2b-compliance-ai-auditor v1.0.0"
   git branch -M main
   git remote add origin https://github.com/Thorlan04/eu-b2b-compliance-ai-auditor.git
   git push -u origin main
   ```

---

## ⚡ Étape 2 : Créer l'Actor sur Apify en 2 Clics (1 min)

1. Connectez-vous sur [console.apify.com](https://console.apify.com).
2. Dans le menu de gauche, cliquez sur **Actors** -> bouton **Create new** (en haut à droite).
3. Choisissez l'option **"Link Git repository"** (ou GitHub).
4. Sélectionnez votre dépôt : `Thorlan04/eu-b2b-compliance-ai-auditor`.
5. Apify détecte automatiquement le fichier `.actor/actor.json` et le `Dockerfile`.
6. Cliquez sur **Build**. En moins de 60 secondes, votre Actor est compilé et prêt à tourner !

---

## 💶 Étape 3 : Activer la Monétisation sur l'Apify Store (1 min)

1. Dans la page de votre Actor sur Apify, cliquez sur l'onglet **Publication** (ou **Monetization**).
2. Choisissez votre modèle de tarification recommandé :
   - **Option 1 : Rental (Abonnement mensuel récurrent)** :  
     Fixez le tarif à **$49.00 / mois** ou **$79.00 / mois** avec un essai gratuit de 3 jours.  
     *(Idéal pour les agences marketing et experts SEO qui lancent des audits en continu)*.
   - **Option 2 : Pay-Per-Result (À la consommation)** :  
     Fixez le tarif à **$0.05 / résultat** (soit 50 $ pour un batch de 1 000 entreprises auditées).
3. Remplissez la description publique (le fichier `README.md` est automatiquement utilisé comme vitrine SEO).
4. Cochez **"Publish to Apify Store"**. Votre Actor est maintenant visible mondialement !

---

## 🏦 Étape 4 : Renseigner son IBAN Français pour les Virements SEPA (1 min)

1. Sur Apify Console, cliquez sur votre avatar (en bas à gauche) -> **Billing & Invoices** -> onglet **Payouts** (ou [apify.com/billing/payouts](https://console.apify.com/billing/payouts)).
2. Cliquez sur **Add Payout Method**.
3. Choisissez **Bank Transfer (SEPA / Wire Transfer)**.
4. Renseignez les coordonnées de votre compte bancaire (professionnel ou dédié micro-entreprise) :
   - **Titulaire du compte** : Votre Nom / Raison Sociale
   - **Pays de la banque** : France (`FR`)
   - **Devise** : `EUR (€)`
   - **IBAN** : Votre IBAN français (`FR76...`)
   - **BIC / SWIFT** : Code BIC de votre banque (ex: BNP, BoursoBank, Qonto, Shine, etc.)
5. À chaque fin de mois, dès que le seuil de $50 est atteint, Apify émet automatiquement un **virement SEPA direct en Euros** sur votre compte bancaire français.

---

## 🔄 Étape 5 : Fonctionnement 100% Autonome & Déclaration Fiscale (1 min)

### 1. Le Rebuild Automatique Hebdomadaire (GitHub Actions)
- Le fichier `.github/workflows/auto_update_actor.yml` tourne chaque lundi matin à 04:00 UTC.
- Il met à jour les User-Agents des nouveaux bots IA (`DeepSeekBot`, `MistralBot`, `GrokBot`), incrémente la version mineure et fait un `git push`.
- Apify détecte le commit GitHub et **rebuild automatiquement l'Actor sur l'Apify Store** : vous conservez ainsi en permanence le badge très convoité **"Recently updated"** qui vous place en tête des résultats de recherche Apify !

### 2. Tenir sa comptabilité en 10 secondes par mois
Dès que vous recevez un virement d'Apify sur votre compte bancaire :
```bash
# Exemple : vous avez reçu un virement de 400 € d'Apify
python -m src.compta_manager add --ref "APIFY-NOV-2026" --gross 500.00 --fee 100.00 --desc "Vente Store Nov 2026"
```

Pour connaître les montants exacts à copier/coller sur le site de l'URSSAF et sur votre déclaration d'impôts (Cases `5HQ` ou `5TE`) :
```bash
python -m src.compta_manager report
```

🎉 **Félicitations, votre robot SaaS Apify Store est 100% opérationnel, auto-maintenu et conforme à la législation française !**
