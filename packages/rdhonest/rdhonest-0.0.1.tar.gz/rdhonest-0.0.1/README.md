# RDHonest - Python

Honest and efficient confidence intervals in regression discontinuity designs.

This is a Python port of the R package [RDHonest](https://github.com/kolesarm/RDHonest) by Michal Kolesár and Timothy B. Armstrong.

## Installation

```bash
pip install rdhonest
```

Or install from source:

```bash
pip install -e .
```

## Quick Start

```python
import rdhonest as rdh
import numpy as np

# Load example data
lee08 = rdh.load_lee08()

# Sharp RD with uniform kernel
results = rdh.rd_honest(
    Y=lee08['voteshare'].values,
    X=lee08['margin'].values,
    cutoff=0,
    kern="uniform",
    M=0.1,
    h=10
)
print(results)

# Or use R-style formula interface
results = rdh.RDHonest(
    formula="voteshare ~ margin",
    data=lee08,
    cutoff=0,
    kern="triangular",
    M=0.1,
    h=10
)
```

## Features

- **Sharp and Fuzzy RD**: Support for both sharp and fuzzy regression discontinuity designs
- **Honest Inference**: Bias-aware confidence intervals that are valid under smoothness assumptions
- **Optimal Bandwidth Selection**: MSE, FLCI, and OCI criteria
- **Multiple Kernels**: Triangular, Epanechnikov, Uniform, and Optimal kernels
- **Smoothness Bounds**: Estimate lower bounds on the smoothness constant M
- **BME Class**: Support for bounded misspecification error function class
- **Clustering**: Cluster-robust standard errors
- **Covariates**: Covariate adjustment support

## Main Functions

### `rd_honest` / `RDHonest`

Main function for honest inference in RD designs.

```python
results = rdh.rd_honest(
    Y,              # Outcome variable
    X,              # Running variable
    cutoff=0,       # RD cutoff
    M=None,         # Smoothness constant (uses ROT if None)
    kern="triangular",  # Kernel type
    h=None,         # Bandwidth (optimal if None)
    opt_criterion="MSE",  # Bandwidth criterion
    se_method="nn", # SE estimation method
    alpha=0.05,     # Significance level
    sclass="H",     # Smoothness class: "H" (Holder) or "T" (Taylor)
)
```

### `rd_honest_bme` / `RDHonestBME`

Honest CIs for discrete running variables under BME class.

```python
cghs = rdh.load_cghs()
results = rdh.rd_honest_bme(
    Y=np.log(cghs['earnings'].values),
    X=cghs['yearat14'].values,
    cutoff=1947,
    h=3,
    order=1
)
```

### `cvb` / `CVb`

Critical values for biased Gaussian estimators.

```python
# 95% critical value with bias B=1
cv = rdh.cvb(B=1, alpha=0.05)

# Standard 95% critical value (no bias)
cv = rdh.cvb(B=0)
```

### `rd_scatter` / `RDScatter`

Binned scatterplot for RD visualization.

```python
import matplotlib.pyplot as plt

lee08 = rdh.load_lee08()
ax = rdh.rd_scatter(
    Y=lee08['voteshare'].values,
    X=lee08['margin'].values,
    cutoff=0,
    avg=50
)
plt.show()
```

## Included Datasets

- `load_lee08()`: Lee (2008) US House elections
- `load_cghs()`: Oreopoulos (2006) UK general household survey
- `load_rcp()`: Battistin et al. (2009) retirement consumption puzzle
- `load_headst()`: Ludwig & Miller (2007) Head Start program
- `load_rebp()`: Lalive (2008) Austrian unemployment duration

## References

- Armstrong, T.B. and Kolesár, M. (2018). Optimal inference in a class of regression models. *Econometrica*, 86(2):655-683.

- Armstrong, T.B. and Kolesár, M. (2020). Simple and honest confidence intervals in nonparametric regression. *Quantitative Economics*, 11(1):1-39.

- Kolesár, M. and Rothe, C. (2018). Inference in regression discontinuity designs with a discrete running variable. *American Economic Review*, 108(8):2277-2304.

## License

GPL-3.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
