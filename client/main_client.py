import json
import pwd
import socket
import threading
from commun.constantes import PORT_DEFAUT, ADRESSE_ECOUTE
import sys


class ClientFTAM:
    def __init__(self):
        self.socket = None
        self.est_connecte = False

    def envoyer_requete(self, primitive, params=None):
        # Envoie une PDU au format JSON et attend la réponse #
        if not self.socket:
            print("Erreur : Non connecté au serveur.")
            return None

        try:
            requete = {"primitive": primitive, "parametres": params or {}}
            self.socket.send(json.dumps(requete).encode())
            reponse_data = self.socket.recv(4096).decode()
            reponse = json.loads(reponse_data)
            return reponse

        except Exception as e:
            print(f"Erreur réseau : {e}")
            return None

    def connecter(self):
        # Demande les informations de connexion et tentation de connexion au serveur #
        adresse_ip = input("Entrez l'adresse IP du serveur : ")
        utilisateur = input("Nom d'utilisateur : ")
        motDePasse = input("Mot de passe : ")

        try:
            # Ouvrire la connexion au serveur #
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((adresse_ip, PORT_DEFAUT))

            # Tentative d'authentification (F-INITIALIZE) #
            res = self.envoyer_requete(
                "F-INITIALIZE", {"user": utilisateur, "mdp": motDePasse}
            )

            if res and res.get("statut") == "SUCCÈS":
                print("Connexion réussie !")
                self.est_connecte = True
            else:
                print(f"Échec : {res.get('message', 'Erreur inconnue')}")
                self.socket.close()
                self.socket = None
        except Exception as e:
            print(f"Impossible de joindre le serveur : {e}")


def afficher_menu():
    # Affiche le menu principal du client #
    print("\n=== Menu Client FTAM ===")
    print("1. Se connecter (F-INITIALIZE)")
    print("2. Lister les fichiers (F-SELECT)")
    print("3. Télécharger (F-READ)")
    print("4. Quitter")
    return input("Choisissez une option : ")


if __name__ == "__main__":
    # Point d'entrée du client FTAM #
    client = ClientFTAM()

    while True:
        option = afficher_menu()
        if option == "1":
            client.connecter()
        elif option == "2" and client.est_connecte:
            res = client.envoyer_requete("F-SELECT", {"nom": "."})
            print(f"Serveur dit : {res}")
        elif option == "3" and client.est_connecte:
            nom_f = input("Nom du fichier : ")
            res = client.envoyer_requete(
                "F-OPEN", {"mode": "lecture", "fichier": nom_f}
            )
            print(f"Réponse : {res}")
        elif option == "4":
            break
        else:
            print("Option invalide ou vous n'êtes pas connecté.")
