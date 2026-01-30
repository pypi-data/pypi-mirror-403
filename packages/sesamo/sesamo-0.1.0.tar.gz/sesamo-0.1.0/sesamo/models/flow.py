import torch
import torch.nn as nn
import logging

from .realnvp import RealNVP
from .priors import PRIORS
from .canonicalization import CANONICALIZATIONS
from .stochmod import STOCHMODS
from .regularization import REGULARIZATIONS
from .scaling import GlobalScaling, LocalScaling
from .vmonf import VMONF

DTYPES = {
    "float32": torch.float32,
    "float64": torch.float64,
    "cdouble": torch.cdouble,
}

# set up flow dict with names and classes
FLOWS = {
    "realnvp": RealNVP,
    "globalscaling": GlobalScaling,
    "localscaling": LocalScaling,
    "vmonf": VMONF,
}
FLOWS.update(STOCHMODS)
FLOWS.update(CANONICALIZATIONS)
FLOWS.update(REGULARIZATIONS)

# set logging name to module name
logger = logging.getLogger("SESaMo")

class SymmetryEnforcingFlow(nn.Module):
    def __init__(
        self,
        kwargs
        ):
        super(SymmetryEnforcingFlow, self).__init__()

        # set attributes
        self.dtype = DTYPES[kwargs["dtype"]]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.lat_shape = kwargs["lat_shape"]

        # init prior
        self.prior = self.init_prior(kwargs["prior"], kwargs)

        
        
        # check if VMONF is in the flow
        self.vmonf_active = False
        if "vmonf" in kwargs["flow"]:
            # check if VMONF is the only flow
            if not kwargs["flow"] == "vmonf" and not kwargs["flow"] == ["vmonf"]:
                raise ValueError(f"VMONF must be the only flow in the flow list, but got {kwargs['flow']}")
            self.vmonf_active = True
            
        # init flows
        self.flow = self.init_flow(kwargs["flow"], kwargs)


    def init_prior(self, prior_name, kwargs):
        if prior_name not in PRIORS.keys() or f"{prior_name}_params" not in kwargs:
            raise ValueError(f"Prior {prior_name} not specified in kwargs")
        return PRIORS[prior_name](**kwargs[f"{prior_name}_params"], dtype=self.dtype, device=self.device)


    def init_flow(self, flow_names, kwargs):
        if flow_names is None:
            raise ValueError("Flows not specified. Specify at least one flow in your config file")
        if type(flow_names) == str:
            flow_names = [flow_names]

        flows = nn.ModuleList()
        for flow_name in flow_names:
            if "canon" in flow_name:
                if "forward" in flow_name:
                    flow_name = flow_name.removesuffix("_forward")
                elif "reverse" in flow_name:
                    flow_name = flow_name.removesuffix("_reverse")
                    if not flow_name + "_forward" in flow_names:
                        raise ValueError(f"Flow {flow_name} must have both forward and reverse canonicalization")
                    # search for the forward canonicalization in flows
                    forward_index = flow_names.index(f"{flow_name}_forward")
                    flows.append(flows[forward_index])
                    continue

            if flow_name not in FLOWS.keys():
                raise ValueError(f"Flow {flow_name} not found in FLOWS")
            
            if f"{flow_name}_params" in kwargs:
                cls = FLOWS[flow_name](**kwargs[f"{flow_name}_params"], dtype=self.dtype, device=self.device)
            else:
                cls = FLOWS[flow_name](dtype=self.dtype, device=self.device)

            flows.append(cls)

        return flows

        
    def forward(self, z):
        # init log det with zeros
        log_det = torch.zeros(z.shape[0], device=z.device, dtype=z.dtype)
        self.regularization = torch.zeros(z.shape[0], device=z.device, dtype=z.dtype)
        
        # if VMONF is active
        if self.vmonf_active:
            z, log_det = self.flow[-1](z)
            self.prob_c = self.flow[-1].prob_c
            return z, log_det
        
        # apply flow
        for flow in self.flow:
            z, single_log_det = flow(z)
            log_det += single_log_det

            # check if flow type is regularization and apply it
            if hasattr(flow, "regularization"):
                self.regularization += flow.regularization(z)

        return z, log_det


    def reverse(self, x):
        raise ValueError("Reverse function not implemented for this flow")


    def sample_with_logprob(self, n_samples):
        # sample from prior with log prob
        z = self.prior.sample(n_samples)
        prior_log_prob = self.prior.log_prob(z)
    
        # apply flow
        x, log_det = self.forward(z)

        # compute log prob
        log_prob = prior_log_prob - log_det
        
        return x, log_prob
