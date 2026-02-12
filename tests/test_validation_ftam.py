# =================================================================
# TESTS DE VALIDATION 
# =================================================================

import unittest
import os
import time
from client.coeur_client import ClientFTAM
from commun.constantes import *

class TestFTAM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ClientFTAM()
        cls.ip = "127.0.0.1"
        cls.user_admin = "salia"
        cls.mdp_admin = "stri2026"
        cls.user_guest = "invite"
        cls.mdp_guest = "guest"

    def setUp(self):
        time.sleep(0.1)

    def tearDown(self):
        if self.client.socket:
            try:
                self.client.quitter()
            except:
                pass

    def inspecter_reponse(self, titre, reponse):
        """ Affiche le contenu de la réponse pour le diagnostic """
        print(f"\n--- DEBUG: {titre} ---")
        print(f"Contenu reçu: {reponse}")
        print(f"Code présent: {K_CODE in reponse} (Valeur: {reponse.get(K_CODE)})")
        print(f"Statut présent: {K_STAT in reponse} (Valeur: {reponse.get(K_STAT)})")
        print("-" * 30)

    def test_01_connexion_reussite(self):
        """ Test : Authentification valide """
        res = self.client.connecter(self.ip, self.user_admin, self.mdp_admin)
        self.assertIn("succes", res)
        self.assertEqual(self.client.etat_actuel, "INITIALIZED")
        print("\n[OK] Test Connexion réussie")

    def test_02_machine_etat_invalid(self):
        """ Test : Respect de la hiérarchie des états """
        self.client.connecter(self.ip, self.user_admin, self.mdp_admin)
        self.client.etat_actuel = "INITIALIZED"
        res = self.client.envoyer_requete(F_READ)
        
        self.inspecter_reponse("F-READ invalide", res)
        
        self.assertEqual(res.get(K_CODE), ERREUR_DROITS, "Le serveur n'a pas renvoyé le code 403 attendu.")
        print("[OK] Test Protection Machine à États")

    def test_03_securite_roles(self):
        """ Test : Contrôle d'accès par rôles """
        client_guest = ClientFTAM()
        try:
            client_guest.connecter(self.ip, self.user_guest, self.mdp_guest)
            res = client_guest.envoyer_requete(F_DELETE, {"nom": "system_config.txt"})
            self.inspecter_reponse("F-DELETE par invité", res)
            self.assertEqual(res.get(K_CODE), ERREUR_DROITS, "L'invité a pu supprimer ou n'a pas reçu de code 403.")
            print("[OK] Test Sécurité : Refus suppression pour invité")
        finally:
            client_guest.quitter()

    def test_04_transfert_et_verrou(self):
        """ Test : Transfert complet """
        self.client.connecter(self.ip, self.user_admin, self.mdp_admin)
        nom_test = "test_integration.txt"
        contenu_test = "Contenu de test pour FTAM " * 100
        with open("test_local.txt", "w") as f:
            f.write(contenu_test)
        import base64
        with open("test_local.txt", "rb") as f:
            bloc = f.read(TAILLE_BLOC)
            bloc_b64 = base64.b64encode(bloc).decode("utf-8")
        res_up = self.client.envoyer_requete(F_WRITE, {"nom": nom_test, "data": bloc_b64, "fin": True})
        
        self.inspecter_reponse("F-WRITE (Upload brut)", res_up)
        self.assertEqual(res_up.get(K_CODE), SUCCES, "Le téléversement n'a pas reçu le code 200.")
        res_down = self.client.telecharger(nom_test)
        self.assertIn("succes", res_down)
        print("[OK] Test Transfert Intégral validé")

    def test_05_reprise_incident(self):
        """ Test : Mécanisme de reprise """
        self.client.connecter(self.ip, self.user_admin, self.mdp_admin)
        res = self.client.envoyer_requete(F_RECOVER)
        
        self.inspecter_reponse("F-RECOVER", res)
        
        self.assertIn(res.get(K_CODE), [SUCCES, ERREUR_NON_TROUVE], "Le serveur a bloqué le RECOVER (403 ?) ou crashé.")
        print("[OK] Test Mécanisme de Reprise")

    def test_07_changement_permissions(self):
        """ Test : Modification dynamique des droits """
        self.client.connecter(self.ip, self.user_admin, self.mdp_admin)
        nom_f = "test_integration.txt"
        
        params = { "nom": nom_f,"permissions_read": [self.user_admin, self.user_guest],"permissions_delete": [self.user_admin] }
        res = self.client.envoyer_requete(F_SET_PERMISSIONS, params)
        
        self.inspecter_reponse("F-SET-PERMISSIONS brute", res)
        
        self.assertEqual(res.get(K_CODE), SUCCES, "Le serveur doit renvoyer le code 200 après modification.")
        client_guest = ClientFTAM()
        try:
            client_guest.connecter(self.ip, self.user_guest, self.mdp_guest)
            res_guest = client_guest.envoyer_requete(F_SELECT, {"nom": nom_f})
            self.assertEqual(res_guest.get(K_CODE), SUCCES, "L'invité devrait avoir accès au fichier après mise à jour.")
            print("[OK] Test : Droits mis à jour et vérifiés par un tiers")
        finally:
            client_guest.quitter()

if __name__ == "__main__":
    unittest.main()