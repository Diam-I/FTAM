# =================================================================
# MACHINE À ÉTATS FINIS (FSM)
# Rôle : Garantit la conformité au protocole FTAM en vérifiant 
#        que les commandes sont envoyées dans le bon ordre 
#        (ex: Interdire F-READ si l'état n'est pas OPEN).
# =================================================================
from commun.constantes import ETATS

class MachineEtats:
    def __init__(self):
        self.etat_actuel = "IDLE"

    def transitionner(self, nouvel_etat):
        if nouvel_etat in ETATS:
            self.etat_actuel = nouvel_etat
            return True
        return False

    def peut_executer(self, primitive):
        # Logique de vérification (ex: F-READ nécessite l'état OPEN) 
        if primitive == "F-READ" and self.etat_actuel != "OPEN":
            return False
        return True