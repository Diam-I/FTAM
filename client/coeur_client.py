import socket
import json
import os
from commun.constantes import PORT_DEFAUT, TAILLE_BLOC


class ClientFTAM:
    def __init__(self):
        self.socket = None
        self.est_connecte = False
        self.session_id = None

    def envoyer_requete(self, primitive, params=None):
        # Envoie une PDU au format JSON et attend la réponse du serveur #
        if not self.socket:
            return {"statut": "ERREUR", "message": "Non connecté"}

        try:
            requete = {"primitive": primitive, "parametres": params or {}}
            self.socket.sendall(json.dumps(requete).encode())

            # Attente de la réponse du serveur #
            reponse_data = self.socket.recv(4096).decode()
            return json.loads(reponse_data)
        except Exception as e:
            return {"statut": "ERREUR", "message": str(e)}

    def connecter(self, ip, user, mdp):
        # Tente de se connecter au serveur et d'initialiser la session #
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, PORT_DEFAUT))

            res = self.envoyer_requete("F-INITIALIZE", {"user": user, "mdp": mdp})
            if res.get("statut") == "SUCCÈS":
                self.est_connecte = True
                self.session_id = res.get("session_id")
                return True
        except:
            self.socket = None
        return False

    def telecharger(self, nom_fichier, offset=0):
        # Sélection et ouverture du fichier #
        self.envoyer_requete("F-SELECT", {"nom": nom_fichier})
        self.envoyer_requete("F-OPEN", {"mode": "lecture"})

        # Si on reprend après un crash, on utilise F-RECOVER #
        if offset > 0:
            self.envoyer_requete("F-RECOVER", {"offset": offset})

        # Réception des données #
        with open(f"telechargements/{nom_fichier}", "ab") as f:
            while True:
                res = self.envoyer_requete("F-READ-DATA")
                if res.get("statut") == "TRANSFER_END":
                    break

                # On écrit le bloc binaire reçu #
                bloc_data = res.get("data").encode("latin-1")
                f.write(bloc_data)

        print(f"Transfert de {nom_fichier} terminé.")

    def deconnecter(self):
        # Finir la session et fermer la connexion #
        if self.socket:
            self.envoyer_requete("F-TERMINATE")
            self.socket.close()
            self.est_connecte = False
