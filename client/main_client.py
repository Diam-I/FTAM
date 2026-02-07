import json
import socket
import base64 
import os
from commun.constantes import *

class ClientFTAM:
    """
    Classe représentant le client FTAM (File Transfer Access and Management).
    Gère la communication avec le serveur via des PDUs au format JSON.
    """
    def __init__(self):
        """Initialise l'instance client avec une socket vide et un état déconnecté."""
        self.socket = None
        self.est_connecte = False
        self.session_id = None

    def envoyer_requete(self, primitive, params=None):
        """
        Envoie une requête (PDU) au serveur et attend une réponse.
        
        Args:
            primitive (str): Le nom de la primitive (ex: F-INITIALIZE).
            params (dict): Les paramètres associés à la requête.
            
        Returns:
            dict: La réponse JSON décodée du serveur, ou None en cas d'erreur.
        """
        if not self.socket:
            print("Erreur : Non connecté.")
            return None
        try:
            requete = {K_PRIM: primitive, K_PARA: params or {}}
            self.socket.send(json.dumps(requete).encode())
            reponse_data = self.socket.recv(4096).decode()
            return json.loads(reponse_data)
        except Exception as e:
            print(f"Erreur réseau : {e}")
            return None

    def connecter(self):
        """
        Initialise la connexion TCP et effectue l'authentification FTAM.
        Récupère le session_id fourni par le serveur pour la reprise sur incident.
        """
        adresse_ip = input("Entrez l'adresse IP du serveur : ")
        utilisateur = input("Nom d'utilisateur : ")
        mdp = input("Mot de passe : ")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((adresse_ip, PORT_DEFAUT))
            res = self.envoyer_requete(F_INITIALIZE, {"user": utilisateur, "mdp": mdp})
            if res and res.get(K_CODE) == SUCCES:
                self.session_id = res.get("session_id")
                print(f"Succès : {res.get(K_MESS)}")
                self.est_connecte = True
            else:
                print("Échec d'authentification.")
                self.socket.close()
                self.socket = None
        except Exception as e:
            print(f"Connexion impossible : {e}")

    def telecharger(self, nom_f):
        """
        Gère le cycle complet de téléchargement d'un fichier.
        Respecte la machine à états : SELECT -> OPEN -> READ.
        
        Args:
            nom_f (str): Le nom du fichier à récupérer sur le serveur.
        """
        # 1. Sélection (Obligatoire pour l'état SELECTED) 
        self.envoyer_requete(F_SELECT, {"nom": nom_f})
        # 2. Ouverture (État OPEN)
        self.envoyer_requete(F_OPEN)

        print(f"Téléchargement de {nom_f}...")
        if not os.path.exists("telechargements"): os.makedirs("telechargements")

        with open(f"telechargements/{nom_f}", "wb") as f:
            while True:
                res = self.envoyer_requete(F_READ)
                if res.get(K_STAT) == "DONNÉES":
                    # Décodage Base64 vers Binaire
                    f.write(base64.b64decode(res.get("data")))
                elif res.get(K_STAT) == "FIN":
                    print("Transfert terminé.")
                    break
                else:
                    print(f"Erreur : {res.get(K_MESS)}")
                    break

def afficher_menu():
    """Affiche les options disponibles à l'utilisateur."""
    print("\n=== Menu ===")
    print("1. Se connecter (F-INITIALIZE)")
    print("2. Lister les fichiers (F-SELECT)")
    print("3. Télécharger (F-READ)")
    print("4. Quitter")
    return input("Choisissez une option : ")

if __name__ == "__main__":
    client = ClientFTAM()
    while True:
        opt = afficher_menu()
        if opt == "1": 
            client.connecter()
        elif opt == "2" and client.est_connecte:
            print(client.envoyer_requete(F_SELECT, {"nom": "."}))
        elif opt == "3" and client.est_connecte:
            client.telecharger(input("Fichier : "))
        elif opt == "4": 
            break
        else:
            print("Option invalide , veuillew reassayer")