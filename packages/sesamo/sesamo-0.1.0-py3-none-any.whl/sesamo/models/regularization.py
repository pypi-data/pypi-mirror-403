import torch
import torch.nn as nn
from math import pi as pi
import logging
import math

logger = logging.getLogger("symmetry")
REGULARIZATIONS = {}
def register_regularization(name):
    def wrap(clss):
        REGULARIZATIONS[name] = clss
        return clss
    return wrap



class Regularization(nn.Module):
    def __init__(self, A=1000, B=100, **kwargs):
        super().__init__()
        self.penalty_size = A
        self.penalty_gradient = B
        logger.info(f"Initialized {self.__class__.__name__} regularization with A={A}, B={B}")

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        return self.forward(x)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x, 0.
    
    def reverse(self, x: torch.Tensor) -> torch.Tensor:
        return x, 0.

    def penalty_term(self, lamb: torch.Tensor) -> torch.Tensor:
        return self.penalty_size * torch.sigmoid(self.penalty_gradient * lamb) * (lamb > 0).float()

    def regularization(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError("Regularization method not implemented")



@register_regularization("z2_reg")
class Z2Regularization(Regularization):
    def regularization(self, x: torch.Tensor) -> torch.Tensor:
        return self.penalty_term(-x.reshape(x.shape[0], -1).sum(-1))
    


@register_regularization("z4_reg")
class Z4Regularization(Regularization):
    def regularization(self, x: torch.Tensor) -> torch.Tensor:
        y = -x.sum(axis=1)
        return self.penalty_term(-y[:,0]) + self.penalty_term(y[:,1])
    


@register_regularization("zn_reg")
class ZNRegularization(Regularization):
    def __init__(self, n: int, offset: bool=False, A=1000, B=100, **kwargs):
        super().__init__(A=A, B=B, **kwargs)
        self.n = n
        self.offset = offset
        logger.info(f"Initialized Z{n} regularization with offset={offset}")
    
    def regularization(self, x):
        # The offset_angle rotates the penalty region
        angle = 2 * pi / self.n
        x_sum = x.sum(axis=1)
        
        if self.offset:
            d1 = x_sum[:,0] - x_sum[:,1]
            d2 = x_sum[:,1]
        else:
            d1 = math.tan(angle/2) * x_sum[:,0] - x_sum[:,1] / (1 + math.tan(angle/2)**2)
            d2 = math.tan(angle/2) * x_sum[:,0] + x_sum[:,1] / (1 + math.tan(angle/2)**2)
        
        return self.penalty_term(-d1) + self.penalty_term(-d2)
    

@register_regularization("hubbard_reg")
class HubbardRegularization(Regularization):
    def regularization(self, x: torch.Tensor) -> torch.Tensor:
        z = x.sum(axis=1)
        return self.penalty_term(-z).sum(-1)