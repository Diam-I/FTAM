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
        print("\n=== Menu ===")
        if not client.est_connecte:
            print("1. Se connecter (F-INITIALIZE)")
            print("6. Quitter")
        else:
            print("2. Lister les fichiers (F-SELECT)")
            print("3. Télécharger un fichier (F-READ)")
            print("4. Reprendre un téléchargement (F-RECOVER)")
            if client.role == "admin":
                print("5. Supprimer un fichier (F-DELETE)")
            print("6. Quitter")

        opt = input("Choisissez une option : ")

        if opt == "1":
            connexion(client)

        elif opt == "2" and client.est_connecte:
            lister_fichiers(client)

        elif opt == "3" and client.est_connecte:
            telecharger(client)

        elif opt == "4" and client.est_connecte:
            reprendre_telechargement(client)

        elif opt == "6":
            client.quitter()
            break

        else:
            print("Option invalide ou accès non autorisé.")


def connexion(client):
    """Gère la connexion de l'utilisateur en demandant les informations nécessaires."""
    ip = input("Adresse IP [127.0.0.1] : ") or "127.0.0.1"
    user = input("Utilisateur : ")
    mdp = getpass("Mot de passe : ")
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
    nom = input("Nom du fichier à télécharger : ")
    res = client.telecharger(nom)
    if "erreur" in res:
        print(f"[ERREUR] {res['erreur']}")
    else:
        print(res["succes"])


def reprendre_telechargement(client):
    """Gère la reprise d'un téléchargement en demandant le nom du fichier."""
    nom = input("Nom du fichier : ")
    res = client.reprendre_telechargement(nom)
    if "erreur" in res:
        print(f"[ERREUR] {res['erreur']}")
    else:
        print(res["succes"])


if __name__ == "__main__":
    main()
