# =================================================================
# GESTIONNAIRE DE CONNEXION CLIENT 
# Rôle : Reçoit les requêtes JSON, les décode et utilise la 
#        Machine à États pour valider et exécuter les primitives.
# =================================================================
import socket
import threading
from commun.constantes import PORT_DEFAUT, ADRESSE_ECOUTE
import json
from serveur.gestion_etats import MachineEtats
from serveur.gestion_securite import authentifier

def gerer_client(conn, addr):
    fsm = MachineEtats() # Initialisation à l'état IDLE
    utilisateur_connecte = None
    
    while True:
        try:
            data = conn.recv(4096).decode()
            if not data: break
            
            requete = json.loads(data)
            primitive = requete.get("primitive")
            parametres = requete.get("parametres", {})

            if primitive == "F-INITIALIZE": # [cite: 382, 496]
                role = authentifier(parametres.get("user"), parametres.get("mdp"))
                if role:
                    fsm.transitionner("INITIALIZED") # Passage à l'état INITIALIZED [cite: 315]
                    utilisateur_connecte = parametres.get("user")
                    reponse = {"statut": "SUCCÈS", "code": 200, "role": role}
                else:
                    reponse = {"statut": "ERREUR", "code": 401, "message": "Identifiants invalides"}
            
            # ... (Ajouter les autres primitives ici plus tard)

            conn.send(json.dumps(reponse).encode())
            
        except Exception as e:
            print(f"[ERREUR] {e}")
            break


def demarrer_serveur():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((ADRESSE_ECOUTE, PORT_DEFAUT))
        s.listen()
        print(f"[SERVEUR] En attente sur le port {PORT_DEFAUT}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=gerer_client, args=(conn, addr)).start()

if __name__ == "__main__":
    demarrer_serveur()