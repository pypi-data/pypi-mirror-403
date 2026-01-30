import torch
import torch.nn as nn
import math
import omegaconf
import nflows.transforms as transforms

import logging
logger = logging.getLogger("symmetry")

# set up dict with names and classes
STOCHMODS = {}
def register_stochmod(name):
    def wrap(clss):
        STOCHMODS[name] = clss
        return clss
    return wrap



class StochasticModulation(nn.Module):
    def __init__(self, **kwargs):
        super(StochasticModulation, self).__init__()

    def forward(self, x):
        # flip the sign of the log_modprob part
        # in the flow.sample_with_logpprob function the log_prob is computed as
        # log_prob = prior_log_prob - log_det1 - log_det2 - ... - log_detN
        # to compensate the negative sign in the log_det, we need to flip the sign of the log_modprob for the stochastic modulation
        # As with the log_modprob, the total log_prob is computed as
        # log_prob = prior_log_prob + log_modprob - log_det1 - log_det2 - ... - log_detN
        # see eq. (12) in the paper
        x, log_modprob = self.transform(x)
        return x, -log_modprob

    def reverse(self, x):
        x, log_modprob = self.inverse_transform(x)
        return x, -log_modprob
    
    def transform(self, x):
        raise NotImplementedError
    
    def inverse_transform(self, x):
        raise NotImplementedError



# ==============================
# DISCRETE SYMMETRIES
# ==============================

@register_stochmod("z2_stochmod")
class Z2Modulation(StochasticModulation):
    def __init__(self, **kwargs):
        """
        Description:
            This class implements a Z2 symmetry where the sign of the configuration is flipped with 50% probability.
        """
        super(Z2Modulation, self).__init__()

        logger.info(f"Initialized Z2 Stochastic Modulation")

    def transform(self, x):
        """
        Args:
            x (torch.Tensor): input tensor of shape (Batch, N_t, N_x)

        Returns:
            x (torch.Tensor): output tensor with flipped signs
            log_modprob (torch.Tensor): log of modulation probability p_S
        """
        assert x.dim() == 3, f"dim of x should be 2, got {x.dim()}"

        N = x.shape[0]

        # sample from bernoulli distribution to flip the sign randomly
        bernoulli = torch.distributions.Bernoulli(torch.tensor(0.5, device=x.device, dtype=x.dtype))
        u = bernoulli.sample((N, 1, 1)).to(x.device) # either 0 or 1 with 50% probability
        random_sign = -2 * u + 1 # either 1 (u=0) or -1 (u=1)

        # apply signs
        x = x * random_sign

        # compute log of modulation probability
        log_modprob = math.log(0.5)

        return x, log_modprob
    


