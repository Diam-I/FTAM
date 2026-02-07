# =================================================================
# MACHINE À ÉTATS FINIS 
# Rôle : Garantit la conformité au protocole FTAM en vérifiant 
#        que les commandes sont envoyées dans le bon ordre 
# =================================================================
from commun.constantes import ETATS, F_INITIALIZE, F_SELECT, F_OPEN, F_READ, F_TERMINATE, F_RECOVER

class MachineEtats:
    def __init__(self):
        self.etat_actuel = "IDLE"

    def transitionner(self, nouvel_etat):
        if nouvel_etat in ETATS:
            self.etat_actuel = nouvel_etat
            return True
        return False

    def peut_executer(self, primitive):
        """
        Vérifie si la primitive demandée est autorisée selon l'état actuel.
        Respecte la hiérarchie : INITIALIZE -> SELECT -> OPEN -> READ [cite: 291, 625]
        """
        if primitive == F_INITIALIZE:
            # On ne peut s'initialiser que si on ne l'est pas déjà
            return self.etat_actuel == "IDLE" 

        elif primitive == F_SELECT:
            # Nécessite d'être authentifié 
            return self.etat_actuel in ["INITIALIZED", "SELECTED", "OPEN"]

        elif primitive == F_OPEN:
            # Nécessite d'avoir sélectionné un fichier 
            return self.etat_actuel == "SELECTED"

        elif primitive == F_READ:
            # Le transfert n'est possible que si le fichier est ouvert 
            return self.etat_actuel == "OPEN"

        elif primitive == F_RECOVER:
            # La reprise est autorisée après une reconnexion 
            return self.etat_actuel == "INITIALIZED"

        elif primitive == F_TERMINATE:
            # On peut fermer la session n'importe quand sauf si on n'est pas connecté
            return self.etat_actuel != "IDLE"

        return False