import logging
import torch
import torch.nn as nn
import numpy as np

logger = logging.getLogger("SESaMo")

COUPLINGS = {}
def register_coupling(name):
    def wrap(clss):
        COUPLINGS[name] = clss
        return clss
    return wrap


class Coupling(nn.Module):
    def __init__(self, mask_config):
        """Initialize a coupling layer.
        Args:
            mask_config: 1 if transform odd units, 0 if transform even units.
        """
        super(Coupling, self).__init__()
        self.mask_config = mask_config
        
    def _split(self, x):
        raise NotImplementedError("_split method not implemented")
    
    def _join(self, on, off):
        raise NotImplementedError("_join method not implemented")
    
    def forward(self, x):
        return self._apply_coupling(x)

    def reverse(self, x):
        return self._apply_coupling(x, reverse=True)
    
    def _apply_coupling(self, x, reverse=False):
        x_shape = x.shape
        x = x.reshape(x.shape[0], -1)
        on, off = self._split(x)

        # Scaling and translation
        scale = self.scale_net(off)
        translation = self.translation_net(off)
        
        if reverse:
            on = (on - translation) / torch.exp(scale)
            log_det = -torch.sum(scale, dim=1)
        else:
            on = on * torch.exp(scale) + translation
            log_det = torch.sum(scale, dim=1)
            
        x = self._join(on, off)
        return x.reshape(x_shape), log_det
    




@register_coupling('altfc')
class AltFCRealNVPCoupling(Coupling):
    def __init__(self, lat_shape, mask_config, mid_dim=1000, nblocks=4, bias=False, activation='ReLU', dtype=torch.float64, z2=False):
        super().__init__(mask_config=mask_config)
        self.lat_shape = lat_shape
        self.mid_dim = mid_dim
        self.nblocks = nblocks
        self.dtype = dtype
        self.z2 = z2

        in_out_dim = np.prod(lat_shape)

        activation_dict = {
            'relu': nn.ReLU(),
            'tanh': nn.Tanh(),
            'leakyrelu': nn.LeakyReLU(0.01),
        }
        activation_func = activation_dict.get(activation.lower(), ValueError(f"Activation {activation} not implemented"))

        if z2:
            activation_func = nn.Tanh()
            bias = False

        # Scaling and translation networks
        self.scale_net = nn.Sequential(
            nn.Linear(in_out_dim // 2, mid_dim, bias=bias, dtype=dtype),
            activation_func,
            *[
                nn.Sequential(
                    nn.Linear(mid_dim, mid_dim, bias=bias, dtype=dtype),
                    activation_func,
                ) for _ in range(nblocks)
            ],
            nn.Linear(mid_dim, in_out_dim // 2, bias=bias, dtype=dtype)
        )

        self.translation_net = nn.Sequential(
            nn.Linear(in_out_dim // 2, mid_dim, bias=bias, dtype=dtype),
            activation_func,
            *[
                nn.Sequential(
                    nn.Linear(mid_dim, mid_dim, bias=bias, dtype=dtype),
                    activation_func,
                ) for _ in range(nblocks)
            ],
            nn.Linear(mid_dim, in_out_dim // 2, bias=bias, dtype=dtype)
        )

        # init parameter with xavier
        for m in self.scale_net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
        for m in self.translation_net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)

    def _split(self, x):
        """
        Split the input into two parts.
        From (0,1,2,3) to (0,2) and (1,3)
        """
        B, W = x.shape
        x = x.reshape((B, W // 2, 2))
        if self.mask_config:
            on, off = x[:, :, 0], x[:, :, 1]
        else:
            off, on = x[:, :, 0], x[:, :, 1]

        return on, off

    def _join(self, on, off):
        if self.mask_config:
            x = torch.stack((on, off), dim=2)
        else:
            x = torch.stack((off, on), dim=2)

        return x
    




class RealNVP(nn.Module):
    def __init__(
            self,
            lat_shape,
            coupling='altfc',
            ncouplings=6,
            nblocks=4,
            mid_dim=100,
            mask_config=1,
            bias=True,
            activation="ReLU", 
            device='cpu',
            dtype=torch.float64,
    ):
        super(RealNVP, self).__init__()
        self.lat_shape = lat_shape
        self.ncouplings = ncouplings
        self.device = device
        coupling_factory = COUPLINGS[coupling]

        # init couplings
        self.couplings = nn.ModuleList(
            [
                coupling_factory(
                    lat_shape=lat_shape,
                    nblocks=nblocks,
                    mid_dim=mid_dim,
                    mask_config=(mask_config + i) % 2,
                    bias=bias,
                    activation=activation,
                    dtype=dtype,
                )
                for i in range(ncouplings)
            ]
        )

        logger.info(f"Initialized RealNVP with {ncouplings} couplings, each with {nblocks} blocks of {mid_dim} hidden units")


    def forward(self, z):
        # init log det
        log_det = torch.zeros(z.shape[0], device=z.device)

        # apply neural network
        for i, coupling in enumerate(self.couplings):
            z, single_log_det = coupling(z)
            log_det += single_log_det

        return z, log_det


    def reverse(self, x):
        # init log det
        log_det = torch.zeros(x.shape[0], device=self.device)

        # apply reverse couplings
        for coupling in reversed(self.couplings):
            x, single_log_det = coupling.reverse(x)
            log_det += single_log_det

        return x, log_det