@register_stochmod("brokenz2_stochmod")
class BrokenZ2Modulation(StochasticModulation):
    def __init__(self, flip_direction=None, init_breaking=math.log(0.5), **kwargs):
        """
        Args:
            dim (list): list of dimensions where to flip the sign, use [] or None for all dimensions
            init_breaking (float): initial value of the breaking parameter, should be smaller or equal to 0

        Description:
            Flips the sign of the input tensor with a probability depending on the breaking parameter.
            The dimensions that should be flipped are specified in the flip_direction list.
            E.g., if flip_direction = [0], the tensor x = [1, 2, 3] -> [-1, 2, 3] with a probability of e^b
            The breaking parameter is a learnable parameter that is initialized to init_breaking.
            The probability of flipping the sign is given by p = e^b where b is the breaking parameter.
        """
        assert init_breaking <= 0, f"init_breaking should be smaller or equal to 0, got {init_breaking}"
        assert type(flip_direction) == list or type(flip_direction) == omegaconf.listconfig.ListConfig or flip_direction == None, f"flip_direction should be a list or None, got {flip_direction}"

        super(BrokenZ2Modulation, self).__init__()
        self.breaking = nn.Parameter(torch.tensor(init_breaking, dtype=torch.float32), requires_grad=True)
        self.flip_direction = flip_direction

        logger.info(f"Initialized Broken Z2 Stochastic Modulation with breaking parameter {init_breaking:.3f} and flip direction {flip_direction}")

    def transform(self, x):
        """
        Args:
            x (torch.Tensor): input tensor of shape (Batch, N_t, N_x)

        Returns:
            x (torch.Tensor): output tensor with flipped signs
            log_modprob (torch.Tensor): log of modulation probability p_S
        """
        if self.flip_direction != [] and self.flip_direction != None:
            assert max(self.flip_direction) < x.shape[2], f"dim {self.flip_direction} is out of bounds for the N_x = {x.shape[2]}"
        assert x.dim() == 3, f"dim of input tensor x should be 3, got {x.dim()}"

        # the breaking parameter should be smaller or equal to 0
        self.breaking.data.clamp_max_(0)

        # sample from bernoulli distribution to randomly flip the sign
        dist = torch.distributions.Bernoulli(torch.exp(self.breaking))
        u = dist.sample((x.shape[0],)).to(x.device) # either 0 or 1 with probability p = e^b
        random_sign = -2 * u + 1 # either 1 (u=0) or -1 (u=1)

        # create random sign tensor
        if self.flip_direction == None or self.flip_direction == []:
            random_sign_full = random_sign.unsqueeze(1).unsqueeze(2)
        else:
            random_sign_full = torch.ones((x.shape[0], 1, x.shape[2]), device=x.device)
            for dim in self.flip_direction:
                random_sign_full[:,0,dim] = random_sign

        # apply signs
        x = x * random_sign_full

        # compute log of modulation probability
        self.log_modprob = dist.log_prob(u)

        return x, self.log_modprob



@register_stochmod("zn_stochmod")
class ZNModulation(StochasticModulation):
    def __init__(self, n=8, **kwargs):
        """
        Args:
            n (int): refers to the Z_n symmetry, e.g. Z_8 has 8 possible rotations

        Description:
            This class implements a Z_n symmetry that is equivalant to a discrete rotation symmetry in a 2D plane with n possible rotations.
        """
        super(ZNModulation, self).__init__()
        self.n = n

        logger.info(f"Initialized ZN Stochastic Modulation with n={n}")


    def transform(self, x):
        """
        Args:
            x (torch.Tensor): input tensor of shape (Batch, N_t, N_x)
        Returns:
            x (torch.Tensor): output tensor with rotated signs
            log_modprob (torch.Tensor): log of modulation probability p_S
        """
        assert x.shape[2] == 2, f"3rd dim of x should be 2, i.e., (batch, nt, 2), but got {x.shape}"

        # sample random rotation
        random = torch.randint(0, self.n, (x.shape[0],1), device=x.device)
        angle = 2 * math.pi * random / self.n

        # apply rotation
        # x = x @ rotation_matrix
        x = torch.stack([x[:,:,0] * torch.cos(angle) - x[:,:,1] * torch.sin(angle), 
                         x[:,:,0] * torch.sin(angle) + x[:,:,1] * torch.cos(angle)], dim
                         =2)

        # compute log of modulation probability
        log_modprob = math.log(1/self.n)

        return x, log_modprob
    
    
@register_stochmod("broken_zn_stochmod")
class BrokenZNModulation(StochasticModulation):
    def __init__(self, n=8, **kwargs):
        """
        Args:
            n (int): refers to the Z_n symmetry, e.g. Z_8 has 8 possible rotations

        Description:
            This class implements a broken Z_n symmetry that is equivalant to a discrete rotation symmetry in a 2D plane with n possible rotations.
        """
        super(BrokenZNModulation, self).__init__()
        self.n = n
        
        init_breaking = -math.log(n) * torch.ones(n, dtype=torch.float32)
        self.breaking = nn.Parameter(init_breaking, requires_grad=True)

        logger.info(f"Initialized Broken ZN Stochastic Modulation with n={n}")


    def transform(self, x):
        """
        Args:
            x (torch.Tensor): input tensor of shape (Batch, N_t, N_x)
        Returns:
            x (torch.Tensor): output tensor with rotated signs
            log_modprob (torch.Tensor): log of modulation probability p_S
        """
        assert x.shape[2] == 2, f"3rd dim of x should be 2, i.e., (batch, nt, 2), but got {x.shape}"

        # sample random rotation
        dist = torch.distributions.Categorical(logits=self.breaking)
        random = dist.sample((x.shape[0],1)).to(x.device)
        angle = 2 * math.pi * random / self.n

        # apply rotation
        # x = x @ rotation_matrix
        x = torch.stack([x[:,:,0] * torch.cos(angle) - x[:,:,1] * torch.sin(angle), 
                         x[:,:,0] * torch.sin(angle) + x[:,:,1] * torch.cos(angle)], dim
                         =2)

        # compute log of modulation probability
        self.log_modprob = dist.log_prob(random).squeeze(1)

        return x, self.log_modprob
    
    
    
