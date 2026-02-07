# =================================================================
# GESTIONNAIRE DE CONNEXION CLIENT 
# Rôle : Reçoit les requêtes JSON, les décode et utilise la 
#        Machine à États pour valider et exécuter les primitives.
# =================================================================
import socket
import threading
import json
import base64  # Pour envoyer les données binaires proprement en JSON
from commun.constantes import *
from serveur.gestion_etats import MachineEtats
from serveur.gestion_securite import authentifier
from serveur.gestion_fichiers import verifier_existence, lire_bloc

def gerer_client(conn, addr):
    fsm = MachineEtats() # Initialisation à l'état IDLE 
    utilisateur_connecte = None
    fichier_selectionne = None
    offset_actuel = 0
    
    while True:
        try:
            data = conn.recv(4096).decode()
            if not data: break
            
            requete = json.loads(data)
            primitive = requete.get("primitive")
            parametres = requete.get("parametres", {})
            reponse = {"statut": "ERREUR", "code": 500, "message": "Erreur interne"}

            # --- Vérification de la Machine à États ---
            if not fsm.peut_executer(primitive):
                reponse = {"statut": "ERREUR", "code": ERREUR_DROITS, "message": f"Action {primitive} interdite dans l'état {fsm.etat_actuel}"}
            
            # --- Traitement des Primitives ---
            elif primitive == F_INITIALIZE:
                role = authentifier(parametres.get("user"), parametres.get("mdp"))
                if role:
                    fsm.transitionner("INITIALIZED") # Passage à l'état INITIALIZED [cite: 90, 436]
                    utilisateur_connecte = parametres.get("user")
                    reponse = {"statut": "SUCCÈS", "code": SUCCES, "role": role}
                else:
                    reponse = {"statut": "ERREUR", "code": ERREUR_AUTH, "message": "Identifiants invalides"}

            elif primitive == F_SELECT:
                nom_f = parametres.get("nom")
                
                # Si le client demande ".", on liste le contenu du répertoire de stockage
                if nom_f == ".":
                    try:
                        from os import listdir
                        from serveur.gestion_fichiers import RACINE
                        
                        fichiers = listdir(RACINE) # Récupère la liste des fichiers réels
                        fsm.transitionner("SELECTED")
                        reponse = {
                            "statut": "SUCCÈS", 
                            "code": SUCCES, 
                            "fichiers": fichiers # On renvoie la liste à Amina
                        }
                    except Exception as e:
                        reponse = {"statut": "ERREUR", "code": 500, "message": str(e)}
                        
                # Si c'est un nom de fichier précis, on vérifie son existence
                elif verifier_existence(nom_f):
                    fichier_selectionne = nom_f
                    fsm.transitionner("SELECTED")
                    reponse = {"statut": "SUCCÈS", "code": SUCCES, "fichier": nom_f}
                else:
                    reponse = {"statut": "ERREUR", "code": ERREUR_NON_TROUVE, "message": "Fichier absent"}


            elif primitive == F_OPEN:
                # Mode lecture ou écriture spécifié par le client [cite: 93, 439]
                fsm.transitionner("OPEN") # Passage à l'état OPEN [cite: 94, 440]
                offset_actuel = 0 # Réinitialisation pour une nouvelle lecture
                reponse = {"statut": "SUCCÈS", "code": SUCCES, "message": f"Fichier {fichier_selectionne} prêt"}

            elif primitive == F_READ:
                # Lecture par bloc de 1024 octets [cite: 101, 450]
                try:
                    contenu_binaire = lire_bloc(fichier_selectionne, offset_actuel, TAILLE_BLOC)
                    if contenu_binaire:
                        # Encodage en Base64 car le JSON ne supporte pas le binaire pur
                        donnees_encodees = base64.b64encode(contenu_binaire).decode('utf-8')
                        offset_actuel += len(contenu_binaire)
                        reponse = {"statut": "DONNÉES", "code": SUCCES, "data": donnees_encodees}
                    else:
                        reponse = {"statut": "FIN", "code": SUCCES, "message": "Fin du transfert"}
                except Exception as e:
                    reponse = {"statut": "ERREUR", "code": 500, "message": str(e)}

            elif primitive == F_TERMINATE:
                fsm.transitionner("IDLE")
                reponse = {"statut": "SUCCÈS", "code": SUCCES, "message": "Session terminée"}
                conn.send(json.dumps(reponse).encode())
                break # On sort de la boucle pour fermer la socket

            conn.send(json.dumps(reponse).encode())
            
        except Exception as e:
            print(f"[ERREUR] {e} avec {addr}")
            break
    conn.close()

def demarrer_serveur():
    # Création de la socket TCP/IP conforme au schéma réseau 
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((ADRESSE_ECOUTE, PORT_DEFAUT))
        s.listen()
        print(f"[SERVEUR] En attente sur le port {PORT_DEFAUT}...")
        while True:
            conn, addr = s.accept()
            # Un thread par client pour gérer la concurrence
            threading.Thread(target=gerer_client, args=(conn, addr)).start()

if __name__ == "__main__":
    demarrer_serveur()