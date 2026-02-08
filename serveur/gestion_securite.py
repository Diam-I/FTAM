# =================================================================
# MODULE D'AUTHENTIFICATION ET CONTRÔLE D'ACCÈS
# Rôle : Vérifie l'identité de l'utilisateur (F-INITIALIZE) et 
#        attribue des droits (Lecteur/Propriétaire) pour restreindre
#        les actions sensibles comme la suppression (F-DELETE).
# =================================================================

# Base de données simulée 
UTILISATEURS = {
    "salia": {"mdp": "stri2026", "role": "proprietaire"},
    "amina": {"mdp": "ftam2026", "role": "proprietaire"},
    "invite": {"mdp": "guest", "role": "lecteur"}
}

def authentifier(utilisateur, mdp):
    """Vérifie les identifiants et retourne le rôle si valide """
    if utilisateur in UTILISATEURS and UTILISATEURS[utilisateur]["mdp"] == mdp:
        return UTILISATEURS[utilisateur]["role"]
    return None