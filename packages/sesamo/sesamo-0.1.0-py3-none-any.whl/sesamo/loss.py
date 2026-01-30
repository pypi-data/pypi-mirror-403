import logging
logger = logging.getLogger("SESaMo")

class ReverseKL:
    """
    Kullback-Leibler divergence loss for normalizing flows.
    """
    def __init__(self):
        logger.info(f"Initialized ReverseKL Loss")

    def __call__(self, actions, log_probs):
        return actions + log_probs