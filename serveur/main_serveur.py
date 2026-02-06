import socket
import threading
from commun.constantes import PORT_DEFAUT, ADRESSE_ECOUTE

def gerer_client(conn, addr):
    print(f"[INFO] Connexion de {addr}")
    with conn:
        # La logique de traitement des messages JSON viendra ici
        pass

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