@register_stochmod("brokenzpown_stochmod")
class BrokenZpowNModulation(StochasticModulation):
    def __init__(self, n_dims=2, **kwargs):
        """
        Description:
            This class implements a broken ZN symmetry where the sign in each dimension is flipped with a learanble probability.
        """
        nn.Module.__init__(self)

        # create learnable tensor with 2**n_dims parameters
        log_probs_init = -n_dims*math.log(2) * torch.ones((2**n_dims), dtype=torch.float32, requires_grad=True) 
        self.flip_log_prob = nn.Parameter(log_probs_init, requires_grad=True)

        # for tensorboard logging
        self.breaking_list = None
        if 2**n_dims < 100:
            self.breaking_list = self.flip_log_prob.tolist()

        # get flip directions
        self.flip_directions = self.get_flip_directions(n_dims) # list of 2**n_dims entries
        
        num_groups = len(self.flip_directions)
        flip_directions_tensor = torch.zeros((num_groups, n_dims+1), dtype=torch.bool)

        for i, dims in enumerate(self.flip_directions):
            flip_directions_tensor[i, dims] = True

        # Store permanently:
        self.register_buffer("flip_directions_tensor", flip_directions_tensor)

        logger.info(f"Initialized BrokenFlipSignsZN with {2**n_dims-1} parameter(s)")
        
        
    def get_flip_directions(self, n_dims):
        """
        Args:
            N_x (int): number of dimensions
        
        Returns:
            flip_directions (list): list of 2^N_x entries with all possible flip directions

        Description:
            For N_x=2 the flip_directions tensor looks like this: [[], [0], [1], [0, 1]]
            The first entry is an empty list, which means no flip. The second entry is [0], which means flip the sign in the first dimension.
        """

        flip_directions = [[]]*(2**n_dims)
        for i in range(2**n_dims):
            dims = []
            for j in range(n_dims):
                if i & (1 << j):
                    dims.append(j)
            flip_directions[i] = dims

        if 2**n_dims < 10:
            logger.info(f"Initialized flip directions: {flip_directions}")

        return flip_directions



    def transform(self, x):
        assert x.dim() == 3, f"x should be of shape (Batch, N_t, N_x), got {x.shape}"

        N = x.shape[0]
        Nx = x.shape[2]

        # update brekeaking list
        if len(self.flip_log_prob) < 100:
            self.breaking_list = self.flip_log_prob.tolist()

        # sample from categorical distribution
        dist = torch.distributions.Categorical(logits=self.flip_log_prob)
        random_flip_directions = dist.sample((N,)).to(x.device)

        # Produce: (N, Nx) boolean mask of where to flip
        flip_mask = self.flip_directions_tensor[random_flip_directions]   # (N, Nx-1)

        # Create output
        random_sign = torch.ones((N, 1, Nx), device=x.device)

        # Apply flips where mask is true
        random_sign[:, 0].masked_fill_(flip_mask, -1)

        # apply flips
        x = x * random_sign

        # compute log_modprob
        log_modprob = dist.log_prob(random_flip_directions)

        return x, log_modprob
    
    
