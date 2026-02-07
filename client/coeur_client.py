# =================================================================
# CLIENT FTAM - COEUR LOGIQUE
# =================================================================
import socket
import json
import os
import base64
from commun.constantes import *

class ClientFTAM:
    """
    Classe implémentant la logique métier du protocole FTAM côté client.
    Elle encapsule les méthodes de connexion, de transfert et de gestion de session.
    """
    def __init__(self):
        """Initialise un client avec une socket inactive et un état de session vierge."""
        self.socket = None
        self.est_connecte = False

    def envoyer_requete(self, primitive, params=None):
        if not self.socket:
            print("Erreur : Non connecté.")
            return None
        try:
            requete = {K_PRIM: primitive, K_PARA: params or {}}
            self.socket.send(json.dumps(requete).encode())
            
            reponse_data = self.socket.recv(4096).decode()
            reponse = json.loads(reponse_data)
            return reponse
        except Exception as e:
            print(f"Erreur : {e}")
            return None

    def connecter(self, ip, user, mdp):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, PORT_DEFAUT))

            res = self.envoyer_requete(F_INITIALIZE, {"user": user, "mdp": mdp})
            if res and res.get(K_CODE) == SUCCES:
                self.est_connecte = True
                print("Connexion réussie.")
                return True
        except:
            self.socket = None
        return False

    def telecharger(self, nom_fichier, offset=0):
        # 1. Sélection et Ouverture 
        self.envoyer_requete(F_SELECT, {"nom": nom_fichier})
        self.envoyer_requete(F_OPEN, {"mode": "lecture"})

        # 2. Gestion de la reprise sur incident
        if offset > 0:
            self.envoyer_requete(F_RECOVER, {"offset": offset})

        # 3. Réception et Décodage des données 
        if not os.path.exists("telechargements"):
            os.makedirs("telechargements")

        with open(f"telechargements/{nom_fichier}", "wb") as f:
            while True:
                res = self.envoyer_requete(F_READ)
                
                if res.get(K_STAT) == "FIN":
                    print("Téléchargement fini.")
                    break
                
                if res.get(K_STAT) == "DONNÉES":
                    donnees_binaires = base64.b64decode(res.get("data"))
                    f.write(donnees_binaires)
                else:
                    print(f"Erreur : {res.get(K_MESS)}")
                    break

    def deconnecter(self):
        if self.socket:
            self.envoyer_requete(F_TERMINATE)
            self.socket.close()
            self.est_connecte = False