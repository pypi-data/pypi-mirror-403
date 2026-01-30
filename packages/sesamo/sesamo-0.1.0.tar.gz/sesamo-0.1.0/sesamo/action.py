import math
import logging
import torch
import os
import yaml
from torch import Tensor
logger = logging.getLogger("SESaMo")

class Action:
    def evaluate(self, phi):
        raise NotImplementedError("evaluate method not implemented")

    def __call__(self, phi):
        return self.evaluate(phi)
    

# ====================================================================================
# PHYSICAL ACTIONS
# ====================================================================================

class ScalarPhi4Action(Action):
    def __init__(self, kappa:float, lambd:float, broken:float=0):
        self.kappa = kappa
        self.lambd = lambd
        self.broken = broken

        logger.info(f"Initialized Phi4Action with kappa={kappa}, lambd={lambd}, breaking={broken}")

    def evaluate(self, phi:Tensor) -> Tensor:
        if len(phi.shape) != 3:
            raise ValueError(f"field has invalid shape, should be (batch, nt, nx), but got {phi.shape}")

        kinetic = (-2 * self.kappa) * phi * (torch.roll(phi, 1, -1) + torch.roll(phi, 1, -2))
        mass = (1 - 2 * self.lambd) * phi ** 2
        inter = self.lambd * phi ** 4
        z2_breaking_term = self.broken * phi.reshape(phi.shape[0], -1).sum(-1)

        return (kinetic + mass + inter).sum(-1).sum(-1) + z2_breaking_term
    



class ComplexPhi4Action(ScalarPhi4Action):
    def __init__(self, kappa:float, lambd:float, broken:float=0):
        r"""
        Args:
            kappa (float): hopping parameter
            lambd (float): interaction parameter
            breaking (float): breaking term for the U(1) symmetry

        Description:
            Action for the complex phi^4 theory

            $$ 
            S[(\phi_1, \phi_2, ...)] = \sum_i S[\phi_i] + breaking * \sum_i \sum_{x} \phi_i(x)
            $$
            
        """
        self.kappa = kappa
        self.lambd = lambd
        self.broken = broken

        logger.info(f"Initialized ComplexPhi4Action with kappa={kappa}, lambd={lambd}, breaking={broken}")

    def evaluate(self, phi:Tensor) -> Tensor:
        kinetic = (-2 * self.kappa) * phi * (torch.roll(phi, 1, -1) + torch.roll(phi, 1, -2))
        mass = (1 - 2 * self.lambd) * phi ** 2
        inter = self.lambd * (phi ** 2).sum(1) ** 2

        return (kinetic.sum(1) + mass.sum(1) + inter).sum(-1).sum(-1)

    def __call__(self, phi:Tensor) -> Tensor:
        if len(phi.shape) != 4:
            raise ValueError(f"field has invalid shape, should be (batch, 2, n_t, n_x), but got {phi.shape}")

        N = phi.shape[0]
        main_action = self.evaluate(phi)
        u1_breaking_term = self.broken * phi.reshape(N, -1).sum(-1)

        return main_action + u1_breaking_term





