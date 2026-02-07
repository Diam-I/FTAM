# =================================================================
# SERVEUR FTAM - GESTIONNAIRE DE CONNEXION
# =================================================================
import socket
import threading
import json
import base64
from commun.constantes import *
from serveur.gestion_etats import MachineEtats
from serveur.gestion_securite import authentifier
from serveur.gestion_fichiers import verifier_existence, lire_bloc, RACINE
# Dictionnaire global pour la persistance des sessions 
# Format : { "nom_utilisateur": {"fichier": "nom", "offset": 1024} }
SESSIONS_RECOVERY = {}

def gerer_client(conn, addr):
    """
    Fonction exécutée dans un thread pour chaque client connecté.
    Gère le cycle de vie de la session FTAM.
    """
    fsm = MachineEtats() 
    utilisateur_connecte = None
    fichier_selectionne = None
    offset_actuel = 0
    
    while True:
        try:
            data = conn.recv(4096).decode()
            if not data: break
            
            requete = json.loads(data)
            primitive = requete.get(K_PRIM)
            parametres = requete.get(K_PARA, {})
            
            # Réponse par défaut (Erreur)
            reponse = {K_STAT: "ERREUR", K_CODE: 500, K_MESS: "Erreur serveur"}

            # --- Vérification de la Machine à États ---
            if not fsm.peut_executer(primitive):
                reponse.update({K_CODE: ERREUR_DROITS, K_MESS: f"Action interdite en l'état {fsm.etat_actuel}"})
            
            # --- Traitement des Primitives ---
            elif primitive == F_INITIALIZE:
                """Initialise la session et authentifie l'utilisateur."""
                role = authentifier(parametres.get("user"), parametres.get("mdp"))
                if role:
                    fsm.transitionner("INITIALIZED") # [cite: 90, 436]
                    utilisateur_connecte = parametres.get("user")
                    reponse.update({K_STAT: "SUCCÈS", K_CODE: SUCCES, K_MESS: "Authentifié", "role": role})
                else:
                    reponse.update({K_CODE: ERREUR_AUTH, K_MESS: "Identifiants invalides"})

            elif primitive == F_SELECT:
                """Sélectionne un fichier ou liste le répertoire."""
                nom_f = parametres.get("nom")
                if nom_f == ".": # Listage du répertoire
                    try:
                        from os import listdir
                        reponse.update({K_STAT: "SUCCÈS", K_CODE: SUCCES, "fichiers": listdir(RACINE)})
                    except Exception as e:
                        reponse.update({K_MESS: str(e)})
                elif verifier_existence(nom_f):
                    fichier_selectionne = nom_f
                    fsm.transitionner("SELECTED") # [cite: 92, 438]
                    reponse.update({K_STAT: "SUCCÈS", K_CODE: SUCCES, K_MESS: f"Fichier {nom_f} sélectionné"})
                else:
                    reponse.update({K_CODE: ERREUR_NON_TROUVE, K_MESS: "Fichier introuvable"})

            elif primitive == F_OPEN:
                """Prépare le fichier pour le transfert."""
                fsm.transitionner("OPEN") # [cite: 94, 440]
                offset_actuel = 0
                reponse.update({K_STAT: "SUCCÈS", K_CODE: SUCCES, K_MESS: "Fichier ouvert"})

        
            elif primitive == F_READ:
                """
                Envoie les données par blocs et sauvegarde l'offset pour le Recovery.
                """
                try:
                    contenu = lire_bloc(fichier_selectionne, offset_actuel, TAILLE_BLOC) # [cite: 101, 450]
                    if contenu:
                        # Envoi en Base64 pour compatibilité JSON
                        donnees_b64 = base64.b64encode(contenu).decode('utf-8')
                        offset_actuel += len(contenu)
                        SESSIONS_RECOVERY[utilisateur_connecte] = {
                            "fichier": fichier_selectionne,
                            "offset": offset_actuel
                        }
                        reponse.update({K_STAT: "DONNÉES", K_CODE: SUCCES, "data": donnees_b64})
                    else:
                        if utilisateur_connecte in SESSIONS_RECOVERY:
                            del SESSIONS_RECOVERY[utilisateur_connecte]
                        reponse.update({K_STAT: "FIN", K_CODE: SUCCES, K_MESS: "Transfert terminé"})
                except Exception as e:
                    reponse.update({K_MESS: f"Erreur lecture : {str(e)}"})

            elif primitive == F_TERMINATE:
                """Ferme proprement la session."""
                fsm.transitionner("IDLE")
                reponse.update({K_STAT: "SUCCÈS", K_CODE: SUCCES, K_MESS: "Déconnexion"})
                conn.send(json.dumps(reponse).encode())
                break

            elif primitive == F_RECOVER:
                """
                Restaure le contexte de transfert après une coupure.
                Vérifie si une session précédente existe pour cet utilisateur.
                """
                if utilisateur_connecte in SESSIONS_RECOVERY:
                    contexte = SESSIONS_RECOVERY[utilisateur_connecte]
                    fichier_selectionne = contexte["fichier"]
                    offset_actuel = contexte["offset"]
                    fsm.transitionner("OPEN") # On revient directement en état ouvert
                    reponse.update({
                        K_STAT: "SUCCÈS", 
                        K_CODE: SUCCES, 
                        K_MESS: f"Reprise de {fichier_selectionne} à l'offset {offset_actuel}"
                    })
                else:
                    reponse.update({K_CODE: ERREUR_NON_TROUVE, K_MESS: "Aucun contexte de reprise trouvé"})


            conn.send(json.dumps(reponse).encode())
            
        except Exception as e:
            print(f"[ERREUR] {e} avec {addr}")
            break
    conn.close()

def demarrer_serveur():
    """Lance le serveur TCP et écoute les connexions entrantes."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((ADRESSE_ECOUTE, PORT_DEFAUT))
        s.listen()
        print(f"[SERVEUR] Écoute sur le port {PORT_DEFAUT}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=gerer_client, args=(conn, addr)).start()

if __name__ == "__main__":
    demarrer_serveur()