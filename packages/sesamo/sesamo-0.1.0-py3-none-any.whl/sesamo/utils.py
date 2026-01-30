import json
import os
import torch
import logging

from .models.flow import SymmetryEnforcingFlow

logger = logging.getLogger("SESaMo")


# load the json file with the arguments of the model
def load_args(checkpoint_path: str):
    args_path = os.path.join(os.path.dirname(checkpoint_path), "config.json")
    if not os.path.exists(args_path):
        logger.error(f"No config.json file found in {checkpoint_path}")
        return None
        
    # load the arguments
    with open(args_path, "r") as f:
        kwargs = json.load(f)

    return kwargs



def load_chechpoint(checkpoint_path: str):
    kwargs = load_args(checkpoint_path)

    if kwargs is None:
        logger.error("No args found")
        return None, None

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sampler = SymmetryEnforcingFlow(kwargs["sampler"])
    sampler.to(device)

    try:
        checkpoint = torch.load(checkpoint_path, map_location=device)
        sampler.load_state_dict(checkpoint["net"])
    except Exception as e:
        logger.error("Model loading error", e)
        return None, None

    return sampler, kwargs



def get_nsteps_from_checkpoint(checkpoint: str) -> str:
    checkpoint = os.path.basename(checkpoint)
    try:
        if checkpoint.endswith(".pth"):
            return int(checkpoint[len("checkpoint_"):-len(".pth")])
        else:
            return int(checkpoint[len("checkpoint_"):])
    except:
        return None



def get_latest_checkpoint(path, verbose=True):
    if not os.path.exists(path):
        logger.info(f"No model found at {path}")
        return None, None

    checkpoints = [checkpoint for checkpoint in os.listdir(path) if checkpoint.startswith("checkpoint_")]
    if len(checkpoints) == 0:
        if verbose:
            logger.info(f"No checkpoints found at {path}")
        return None, None
    
    # sort the checkpoints by the training steps
    checkpoints = sorted(checkpoints, key=get_nsteps_from_checkpoint)

    if checkpoints[0].endswith(".pth"):
        latest_checkpoint_path = os.path.join(path, checkpoints[-1])
    else:
        latest_checkpoint_dir = os.path.join(path, checkpoints[-1])
        latest_checkpoint_path = os.path.join(latest_checkpoint_dir, os.listdir(latest_checkpoint_dir)[0])

    latest_checkpoint_epoch = get_nsteps_from_checkpoint(os.path.basename(latest_checkpoint_path))

    return latest_checkpoint_path, latest_checkpoint_epoch






def load_latest_checkpoint(dir, verbose=True):
    # load sampler from latest checkpoint
    if not dir.endswith(".pth"):
        checkpoint_path, _ = get_latest_checkpoint(dir, verbose=verbose)
        if checkpoint_path is None:
            return None, None

    return load_chechpoint(checkpoint_path)