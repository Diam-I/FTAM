# =================================================================
# MACHINE À ÉTATS 
# =================================================================
from commun.constantes import *


class MachineEtats:
    def __init__(self):
        self.etat_actuel = "IDLE"

    def transitionner(self, nouvel_etat):
        if nouvel_etat in ETATS:
            self.etat_actuel = nouvel_etat
            return True
        return False

    def peut_executer(self, primitive):
        """ Vérifie si la primitive demandée est autorisée selon l'état actuel """
        if primitive == F_INITIALIZE:
            return self.etat_actuel == "IDLE"
        elif primitive == F_SELECT:
            return self.etat_actuel in ["INITIALIZED", "SELECTED", "OPEN"]
        elif primitive == F_OPEN:
            return self.etat_actuel == "SELECTED"
        elif primitive == F_READ:
            return self.etat_actuel == "OPEN"
        elif primitive == F_RECOVER:
            return self.etat_actuel in ["INITIALIZED","SELECTED"]
        elif primitive == F_TERMINATE:
            return self.etat_actuel != "IDLE"
        elif primitive == F_DELETE:
            return self.etat_actuel in ["INITIALIZED", "SELECTED"]
        elif primitive == F_WRITE:
            return self.etat_actuel == "INITIALIZED"
        elif primitive == F_SET_PERMISSIONS:
            return self.etat_actuel in ["INITIALIZED", "SELECTED"]
        return False
