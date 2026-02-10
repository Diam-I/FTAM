import json
import os

META_PATH = os.path.join(os.path.dirname(__file__), "stockage", ".meta.json")


def charger_meta():
    if not os.path.exists(META_PATH):
        return {}
    with open(META_PATH, "r") as f:
        return json.load(f)


def peut_lire(utilisateur, nom_fichier):
    meta = charger_meta()
    if nom_fichier not in meta:
        return False
    return utilisateur in meta[nom_fichier]["permissions"].get("read", [])


def peut_supprimer(utilisateur, nom_fichier):
    meta = charger_meta()
    if nom_fichier not in meta:
        return False
    return utilisateur in meta[nom_fichier]["permissions"].get("delete", [])
