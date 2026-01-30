import torch
import logging

logger = logging.getLogger("SESaMo")
PRIORS = {'none': None}

def register_prior(name):
    def wrap(clss):
        PRIORS[name] = clss
        return clss
    return wrap



@register_prior('gaussian')
class GaussianPrior():
    def __init__(self, lat_shape, device="cpu", dtype=torch.float64, mean=0, var=1, verbose=True):
        assert var > 0, "Variance must be positive"

        self.lat_shape = lat_shape
        self.device = device
        self.mean = torch.tensor(mean, device=device, dtype=dtype)
        self.sigma = torch.tensor(var**0.5, device=device, dtype=dtype)
        self.dtype = dtype

        if verbose:
            logger.info(f"Initialized gaussian prior with: mean = {mean}, var = {var}")

    def log_prob(self, x):
        log_prob = torch.distributions.Normal(self.mean, self.sigma).log_prob(x).to(self.device)
        return log_prob.reshape(x.shape[0], -1).sum(-1)

    def sample(self, n):
        return torch.distributions.Normal(self.mean, self.sigma).sample((n,*self.lat_shape)).to(self.device)
    


@register_prior('uniform')
class UniformPrior():
    def __init__(self, lat_shape, device="cpu", low=-1, high=1, dtype=torch.float64):
        assert high > low, "High must be greater than low"

        self.lat_shape = lat_shape
        self.device = device
        self.low = torch.tensor(low, device=device, dtype=dtype)
        self.high = torch.tensor(high, device=device, dtype=dtype)

        logger.info(f"Initalized uniform prior with: low = {self.low}, high = {self.high}")

    def log_prob(self, x):
        log_prob = torch.distributions.Uniform(self.low, self.high).log_prob(x).to(self.device)
        return log_prob.reshape(x.shape[0], -1).sum(-1)

    def sample(self, n):
        return torch.distributions.Uniform(self.low, self.high).sample((n,*self.lat_shape)).to(self.device)