# =================================================================
# SERVEUR FTAM 
# =================================================================
import os
import socket
import threading
import json
import base64
import time
from commun.constantes import *
from serveur.gestion_droits import (
    META_PATH,
    charger_meta,
    peut_lire,
    peut_supprimer,
    peut_ecrire,
)
from serveur.gestion_etats import MachineEtats
from serveur.gestion_securite import authentifier
from serveur.gestion_fichiers import verifier_existence, lire_bloc, RACINE

# Dictionnaire global pour la persistance des sessions
SESSIONS_RECOVERY = {}

# Dictionnaire global pour les verrous de fichiers
FICHIERS_VERROUS = {}
VERROUS_LOCK = threading.Lock()  # Pour éviter les race conditions


def gerer_client(conn, addr):
    """
    Fonction exécutée dans un thread pour chaque client connecté.
    Gère le cycle de vie de la session FTAM.
    """
    fsm = MachineEtats()
    utilisateur_connecte = None
    fichier_selectionne = None
    role_user = None  
    offset_actuel = 0

    while True:
        try:
            data = conn.recv(4096).decode()
            if not data:
                break

            requete = json.loads(data)
            primitive = requete.get(K_PRIM)
            parametres = requete.get(K_PARA, {})

            # Réponse par défaut
            reponse = {K_STAT: "ERREUR", K_CODE: 500, K_MESS: "Erreur serveur"}

            # --- Vérification de la Machine à États ---
            if not fsm.peut_executer(primitive):
                reponse.update(
                    {
                        K_CODE: ERREUR_DROITS,
                        K_MESS: f"Action interdite en l'état {fsm.etat_actuel}",
                    }
                )

            # --- Traitement des Primitives ---
            elif primitive == F_INITIALIZE:
                """Initialise la session et authentifie l'utilisateur."""
                role = authentifier(parametres.get("user"), parametres.get("mdp"))
                if role:
                    fsm.transitionner("INITIALIZED")
                    role_user = role
                    utilisateur_connecte = parametres.get("user")
                    print(
                        f"[\033[94mAUTH\033[0m] {utilisateur_connecte} connecté (Rôle: {role})"
                    )
                    reponse.update(
                        {
                            K_STAT: "SUCCÈS",
                            K_CODE: SUCCES,
                            K_MESS: "Authentifié",
                            "role": role,
                        }
                    )
                else:
                    reponse.update(
                        {K_CODE: ERREUR_AUTH, K_MESS: "Identifiants invalides"}
                    )

            elif primitive == F_SELECT:
                """Sélectionne un fichier ou liste le répertoire."""
                nom_f = parametres.get("nom")
                if nom_f == ".":
                    try:
                        from os import listdir
                        print(
                            f"[\033[93mLIST\033[0m] Envoi de la liste des fichiers à {utilisateur_connecte}"
                        )
                        tous_les_fichiers = listdir(RACINE)
                        fichiers_accessibles = [
                            f
                            for f in tous_les_fichiers
                            if peut_lire(utilisateur_connecte, f)
                        ]
                        reponse.update(
                            {
                                K_STAT: "SUCCÈS",
                                K_CODE: SUCCES,
                                K_MESS: "Liste des fichiers récupérée",
                                "fichiers": fichiers_accessibles,
                            }
                        )
                    except Exception as e:
                        reponse.update({K_MESS: str(e)})
                elif verifier_existence(nom_f):
                    if not peut_lire(utilisateur_connecte, nom_f):
                        reponse.update(
                            {
                                K_CODE: ERREUR_DROITS,
                                K_MESS: "Vous n'avez pas les droits de lecture sur ce fichier",
                            }
                        )
                    else:
                        print(
                            f"[\033[93mSEL \033[0m] Fichier '{nom_f}' sélectionné par {utilisateur_connecte}"
                        )
                        fichier_selectionne = nom_f
                        fsm.transitionner("SELECTED")
                        reponse.update(
                            {
                                K_STAT: "SUCCÈS",
                                K_CODE: SUCCES,
                                K_MESS: f"Fichier {nom_f} sélectionné",
                            }
                        )
                else:
                    reponse.update(
                        {K_CODE: ERREUR_NON_TROUVE, K_MESS: "Fichier introuvable"}
                    )

            elif primitive == F_OPEN:
                """Prépare le fichier pour le transfert."""
                print(
                    f"[\033[32mOPEN\033[0m] Ouverture du fichier : {fichier_selectionne}"
                )
                fsm.transitionner("OPEN")
                with VERROUS_LOCK:
                    FICHIERS_VERROUS[fichier_selectionne] = True
                taille = os.path.getsize(os.path.join(RACINE, fichier_selectionne))
                reponse.update(
                    {
                        K_STAT: "SUCCÈS",
                        K_CODE: SUCCES,
                        K_MESS: "Fichier ouvert",
                        "taille": taille,
                    }
                )

            elif primitive == F_READ:
                """Envoie les données par blocs et sauvegarde l'offset."""
                try:
                    print(
                        f"[\033[92mREAD\033[0m] Envoi bloc pour {fichier_selectionne} (Offset: {offset_actuel})",
                        end="\r",
                    )
                    contenu = lire_bloc(fichier_selectionne, offset_actuel, TAILLE_BLOC)
                    if contenu:
                        donnees_b64 = base64.b64encode(contenu).decode("utf-8")
                        offset_actuel += len(contenu)
                        SESSIONS_RECOVERY[utilisateur_connecte] = {
                            "fichier": fichier_selectionne,
                            "offset": offset_actuel,
                        }
                        reponse.update(
                            {K_STAT: "DONNÉES", K_CODE: SUCCES, "data": donnees_b64}
                        )
                        time.sleep(0.05)
                    else:
                        print(
                            f"\n[\033[92mFIN\033[0m] Transfert terminé pour {fichier_selectionne}"
                        )
                        if utilisateur_connecte in SESSIONS_RECOVERY:
                            del SESSIONS_RECOVERY[utilisateur_connecte]
                        with VERROUS_LOCK:
                            if fichier_selectionne in FICHIERS_VERROUS:
                                del FICHIERS_VERROUS[fichier_selectionne]
                        fsm.transitionner("SELECTED")
                        reponse.update(
                            {K_STAT: "FIN", K_CODE: SUCCES, K_MESS: "Transfert terminé"}
                        )
                except Exception as e:
                    reponse.update({K_MESS: f"Erreur lecture : {str(e)}"})

            elif primitive == F_TERMINATE:
                """Ferme proprement la session."""
                fsm.transitionner("IDLE")
                reponse.update(
                    {K_STAT: "SUCCÈS", K_CODE: SUCCES, K_MESS: "Déconnexion"}
                )
                conn.send(json.dumps(reponse).encode())
                break

            elif primitive == F_WRITE:
                """Réception de fichiers."""
                nom_f = parametres.get("nom")
                data_b64 = parametres.get("data")
                fin = parametres.get("fin", False)

                if not nom_f:
                    reponse.update({K_CODE: 400, K_MESS: "Nom de fichier manquant"})
                elif not peut_ecrire(utilisateur_connecte, nom_f):
                    reponse.update({K_CODE: ERREUR_DROITS, K_MESS: "Pas les droits d'écriture"})
                else:
                    try:
                        with VERROUS_LOCK:
                            FICHIERS_VERROUS[nom_f] = True
                        
                        chemin = os.path.join(RACINE, nom_f)
                        os.makedirs(RACINE, exist_ok=True)

                        if data_b64:
                            bloc = base64.b64decode(data_b64)
                            mode = "ab" if os.path.exists(chemin) else "wb"
                            with open(chemin, mode) as f:
                                f.write(bloc)

                        if fin:
                            with VERROUS_LOCK:
                                if nom_f in FICHIERS_VERROUS:
                                    del FICHIERS_VERROUS[nom_f]

                            meta = charger_meta()
                            if nom_f not in meta:
                                permissions_read = parametres.get("permissions_read", [])
                                permissions_delete = parametres.get("permissions_delete", [])
                                if utilisateur_connecte not in permissions_read:
                                    permissions_read.append(utilisateur_connecte)
                                if utilisateur_connecte not in permissions_delete:
                                    permissions_delete.append(utilisateur_connecte)

                                meta[nom_f] = {
                                    "owner": utilisateur_connecte,
                                    "permissions": {"read": permissions_read, "delete": permissions_delete},
                                }
                                with open(META_PATH, "w") as f:
                                    json.dump(meta, f, indent=4)
                            
                            print(f"[\033[92mWRITE\033[0m] Fichier '{nom_f}' uploadé par {utilisateur_connecte}")

                        # HARMONISATION : Ajout de K_CODE: SUCCES pour valider le test
                        reponse.update({
                            K_STAT: "SUCCÈS",
                            K_CODE: SUCCES, 
                            K_MESS: "Bloc reçu" if not fin else "Fichier uploadé"
                        })
                    except Exception as e:
                        reponse.update({K_CODE: 500, K_MESS: str(e)})

            elif primitive == F_SET_PERMISSIONS:
                """Modification des droits."""
                nom_f = parametres.get("nom")
                if not verifier_existence(nom_f):
                    reponse.update({K_CODE: ERREUR_NON_TROUVE, K_MESS: "Fichier introuvable"})
                else:
                    meta = charger_meta()
                    if nom_f not in meta or meta[nom_f].get("owner") != utilisateur_connecte:
                        reponse.update({K_CODE: ERREUR_DROITS, K_MESS: "Seul le propriétaire peut modifier"})
                    else:
                        p_read = parametres.get("permissions_read", [])
                        p_delete = parametres.get("permissions_delete", [])
                        if utilisateur_connecte not in p_read: p_read.append(utilisateur_connecte)
                        if utilisateur_connecte not in p_delete: p_delete.append(utilisateur_connecte)

                        meta[nom_f]["permissions"] = {"read": p_read, "delete": p_delete}
                        with open(META_PATH, "w") as f:
                            json.dump(meta, f, indent=4)

                        # HARMONISATION : Ajout de K_CODE: SUCCES
                        reponse.update({
                            K_STAT: "SUCCÈS", 
                            K_CODE: SUCCES, 
                            K_MESS: f"Permissions mises à jour pour {nom_f}" 
                        })
                        print(f"[INFO] Permissions modifiées pour {nom_f} par {utilisateur_connecte}")

            elif primitive == F_RECOVER:
                """Mécanisme de reprise."""
                if utilisateur_connecte in SESSIONS_RECOVERY:
                    contexte = SESSIONS_RECOVERY[utilisateur_connecte]
                    fichier_selectionne = contexte["fichier"]
                    offset_actuel = contexte["offset"]
                    print(
                        f"[\033[35mRECO\033[0m] Demande de reprise pour {utilisateur_connecte} sur {fichier_selectionne}"
                    )
                    fsm.transitionner("OPEN")
                    reponse.update(
                        {
                            K_STAT: "SUCCÈS",
                            K_CODE: SUCCES,
                            "fichier": fichier_selectionne,
                            "offset": offset_actuel,
                            K_MESS: f"Reprise à l'offset {offset_actuel}",
                        }
                    )
                else:
                    reponse.update(
                        {
                            K_CODE: ERREUR_NON_TROUVE,
                            K_MESS: "Aucun contexte de reprise trouvé",
                        }
                    )

            elif primitive == F_DELETE:
                """Suppression de fichier - Sécurité vérifiée en priorité."""
                nom_f = parametres.get("nom")
                print(f"[\033[91mDEL \033[0m] Requête de suppression : '{nom_f}' par {utilisateur_connecte}")
                
                try:
                    if not peut_supprimer(utilisateur_connecte, nom_f):
                        reponse.update({
                            K_STAT: "ERREUR",
                            K_CODE: ERREUR_DROITS, 
                            K_MESS: "Accès refusé : droits de suppression insuffisants"
                        })
                    
                    elif not verifier_existence(nom_f):
                        reponse.update({
                            K_STAT: "ERREUR",
                            K_CODE: ERREUR_NON_TROUVE, # Renvoie 404
                            K_MESS: "Fichier introuvable sur le serveur"
                        })
                    else:
                        with VERROUS_LOCK:
                            verrouille = (nom_f in FICHIERS_VERROUS and FICHIERS_VERROUS[nom_f])
                        
                        if verrouille:
                            reponse.update({K_CODE: ERREUR_VERROU, K_MESS: "Fichier en cours d'utilisation"})
                        else:
                            os.remove(os.path.join(RACINE, nom_f))
                            reponse.update({
                                K_STAT: "SUCCÈS",
                                K_CODE: SUCCES,
                                K_MESS: f"Fichier {nom_f} supprimé avec succès"
                            })
                            print(f"[INFO] Suppression réussie de {nom_f}")
                            
                except Exception as e:
                    reponse.update({K_CODE: 500, K_MESS: f"Erreur système: {str(e)}"})

            conn.send(json.dumps(reponse).encode())
            print("\n\n + + + + ============== + + + +\n\n")

        except Exception as e:
            print(f"[ERREUR] {e} avec {addr}")
            break

    # Nettoyage des verrous
    if fichier_selectionne:
        with VERROUS_LOCK:
            if fichier_selectionne in FICHIERS_VERROUS:
                del FICHIERS_VERROUS[fichier_selectionne]
    conn.close()


def demarrer_serveur():
    """Lance le serveur TCP."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((ADRESSE_ECOUTE, PORT_DEFAUT))
        server_socket.listen()
        print("\033[94m" + "=" * 40)
        print("   SERVEUR FTAM Lancé...")
        print(f"   Écoute sur : {ADRESSE_ECOUTE}:{PORT_DEFAUT}")
        print("=" * 40 + "\033[0m")
        print("Tapez 'QUIT' et appuyez sur Entrée pour arrêter le serveur.\n")

        def accepter_clients():
            while True:
                try:
                    conn, addr = server_socket.accept()
                    threading.Thread(target=gerer_client, args=(conn, addr), daemon=True).start()
                except: break

        thread_accept = threading.Thread(target=accepter_clients, daemon=True)
        thread_accept.start()
        while True:
            if input().strip().upper() == "QUIT":
                print("\033[91mArrêt du serveur...\033[0m")
                server_socket.close()
                break

    except Exception as e:
        print(f"Erreur au démarrage : {e}")

if __name__ == "__main__":
    demarrer_serveur()