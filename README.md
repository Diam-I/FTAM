# Projet FTAM - STRI 2026

Implémentation du protocole ISO 8571 pour le transfert de fichiers.

## Structure
- `serveur/` : Gestionnaire VFS, Machine à états et Sécurité.
- `client/` : Coeur logique et Interface utilisateur.
- `commun/` : Constantes et structures de données.

## Installation & Lancement
1. Placez vos fichiers dans `serveur/stockage/`.
2. Lancez le serveur :
   ```bash
   python3 -m serveur.main_serveur
   ```
3. Lancer le client:
    ```bash
   python3 -m client.main_client
   ```