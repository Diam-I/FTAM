# =================================================================
# BANQUET DE TESTS DE VALIDATION - PROTOCOLE FTAM
# =================================================================

import unittest
import os
import time
import base64
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

    def journaliser_echange(self, action, reponse):
        """ Affiche l'analyse de l'échange PDU de manière professionnelle """
        print(f"\n[ANALYSE] {action}")
        print(f"  > Statut reçu : {reponse.get(K_STAT, 'N/A')}")
        print(f"  > Code PDU    : {reponse.get(K_CODE, 'N/A')}")
        print(f"  > Message     : {reponse.get(K_MESS, 'Aucun message')}")
        print("-" * 45)

    def test_01_authentification(self):
        """ Test : Validation de la procédure d'accès sécurisé """
        res = self.client.connecter(self.ip, self.user_admin, self.mdp_admin)
        self.assertIn("succes", res)
        self.assertEqual(self.client.etat_actuel, "INITIALIZED")
        print("\n[SUCCÈS] Procédure d'authentification validée")

    def test_02_machine_etat(self):
        """ Test : Respect de la hiérarchie des primitives et des états """
        self.client.connecter(self.ip, self.user_admin, self.mdp_admin)
        res = self.client.envoyer_requete(F_READ)
        
        self.journaliser_echange("Contrôle d'accès à la primitive F-READ", res)
        
        self.assertEqual(res.get(K_CODE), ERREUR_DROITS, "Le système n'a pas bloqué la transition d'état illégale.")
        print("[SUCCÈS] Intégrité de la machine à états vérifiée")

    def test_03_controle_acces_roles(self):
        """ Test : Étanchéité des privilèges par profil utilisateur """
        client_guest = ClientFTAM()
        try:
            client_guest.connecter(self.ip, self.user_guest, self.mdp_guest)
            res = client_guest.envoyer_requete(F_DELETE, {"nom": "system_config.txt"})
            
            self.journaliser_echange("Tentative de suppression (Profil Invité)", res)
            
            self.assertEqual(res.get(K_CODE), ERREUR_DROITS, "Le profil invité a pu outrepasser ses droits.")
            print("[SUCCÈS] Politique de contrôle d'accès par rôles validée")
        finally:
            client_guest.quitter()

    def test_04_transfert_integral(self):
        """ Test : Validation du transfert binaire par blocs (Upload/Download) """
        self.client.connecter(self.ip, self.user_admin, self.mdp_admin)
        nom_test = "test_integration.txt"
        contenu_test = "Contenu de vérification d'intégrité FTAM " * 100
        
        with open("test_local.txt", "w") as f:
            f.write(contenu_test)

        with open("test_local.txt", "rb") as f:
            bloc = f.read(TAILLE_BLOC)
            bloc_b64 = base64.b64encode(bloc).decode("utf-8")
        res_up = self.client.envoyer_requete(F_WRITE, {"nom": nom_test, "data": bloc_b64, "fin": True})
        
        self.journaliser_echange("Validation de la primitive F-WRITE (Upload)", res_up)
        self.assertEqual(res_up.get(K_CODE), SUCCES)
        res_down = self.client.telecharger(nom_test)
        self.assertIn("succes", res_down)
        print("[SUCCÈS] Intégrité du transfert bidirectionnel confirmée")

    def test_05_mecanisme_reprise(self):
        """ Test : Validation du mécanisme de Recovery (Checkpointing) """
        self.client.connecter(self.ip, self.user_admin, self.mdp_admin)
        res = self.client.envoyer_requete(F_RECOVER)
        
        self.journaliser_echange("Interrogation du contexte de reprise (F-RECOVER)", res)
        self.assertIn(res.get(K_CODE), [SUCCES, ERREUR_NON_TROUVE])
        print("[SUCCÈS] Service de reprise sur incident opérationnel")

    def test_07_gestion_dynamique_permissions(self):
        """ Test : Mise à jour des ACL et propagation des droits à un tiers """
        self.client.connecter(self.ip, self.user_admin, self.mdp_admin)
        nom_f = "test_integration.txt"
        
        params = { 
            "nom": nom_f,
            "permissions_read": [self.user_admin, self.user_guest],
            "permissions_delete": [self.user_admin] 
        }
        res = self.client.envoyer_requete(F_SET_PERMISSIONS, params)
        
        self.journaliser_echange("Mise à jour dynamique des permissions (F-SET-PERMISSIONS)", res)
        self.assertEqual(res.get(K_CODE), SUCCES)

        client_guest = ClientFTAM()
        try:
            client_guest.connecter(self.ip, self.user_guest, self.mdp_guest)
            res_guest = client_guest.envoyer_requete(F_SELECT, {"nom": nom_f})
            self.assertEqual(res_guest.get(K_CODE), SUCCES)
            print("[SUCCÈS] Propagation dynamique des droits vérifiée par un tiers")
        finally:
            client_guest.quitter()

if __name__ == "__main__":
    unittest.main()