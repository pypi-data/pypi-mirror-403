# =========================================================================
# VMONF: Variational Mixture of Normalizing Flows
# From Guilherme G. P. Freitas Pires and Mário A. T. Figueiredo
# https://www.esann.org/sites/default/files/proceedings/2020/ES2020-188.pdf
# =========================================================================
import torch
import torch.nn as nn
import logging
from .realnvp import RealNVP

logger = logging.getLogger("SESaMo")

class VMONF(nn.Module):
    def __init__(
        self,
        lat_shape: list,
        sectors: int = 4,
        coupling: str = "altfc",
        ncouplings: int = 2,
        mid_dim: int = 64,
        nblocks: int = 4,
        activation: str = "relu",
        dtype: str = "float32",
        **kwargs
    ):
        super(VMONF, self).__init__()
        self.sectors = sectors
        
        
        self.realvnp_list = nn.ModuleList(
            [
                RealNVP(
                    lat_shape=lat_shape,
                    coupling=coupling,
                    ncouplings=ncouplings,
                    mid_dim=mid_dim,
                    nblocks=nblocks,
                    activation=activation,
                    dtype=dtype,
                )
                for _ in range(sectors)
            ]
        )
        
        in_dim = torch.prod(torch.tensor(lat_shape)).item()
        self.feedforward = nn.Sequential(
            nn.Linear(in_dim, mid_dim, dtype=dtype),
            nn.ReLU(),
            *[
                nn.Sequential(
                    nn.Linear(mid_dim, mid_dim, dtype=dtype),
                    nn.ReLU()
                ) for _ in range(nblocks - 1)
            ],
            nn.Linear(mid_dim, sectors, dtype=dtype),
            nn.Softmax(dim=-1)
        )
        
        # self.same_ff_out = False
        
        logger.info(f"Initialized VMONF with {sectors} sectors")

    def forward(self, z):
        self.prob_c = self.feedforward(z.reshape(z.shape[0], -1)).transpose(0,1) # shape (sectors, batch_size)
        
        # init x and log_dets
        x_i = torch.zeros((self.sectors, *z.shape), device=z.device, dtype=z.dtype)
        log_det_i = torch.zeros((self.sectors, z.shape[0]), device=z.device, dtype=z.dtype)
        
        for i, realvnp in enumerate(self.realvnp_list):
            x_i[i], log_det_i[i] = realvnp(z)
        
        return x_i, log_det_i