class HubbardAction(Action):
    """
    Hubbard action for a 2-site model with one timesclice and a given hopping matrix.
    Describes spin-up and spin-down fermions that hop between the two sites and interact with each other via an on-site interaction of strength u.
    This is the spin-basis with exponential discretization.
    For more details see: https://arxiv.org/pdf/1812.09268
    """
    def __init__(self, u:float=18, beta:float=1, nt:float=1, nx:float=2):
        """
        Args:
            u (float): coupling constant
            beta (float): inverse temperature
        """
        self.u = u
        self.beta = beta
        self.dtype_warning_issued = False
        self.nt = nt
        self.nx = nx
        
        if nx not in [2, 18]:
            raise ValueError(f"HubbardAction only implemented for nx=2 or nx=18, but got nx={nx}")
        
        if nx == 18:
            lattice_file = "hubbard_lattices/18_sites_hex.yaml"
            with open(os.path.join(os.path.dirname(__file__), lattice_file), 'r') as f:
                self.hopping = yaml.safe_load(f)

        logger.info(f"Initialized HubbardAction with U={u}, beta={beta}")


    def fermion_mat(self, phi:Tensor, species:int) -> Tensor:
        """
        Computes the fermion matrix
        """
        if species not in [-1, 1]:
            raise ValueError(f"Species must be +/- 1 but got {species}")
        
        N, nt, nx = phi.shape
        device = phi.device
        dtype = phi.dtype
        
        if phi.dtype != torch.float64 and not self.dtype_warning_issued:
            self.dtype_warning_issued = True
            logger.warning(f"dtype {phi.dtype} may lead to numerical instabilities of the Hubbard action, consider using float64")

        # get the hopping matrix
        exp_kappa = torch.zeros((nx, nx), device=device, dtype=dtype)
        if nx == 2:
            exp_kappa[0, 0] = math.cosh(self.beta / nt)
            exp_kappa[0, 1] = math.sinh(self.beta / nt)
            exp_kappa[1, 0] = math.sinh(self.beta / nt)
            exp_kappa[1, 1] = math.cosh(self.beta / nt)
        elif nx == 18:
            for index, (i,j) in enumerate(self.hopping["adjacency"]):
                exp_kappa[i,j] = self.hopping["hopping"][index] * self.beta/nt
            exp_kappa = torch.matrix_exp(exp_kappa)
        else:
            raise ValueError(f"Fermion matrix not implemented for nx={nx}")
        
        # precompute the exponential of the configuration
        exp_phi = torch.exp(species * phi).type(dtype)

        # initialize the fermion matrix
        m = torch.zeros((N, nt, nx, nt, nx), dtype=dtype, device=device)

        # set up the fermion matrix
        nx_unit = torch.eye(nx, dtype=dtype, device=device)
        ts = torch.arange(nt - 1)
        m[:, ts, :, ts, :] = nx_unit
        
        # fill fermion matrix entries
        if nt == 1:
            m[:, 0, :, 0, :] = nx_unit + exp_kappa * exp_phi[:, 0, None, :]
        else:
            m[:, ts+1, :, ts, :] = (-exp_kappa * exp_phi[:, ts, None, :]).permute(1, 0, 2, 3)
            m[:, nt-1, :, nt-1, :] = nx_unit
            m[:, 0, :, nt-1, :] = exp_kappa * exp_phi[:, nt-1, None, :]

        return m

    def logdet_m(self, phi:Tensor, species:int) -> Tensor:
        r"""
        Computes the log determinant of the fermion matrix
            \params:
                - phi: torch.tensor(self.n_t, self.n_x), configuration
                - species: +1 for spin-up, -1 for spin-down particles
            
            \log \det [m(phi)_{t',x'; t,x}] 
        """
        
        N, nt, nx = phi.shape
        m = self.fermion_mat(phi, species)
        m = m.reshape(N, nt*nx, nt*nx) # reshape to (N, nt*nx, nt*nx) to compute the determinant of the 2D matrix
        return torch.logdet(m)

    def evaluate(self, phi:Tensor) -> Tensor:
        nt = phi.shape[1]
        u_tilde = self.u * self.beta / nt

        actions = (- self.logdet_m(phi, +1) - self.logdet_m(phi, -1) + (phi*phi).sum(dim=(1, 2)) / (2 * u_tilde)).real
        
        return actions
    
    def __call__(self, phi:Tensor) -> Tensor:
        if len(phi.shape) != 3 or phi.shape[1:] != (1, 2):
            raise ValueError(f"field has invalid shape, should be (batch, 1, 2), but got {phi.shape}")

        return self.evaluate(phi)
    
    def logZ(self) -> float:
        r"""
        Returns:
            logZ (float): log partition function
        Description:
            Only implemented for Nx=2, Nt=1, u=18, and beta=1
        """
        if self.u != 18 or self.beta != 1:
            raise ValueError("logZ is only defined for u=18 and beta=1")
        
        return 24.6398



# ====================================================================================
# TOY MODELS
# ====================================================================================

class GaussianMixtureAction(Action):
    def __init__(self, n_gaussians:int=8, radius:float=12, broken:float=0):
        """
        Args:
            n_gaussian (int): number of Gaussians
            radius (float): radius of the circle where the Gaussians are placed on
        
        Description:
            Creates Gaussian shaped modes at a circle
        """
        self.n_gaussians = n_gaussians
        self.radius = radius
        self.broken = broken

        self.centers = self.get_gaussians()

        logger.info(f"Initialized GaussianMixtureAction with n_gaussians={n_gaussians}, radius={radius}, breaking={broken}")


    def get_gaussians(self):
        centers = []

        for i in range(self.n_gaussians):
            centers.append([math.cos(2*math.pi/self.n_gaussians*i), math.sin(2*math.pi/self.n_gaussians*i)])

        return self.radius * torch.tensor(centers)
    

    def evaluate(self, phi:Tensor) -> Tensor:
        assert len(phi.shape) == 3 and phi.shape[1:] == (1,2), f"field has invalid shape, should be (batch, 1, 2), but got {phi.shape}"

        if self.centers.device != phi.device:
            self.centers = self.centers.to(phi.device)

        return -torch.logsumexp(-0.5*(phi - self.centers[None, None, :]).norm(dim=-1)**2, dim=-1).squeeze(0) + self.broken * phi.sum(dim=(1,2))
    
    
    def logZ(self) -> float:
        """
        Returns:
            logZ (float): log partition function
        """
        if self.broken == 0:
            return math.log(2*math.pi * self.n_gaussians)
        else:
            phi_k = 2*math.pi / self.n_gaussians * torch.arange(self.n_gaussians)
            return math.log(2*math.pi) + torch.logsumexp(self.broken**2 - self.broken*self.radius*math.sqrt(2) * torch.sin(phi_k + math.pi/4), dim=-1).item()