@register_stochmod("hubbard_stochmod")
class HubbardModulation(StochasticModulation):
    def __init__(self, n_dims=2, **kwargs):
        """
        Description:
            This class implements an exact Z2 symmetry and a broken ZN symmetry with N = 2^(Nx - 1)
            This symmetry is used for the Hubbard model in the spin basis.
        """
        super().__init__(**kwargs)

        # init exact z2 flips
        self.z2modulation = Z2Modulation()

        # init broken zn flips, with n = 2^(n_dims-1)
        self.brokenzpownmodulation = BrokenZpowNModulation(n_dims-1)

        # update brekeaking list
        self.breaking_list = self.brokenzpownmodulation.flip_log_prob.tolist()


    def transform(self, x):
        """
        Args:
            x (torch.Tensor): input tensor of shape (Batch, N_t, N_x)

        Returns:
            x (torch.Tensor): output tensor with flipped signs

            log_det (torch.Tensor): log determinant of the transformation
        """
        # update brekeaking list
        self.breaking_list = self.brokenzpownmodulation.flip_log_prob.tolist()

        # apply flips
        x, log_det2 = self.brokenzpownmodulation(x)
        x, log_det1 = self.z2modulation(x)
    
        return x, log_det1 + log_det2

    
    
    

# ==============================
# CONTINUOUS SYMMETRIES
# ==============================

@register_stochmod("u1_stochmod")
class U1Modulation(StochasticModulation):
    def __init__(self, **kwargs):
        """
        Description:
            This class implements a U1 symmetry that is equivalant to a continuous rotation symmetry in a 2D plane.
        """
        super(U1Modulation, self).__init__()

        logger.info(f"Initialized U1 Stochastic Modulation")


    def transform(self, x):
        """
        Args:
            x (torch.Tensor): input tensor of shape (Batch, 1, N_t, N_x)
        Returns:
            x (torch.Tensor): output tensor with rotated signs of shape (Batch, 2, N_t, N_x)
            log_modprob (torch.Tensor): log of modulation probability p_S
        """
        assert len(x.shape) == 4 and x.shape[1] == 1, f"x should be of shape (Batch, 1, N_t, N_x), got {x.shape}"

        # sample random rotation
        angle = torch.rand((x.shape[0],1,1), device=x.device) * 2 * math.pi

        # apply rotation
        x = torch.stack([x[:,0] * torch.cos(angle), 
                         x[:,0] * torch.sin(angle)], dim
                         =1)

        # compute log of modulation probability
        log_modprob = -math.log(2 * math.pi)

        return x, log_modprob
    


@register_stochmod("brokenu1_stochmod")
class BrokenU1Modulation(StochasticModulation):
    def __init__(self, lat_shape, **kwargs):
        """
        Description:
            This class implements a U1 symmetry that is equivalant to a continuous rotation symmetry in a 2D plane.
            The symmetry is broken which means that some angles are preferred over others.
            This is done by using a rational quadratic spline to sample the angles.
        """
        super(BrokenU1Modulation, self).__init__()

        # Define Rational Quadratic Spline (RQS) transformation
        self.spline = transforms.MaskedPiecewiseRationalQuadraticAutoregressiveTransform(
            features=1,
            hidden_features=5,
            num_bins=8,
        )

        logger.info(f"Initialized Broken U1 Stochastic Modulation with RQS")


    def transform(self, x):
        """
        Args:
            x (torch.Tensor): input tensor of shape (Batch, 1, N_t, N_x)
        Returns:
            x (torch.Tensor): output tensor with rotated signs of shape (Batch, 2, N_t, N_x)
            log_modprob (torch.Tensor): log of modulation probability p_S
        """
        assert len(x.shape) == 4 and x.shape[1] == 1, f"x should be of shape (Batch, 1, N_t, N_x), got {x.shape}"

        # sample random rotation
        uniform = torch.rand((x.shape[0],1), device=x.device)
        angle, log_det_spline = self.spline(uniform)
        angle = angle.reshape(-1,1,1) * 2 * math.pi

        # apply rotation
        x = torch.stack([x[:,0] * torch.cos(angle), 
                         x[:,0] * torch.sin(angle)], dim
                         =1)

        # compute log of modulation probability
        # see eq. (43)
        self.log_modprob = -log_det_spline - math.log(2 * math.pi)

        return x, self.log_modprob

