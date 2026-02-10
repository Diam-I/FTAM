# =================================================================
# CLIENT FTAM - INTERFACE UTILISATEUR
# =================================================================
from getpass import getpass
from .coeur_client import ClientFTAM


def afficher_etat(client):
    """Affiche l'état actuel de la machine à états pour le client."""
    couleur = {
        "IDLE": "\033[90m",  # Gris
        "INITIALIZED": "\033[94m",  # Bleu
        "SELECTED": "\033[93m",  # Jaune
        "OPEN": "\033[92m",  # Vert
    }
    print(
        f"État actuel : {couleur.get(client.etat_actuel, '')}{client.etat_actuel}\033[0m"
    )


def main():
    client = ClientFTAM()

    while True:
        afficher_etat(client)
        print("\n+ + + === Menu === + + +")
        if not client.est_connecte:
            print("1. Se connecter (F-INITIALIZE)")
            print("2. Quitter")
            leave = "2"
        else:
            print("1. Lister les fichiers (F-SELECT)")
            print("2. Télécharger un fichier (F-READ)")
            print("3. Reprendre un téléchargement (F-RECOVER)")
            if client.role == "admin" or client.role == "proprietaire":
                print("4. Supprimer un fichier (F-DELETE)")
                print("5. Quitter")
                leave = "5"
            else:
                print("4. Quitter")
                leave = "4"

        opt = input("Choisissez une option : ").strip()
        if opt == leave:
            client.quitter()
            break
        elif opt == "1" and not client.est_connecte:
            connexion(client)
        elif client.est_connecte:
            if opt == "1":
                lister_fichiers(client)
            elif opt == "2":
                telecharger(client)
            elif opt == "3":
                reprendre_telechargement(client)
            elif opt == "4" and (
                client.role == "admin" or client.role == "proprietaire"
            ):
                supprimer_fichier(client)
            else:
                print("Option invalide.")
        else:
            print("Option invalide ou accès non autorisé.")

        print("\n\n ===========================\n\n")


def connexion(client):
    """Gère la connexion de l'utilisateur en demandant les informations nécessaires."""
    ip = input("Adresse IP [127.0.0.1] : ") or "127.0.0.1"
    user = input("Utilisateur : ").strip()
    mdp = getpass("Mot de passe : ").strip()
    res = client.connecter(ip, user, mdp)
    if "erreur" in res:
        print(f"[ERREUR] {res['erreur']}")
    else:
        print(res["succes"])


def lister_fichiers(client):
    """Affiche la liste des fichiers disponibles sur le serveur."""
    res = client.lister_fichiers()
    if "erreur" in res:
        print(f"[ERREUR] {res['erreur']}")
    else:
        print("\n--- Fichiers sur le serveur ---")
        for f in res["fichiers"]:
            print(f"  > {f}")


def telecharger(client):
    """Gère le téléchargement d'un fichier en demandant son nom et en affichant les progrès."""
    nom = input("Nom du fichier à télécharger : ").strip()
    res = client.telecharger(nom)
    if "erreur" in res:
        print(f"[ERREUR] {res['erreur']}")
    else:
        print(res["succes"])


def reprendre_telechargement(client):
    """Gère la reprise d'un téléchargement en demandant le nom du fichier."""
    nom = input("Nom du fichier : ").strip()
    res = client.reprendre_telechargement(nom)
    if "erreur" in res:
        print(f"[ERREUR] {res['erreur']}")
    else:
        print(res["succes"])


def supprimer_fichier(client):
    """Demande confirmation avant de supprimer un fichier distant."""
    nom = input("Nom du fichier à supprimer définitivement : ").strip()
    conf = input(f"Êtes-vous sûr de vouloir supprimer '{nom}' ? (o/n) : ").lower()

    if conf == "o":
        res = client.supprimer_fichier(nom)
        if "erreur" in res:
            print(f"[ERREUR] {res['erreur']}")
        else:
            print(f"[SUCCÈS] {res['succes']}")
    else:
        print("Suppression annulée.")


if __name__ == "__main__":
    main()
