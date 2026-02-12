# Projet FTAM - STRI 2026

[cite_start]Implémentation du protocole ISO 8571 (File Transfer, Access and Management) pour le transfert et la gestion de fichiers distants[cite: 19, 28].

## Structure du Projet
- [cite_start]`serveur/` : Gestionnaire VFS (Virtual File System), Machine à états finis et contrôle d'accès[cite: 68, 73, 251].
- [cite_start]`client/` : Cœur logique (PDU JSON) et Interface utilisateur (CLI)[cite: 74, 249, 285].
- [cite_start]`commun/` : Constantes ISO FTAM et structures de données partagées[cite: 66, 532].
- [cite_start]`tests/` : Suite de tests automatisés (Unitaires, Intégration, Validation)[cite: 538].

## Installation & Lancement

1. **Préparation :** Placez vos fichiers dans `serveur/stockage/`.
2. **Lancement du Serveur :**
   ```bash
   python3 -m serveur.main_serveur

---

## Comment lancer le test 


1.  **Terminal 1 (Serveur) :** Lancez le serveur. 
2.  **Terminal 2 (Tests) :** Lancez la commande `python3 -m tests.validation_ftam`.
3.  **Analyse :** Chaque point `.` ou `[OK]` qui s'affiche confirme une fonctionnalité réussie. Si un test échoue, le message d'erreur vous indiquera exactement quelle primitive (`F-READ`, `F-DELETE`, etc.) a posé problème.