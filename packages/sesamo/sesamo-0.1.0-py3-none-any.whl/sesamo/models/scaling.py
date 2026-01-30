import torch
import torch.nn as nn

import logging
logger = logging.getLogger("SESaMo")


SCALINGS = {}
def register_scaling(name):
    def wrap(clss):
        SCALINGS[name] = clss
        return clss
    return wrap


@register_scaling('globalscaling')
class GlobalScaling(nn.Module):
    def __init__(self, lat_shape, dtype=torch.float64, verbose=True, **kwargs):
        super().__init__()
        self.scale = nn.Parameter(torch.zeros(1, dtype=dtype), requires_grad=True)
        self.lat_shape = lat_shape
        if verbose:
            logger.info(f"Initialized globalscaling")

    def forward(self, x):
        x = x * torch.exp(self.scale)
        return x, self._log_det(x)

    def reverse(self, x):
        x = x * torch.exp(-self.scale)
        return x, self._log_det(x, reverse=True)

    def _log_det(self, x, reverse=False):
        scale = (-1. if reverse else 1.) * self.scale * int(torch.prod(torch.tensor(self.lat_shape)))

        return scale




@register_scaling('localscaling')
class LocalScaling(nn.Module):
    def __init__(self, lat_shape, dtype=torch.float64, **kwargs):
        super().__init__()
        self.lat_shape = lat_shape
        self.scale = nn.Parameter(
            torch.zeros((1, *lat_shape), dtype=dtype),
            requires_grad=True
        )
        logger.info(f"Initialized localscaling with dim {lat_shape}")

    def forward(self, x):
        x = x * torch.exp(self.scale)
        return x, self._log_det(x)

    def reverse(self, x):
        x = x * torch.exp(-self.scale)
        return x, self._log_det(x, reverse=True)

    def _log_det(self, x, reverse=False):
        scale = (-1. if reverse else 1.) * torch.sum(self.scale)
        return scale.repeat(x.shape[0])