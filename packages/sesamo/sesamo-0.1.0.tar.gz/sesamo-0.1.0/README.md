# SESaMo: Symmetry-Enforcing Stochastic Modulation for Normalizing Flows

## Quick installation

Move into the repository's directory and create a new python environment:
```
$ cd SESaMo
$ python -m venv .venv
$ source .venv/bin/activate
```
Install the SESaMo module with pip:
```
$ pip install -e .
```

## Run experiments

Run experiments with
```
cd scripts
python train.py -cp configs/<experiment> -cn <model>
```

Available ```<experiment>```s are:
```
hubbard
gaussian-mixture
broken-gaussian-mixture
complex-phi4
broken-complex-phi4
broken-scalar-phi4
```

Available ```<model>```s are:
```
realnvp
vmonf
canonicalization
sesamo
```

The checkpoint, tensorboard, config and stats files are stored in the ```SESaMo/scripts/runs``` folder.

After training is completed or interupted the distribution is plotted and saved as ```SESaMo/scripts/runs/.../samples.png```