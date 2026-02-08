# --- Primitives ISO FTAM ---
F_INITIALIZE = "F-INITIALIZE"
F_SELECT = "F-SELECT"
F_OPEN = "F-OPEN"
F_READ = "F-READ"
F_WRITE = "F-WRITE"
F_RECOVER = "F-RECOVER"
F_TERMINATE = "F-TERMINATE"
F_DELETE = "F-DELETE"

# --- Configuration Réseau ---
PORT_DEFAUT = 2121  
ADRESSE_ECOUTE = "0.0.0.0" 
TAILLE_BLOC = 1024

# Codes de statut 
SUCCES = 200 
ERREUR_AUTH = 401 
ERREUR_DROITS = 403 
ERREUR_NON_TROUVE = 404
ERREUR_VERROU = 423 

# Clés de structure (Pour éviter les fautes de frappe)
K_PRIM = "primitive"
K_PARA = "parametres"
K_STAT = "statut"
K_CODE = "code"
K_MESS = "message"

# États de la Machine à États
ETATS = ["IDLE", "INITIALIZED", "SELECTED", "OPEN"] 

# --- Structures de donnes echnger ---
# Modèle de requête : {"primitive": "", "parametres": {}}
REQ_STRUCT = {
    "primitive": "",
    "parametres": {}
}

# Modèle de réponse : {"statut": "", "code": 0, "message": ""}
RES_STRUCT = {
    "statut": "",
    "code": 0,
    "message": ""
}