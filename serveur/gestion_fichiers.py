# =================================================================
# GESTIONNAIRE DU SYSTÈME DE FICHIERS VIRTUEL
# =================================================================
import os

# Dossier racine 
RACINE = os.path.abspath("./serveur/stockage/") 

def verifier_existence(nom):
    """ Vérifie la présence d'un document avant sélection """
    if not nom: return False
    chemin_complet = os.path.abspath(os.path.join(RACINE, nom))
    if not chemin_complet.startswith(RACINE):
        return False
    return os.path.exists(chemin_complet)

def lire_bloc(nom, offset, taille=1024):
    """ Extrait une portion de données à partir d'une position précise """
    chemin_complet = os.path.abspath(os.path.join(RACINE, nom))
    if not chemin_complet.startswith(RACINE):
        raise PermissionError("Accès interdit hors du stockage sécurisé")
    try:
        with open(chemin_complet, "rb") as f:
            f.seek(offset) 
            return f.read(taille)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"[ERREUR] Lecture impossible : {e}")
        return None