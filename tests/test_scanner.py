"""
Suite de tests unitaires pour eu-b2b-compliance-ai-auditor.
Exécutée automatiquement dans le pipeline GitHub Actions avant tout déploiement Apify.
"""

import unittest
from src.official_registries import validate_luhn, calculate_french_vat, clean_target_query
from src.web_ai_compliance_scanner import load_compliance_signatures, normalize_domain_url
from src.self_healing_parser import extract_regex_heuristics
from src.self_updater import bump_version
from src.compta_manager import URSSAF_COTISATIONS_RATE, ABATTEMENT_BNC, VERSEMENT_LIBERATOIRE_RATE


class TestComplianceAuditor(unittest.TestCase):

    def test_luhn_algorithm_validation(self):
        # SIREN valide Doctolib (794598813)
        self.assertTrue(validate_luhn("794598813"))
        # SIRET valide (14 chiffres - siège Doctolib)
        self.assertTrue(validate_luhn("79459881300077"))
        # SIREN invalide
        self.assertFalse(validate_luhn("794598814"))
        self.assertFalse(validate_luhn("123"))

    def test_french_vat_calculation(self):
        # Formule officielle FR + (12 + 3 * (SIREN % 97)) % 97 + SIREN
        # 794598813 % 97 = 29 -> 12 + 3*29 = 99 -> 99 % 97 = 2 -> FR14? Wait: 794598813 % 97
        vat = calculate_french_vat("794598813")
        self.assertEqual(vat, "FR14794598813")

        # Test autre entreprise
        vat2 = calculate_french_vat("534966688")
        self.assertTrue(vat2.startswith("FR"))
        self.assertEqual(len(vat2), 13)

    def test_clean_target_query(self):
        self.assertEqual(clean_target_query("https://www.doctolib.fr/recherche"), "doctolib")
        self.assertEqual(clean_target_query("https://mirakl.com"), "mirakl")
        self.assertEqual(clean_target_query("794598813"), "794598813")

    def test_compliance_signatures_integrity(self):
        signatures = load_compliance_signatures()
        self.assertIn("ai_crawlers", signatures)
        self.assertIn("gdpr_trackers", signatures)
        self.assertGreater(len(signatures["ai_crawlers"]), 5)
        self.assertGreater(len(signatures["gdpr_trackers"]), 3)

        # Vérifier que GPTBot, PerplexityBot et OAI-SearchBot sont catalogués
        names = [c["name"] for c in signatures["ai_crawlers"]]
        self.assertIn("GPTBot", names)
        self.assertIn("OAI-SearchBot", names)
        self.assertIn("PerplexityBot", names)

    def test_self_healing_regex_heuristics(self):
        dirty_html = """
        <html>
            <body>
                Contactez-nous à support@entreprise-test.com ou privacy@entreprise-test.com.
                Société SAS au capital de 10000€. SIREN : 794 598 813.
                SIRET 794 598 813 00077 - TVA FR14794598813.
            </body>
        </html>
        """
        extracted = extract_regex_heuristics(dirty_html)
        self.assertIn("794598813", extracted["siren_candidates"])
        self.assertIn("79459881300077", extracted["siret_candidates"])
        self.assertIn("support@entreprise-test.com", extracted["emails"])
        self.assertIn("FR14794598813", extracted["vat_candidates"])

    def test_version_bumping(self):
        self.assertEqual(bump_version("1.0.0", "patch"), "1.0.1")
        self.assertEqual(bump_version("1.0.9", "patch"), "1.0.10")
        self.assertEqual(bump_version("1.2.5", "minor"), "1.3.0")

    def test_fiscal_calculations(self):
        ca = 1000.0
        cotisations = ca * URSSAF_COTISATIONS_RATE
        self.assertAlmostEqual(cotisations, 212.0)
        
        # Abattement 34% BNC pour case 5HQ
        base_5hq = ca * (1 - ABATTEMENT_BNC)
        self.assertAlmostEqual(base_5hq, 660.0)

        # Versement libératoire case 5TE
        ir_liberatoire = ca * VERSEMENT_LIBERATOIRE_RATE
        self.assertAlmostEqual(ir_liberatoire, 22.0)


if __name__ == "__main__":
    unittest.main()
