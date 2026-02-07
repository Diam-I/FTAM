# =================================================================
# GESTIONNAIRE DU SYSTÈME DE FICHIERS VIRTUEL (VFS)
# Rôle : Interface avec l'OS pour manipuler les fichiers réels.
#        Gère l'isolation du stockage, la lecture par blocs et
#        le mécanisme d'offset pour la REPRISE SUR INCIDENT.
# =================================================================
import os

RACINE = "./serveur/stockage/"

def verifier_existence(nom):
    return os.path.exists(os.path.join(RACINE, nom)) 

def lire_bloc(nom, offset, taille=1024):
    chemin = os.path.join(RACINE, nom)
    with open(chemin, "rb") as f:
        f.seek(offset) # Reprise sur incident 
        return f.read(taille)