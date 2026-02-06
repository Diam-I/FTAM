import os

RACINE = "./serveur/stockage/"

def verifier_existence(nom):
    return os.path.exists(os.path.join(RACINE, nom)) 

def lire_bloc(nom, offset, taille=1024):
    chemin = os.path.join(RACINE, nom)
    with open(chemin, "rb") as f:
        f.seek(offset) # Pour la reprise sur incident 
        return f.read(taille)