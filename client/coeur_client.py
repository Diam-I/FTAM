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
        self.session_id = None
        self.utilisateur = None
        self.role = None
        self.etat_actuel = "IDLE"

    def envoyer_requete(self, primitive, params=None):
        """
        Envoie une requête (PDU) au serveur et attend une réponse.
        """
        if not self.socket:
            return {"erreur": "Non connecté"}
        try:
            requete = {K_PRIM: primitive, K_PARA: params or {}}
            self.socket.send(json.dumps(requete).encode())
            self.socket.settimeout(5.0)
            reponse_data = self.socket.recv(4096).decode()
            reponse = json.loads(reponse_data)
            if reponse.get(K_CODE) == SUCCES:
                self.mettre_a_jour_etat(primitive)
            return reponse
        except socket.timeout:
            return {"erreur": "Le serveur ne répond pas (Timeout)"}
        except Exception as e:
            return {"erreur": f"Erreur réseau : {e}"}

    def mettre_a_jour_etat(self, primitive):
        """Met à jour l'état actuel de la machine à états."""
        if primitive == F_INITIALIZE:
            self.etat_actuel = "INITIALIZED"
        elif primitive == F_SELECT:
            self.etat_actuel = "SELECTED"
        elif primitive == F_OPEN:
            self.etat_actuel = "OPEN"
        elif primitive == F_READ:
            self.etat_actuel = "SELECTED"
        elif primitive == F_TERMINATE:
            self.etat_actuel = "IDLE"

    def connecter(self, ip, utilisateur, mdp):
        """Initialise la connexion TCP et effectue l'authentification FTAM."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, PORT_DEFAUT))
            res = self.envoyer_requete(F_INITIALIZE, {"user": utilisateur, "mdp": mdp})
            if res.get(K_CODE) == SUCCES:
                self.session_id = res.get("session_id")
                self.role = res.get("role")
                self.est_connecte = True
                self.utilisateur = utilisateur
                return {
                    "succes": f"Connecté avec succès en tant que {utilisateur} ({self.role})"
                }
            else:
                self.socket.close()
                self.socket = None
                return {"erreur": "Échec d'authentification"}
        except Exception as e:
            return {"erreur": f"Connexion impossible : {e}"}

    def lister_fichiers(self):
        """Liste les fichiers distants."""
        res = self.envoyer_requete(F_SELECT, {"nom": "."})
        if res.get(K_CODE) == SUCCES:
            return {"fichiers": res.get("fichiers", [])}
        else:
            return {"erreur": "Impossible de lister les fichiers"}

    def telecharger(self, nom_f, offset=0):
        """Télécharge un fichier distant, reprend automatiquement si offset fourni."""
        # Sélection du fichier
        res_select = self.envoyer_requete(F_SELECT, {"nom": nom_f})
        if not res_select or res_select.get(K_CODE) != SUCCES:
            return {"erreur": f"Fichier '{nom_f}' introuvable sur le serveur."}

        # Ouverture du fichier
        res_open = self.envoyer_requete(F_OPEN)
        if not res_open or res_open.get(K_CODE) != SUCCES:
            return {"erreur": "Impossible d'ouvrir le fichier distant."}
        self.taille_fichier = res_open.get("taille", 0)

        # Dossier utilisateur
        dossier_utilisateur = os.path.join("telechargements", self.utilisateur)
        if not os.path.exists(dossier_utilisateur):
            os.makedirs(dossier_utilisateur)

        mode_ouverture = "ab" if offset > 0 else "wb"
        chemin_fichier = os.path.join(dossier_utilisateur, nom_f)

        with open(chemin_fichier, mode_ouverture) as f:
            if offset > 0:
                f.seek(offset)
            telecharge = offset
            while True:
                res = self.envoyer_requete(F_READ)
                if not res:
                    return {"erreur": "Erreur de lecture"}
                if res.get(K_STAT) == "DONNÉES":
                    bloc = base64.b64decode(res.get("data"))
                    f.write(bloc)
                    telecharge += len(bloc)
                    if self.taille_fichier > 0:
                        pourcent = (telecharge / self.taille_fichier) * 100
                        print(
                            f"Téléchargé : {telecharge} / {self.taille_fichier} bytes ({pourcent:.2f}%)",
                            end="\r",
                        )
                elif res.get(K_STAT) == "FIN":
                    print(
                        f"Téléchargement de '{nom_f}' terminé. Total : {telecharge} bytes."
                    )
                    break
                else:
                    return {"erreur": res.get(K_MESS)}
        return {"succes": f"Téléchargement de '{nom_f}' terminé"}

    def reprendre_telechargement(self, nom_fichier):
        """Permet de reprendre un téléchargement à partir de l'offset fourni par le serveur."""
        res = self.envoyer_requete(F_RECOVER)
        if res.get(K_CODE) == SUCCES:
            offset = int(res.get("offset", 0))
            print(f"[INFO] Reprise à partir de {offset} octets")

            return self.telecharger(nom_fichier, offset=offset)
        else:
            return {"erreur": res.get(K_MESS)}

    def quitter(self):
        """Ferme proprement la session FTAM."""
        if self.socket and self.est_connecte:
            self.envoyer_requete(F_TERMINATE)
            self.socket.close()
        self.socket = None
        self.est_connecte = False
        self.etat_actuel = "IDLE"
        print(f"[Info] Fermeture de la session cliente .....")

    def supprimer_fichier(self, nom_f):
        """Demande la suppression d'un fichier sur le serveur."""
        res = self.envoyer_requete(F_DELETE, {"nom": nom_f})
        if res.get(K_CODE) == SUCCES:
            return {"succes": res.get(K_MESS)}
        else:
            return {"erreur": res.get(K_MESS)}

    def uploader(
        self, chemin_local, nom_distant, permissions_read=None, permissions_delete=None
    ):
        """Upload d'un fichier local vers le serveur par blocs."""
        if not os.path.exists(chemin_local):
            return {"erreur": f"Fichier local '{chemin_local}' introuvable"}

        taille = os.path.getsize(chemin_local)
        envoye = 0
        with open(chemin_local, "rb") as f:
            while bloc := f.read(TAILLE_BLOC):
                bloc_b64 = base64.b64encode(bloc).decode("utf-8")
                res = self.envoyer_requete(
                    F_WRITE, {"nom": nom_distant, "data": bloc_b64}
                )
                if res.get(K_CODE) != SUCCES:
                    return {"erreur": res.get(K_MESS)}
                envoye += len(bloc)
                pourcent = (envoye / taille) * 100
                print(f"Upload : {envoye}/{taille} bytes ({pourcent:.2f}%)", end="\r")

        # Envoyer le signal de fin avec les permissions
        params_fin = {"nom": nom_distant, "fin": True}
        if permissions_read is not None:
            params_fin["permissions_read"] = permissions_read
        if permissions_delete is not None:
            params_fin["permissions_delete"] = permissions_delete

        res_fin = self.envoyer_requete(F_WRITE, params_fin)
        if res_fin.get(K_CODE) == SUCCES:
            print(f"\nUpload de '{nom_distant}' terminé.")
            return {"succes": f"Fichier '{nom_distant}' uploadé avec succès"}
        else:
            return {"erreur": res_fin.get(K_MESS)}

    def set_permissions(
        self, nom_fichier, permissions_read=None, permissions_delete=None
    ):
        """Modifie les permissions d'un fichier existant.
        Si aucune permission n'est spécifiée, retourne une erreur.
        """
        if permissions_read is None and permissions_delete is None:
            return {"erreur": "Aucune permission spécifiée"}

        params = {"nom": nom_fichier}
        if permissions_read is not None:
            params["permissions_read"] = permissions_read
        if permissions_delete is not None:
            params["permissions_delete"] = permissions_delete

        res = self.envoyer_requete(F_SET_PERMISSIONS, params)
        if res.get(K_CODE) == SUCCES:
            return {"succes": res.get(K_MESS)}
        else:
            return {"erreur": res.get(K_MESS)}
