import socket
import threading
from commun.constantes import PORT_DEFAUT, ADRESSE_ECOUTE
import json
from serveur.gestion_etats import MachineEtats

def gerer_client(conn, addr):
    fsm = MachineEtats()
    while True:
        data = conn.recv(4096).decode()
        if not data: break
        
        requete = json.loads(data) # Décodage du PDU JSON 
        primitive = requete.get("primitive")
        
        if fsm.peut_executer(primitive):
            # Traiter la primitive ici (F-INITIALIZE, F-SELECT...)
            reponse = {"statut": "SUCCÈS", "code": 200} 
        else:
            reponse = {"statut": "ERREUR", "code": 403}
            
        conn.send(json.dumps(reponse).encode())

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