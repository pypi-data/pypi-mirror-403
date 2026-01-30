import torch
import torch.nn as nn
from math import pi as pi
import logging

logger = logging.getLogger("symmetry")
CANONICALIZATIONS = {}
def register_canonicalization(name):
    def wrap(clss):
        CANONICALIZATIONS[name] = clss
        return clss
    return wrap



class Canonicalization(nn.Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.penalty_size = 1000
        self.penalty_gradient = 100
        self.forwarded = False
        logger.info(f"Initialized {self.__class__.__name__} symmetry")

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        if self.forwarded:
            return self.reverse(x)
        else:
            return self.forward(x)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        self.forwarded = True
        return self.transform(x), 0.
    
    def reverse(self, x: torch.Tensor) -> torch.Tensor:
        if not self.forwarded:
            raise ValueError("The forward method must be called before the reverse method")
        
        self.forwarded = False
        return self.inverse_transform(x), 0.
    
    def transform(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError("Transform method not implemented")

    def inverse_transform(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError("Inverse transform method not implemented")



@register_canonicalization("z2_canon")
class Z2Canonicalization(Canonicalization):
    def __init__(self, **kwargs):
        """This transformation takes the sign of the sum of all fields on the lattice and multiplies the field with this sign 
        The inverse transformation returns the original field
        """
        super().__init__()
        self.signs = None

    def transform(self, x: torch.Tensor) -> torch.Tensor:
        assert x.dim() == 3, "Input tensor should be 3-dimensional"

        # get signs from x
        self.signs = x.sum(axis=(1,2)).sign().unsqueeze(1).unsqueeze(2)

        return x * self.signs
    
    def inverse_transform(self, x: torch.Tensor) -> torch.Tensor:
        """Inverse transformation of the input tensor x by multiplying it with the inverse sign of the sum of all fields on the lattice
        """
        return x * self.signs
    


@register_canonicalization("z4_canon")
class Z4Canonicalization(Canonicalization):
    def __init__(self, **kwargs):
        """This transformation takes the sign of the sum of all fields on the lattice and multiplies the field with this sign 
        The inverse transformation returns the original field
        """
        super().__init__()
        self.signs = None

    def transform(self, x: torch.Tensor) -> torch.Tensor:
        assert x.dim() == 3, "Input tensor should be 3-dimensional"

        # get signs from x
        self.signs = x.sum(axis=1).sign().unsqueeze(1)

        return x * self.signs
    
    def inverse_transform(self, x: torch.Tensor) -> torch.Tensor:
        """Inverse transformation of the input tensor x by multiplying it with the inverse sign of the sum of all fields on the lattice
        """
        return x * self.signs
    


@register_canonicalization("zn_canon")
class ZNCanonicalization(Canonicalization):
    def __init__(self, n=8, **kwargs):
        super().__init__()
        self.n = n

        logger.info(f"Initialized Z{n} canonicalization")

    def transform(self, x):
        """
            Transform configs to pizza slices at angle = 0
        """
        assert x.shape[2] == 2, f"Input tensor should have shape (batch, Nt, 2) but got {x.shape}"
        x_sum = x.sum(axis=1)

        angle_x = torch.atan2(x_sum[:,1], x_sum[:,0]) # in [-pi, pi]
        self.angle = -(angle_x / (2*pi/self.n)).round() * 2*pi/self.n
        self.angle = self.angle.unsqueeze(1)


        x = torch.stack([x[:,:,0] * torch.cos(self.angle) - x[:,:,1] * torch.sin(self.angle), 
                         x[:,:,0] * torch.sin(self.angle) + x[:,:,1] * torch.cos(self.angle)], dim
                         =2)

        return x
    
    def inverse_transform(self, x):
        """
            Transform pizza slices back to original configs
        """
        x = torch.stack([x[:,:,0] * torch.cos(-self.angle) - x[:,:,1] * torch.sin(-self.angle),
                         x[:,:,0] * torch.sin(-self.angle) + x[:,:,1] * torch.cos(-self.angle)], dim=2)
        
        return x