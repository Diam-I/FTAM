import logging

LOG_FILE = "serveur.log"


def configurer_journalisation():
    """Configure le système de log (Fichier + Console)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def logger_info(message):
    """Log un message d'information."""
    logging.info(message)


def logger_erreur(message):
    """Log un message d'erreur."""
    logging.error(message)
