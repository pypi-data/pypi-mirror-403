"""
RDHonest: Honest Inference in Regression Discontinuity Designs

This package provides honest and efficient confidence intervals in fuzzy and
sharp regression discontinuity (RD) designs using bias-aware inference methods.

Based on the R package by Michal Kolesar and Timothy B. Armstrong.

Main Functions
--------------
rd_honest / RDHonest
    Main function for honest inference in sharp/fuzzy RD designs.
rd_honest_bme / RDHonestBME
    Honest CIs for sharp RD with discrete running variables under BME.
cvb / CVb
    Critical values for biased Gaussian estimators.
rd_scatter / RDScatter
    Scatterplot of binned observations.
rd_smoothness_bound / RDSmoothnessBound
    Lower bounds on smoothness constant M.
rd_t_efficiency_bound / RDTEfficiencyBound
    Efficiency bounds for minimax CIs.

Data Loading
------------
load_lee08
    Lee (2008) US House elections data.
load_cghs
    Oreopoulos (2006) UK general household survey.
load_rcp
    Battistin et al. (2009) retirement consumption puzzle data.
load_headst
    Ludwig & Miller (2007) Head Start program data.
load_rebp
    Lalive (2008) Austrian unemployment duration data.

References
----------
Armstrong, T.B. and Kolesar, M. (2018). Optimal inference in a class of
    regression models. Econometrica, 86(2):655-683.

Armstrong, T.B. and Kolesar, M. (2020). Simple and honest confidence intervals
    in nonparametric regression. Quantitative Economics, 11(1):1-39.

Kolesar, M. and Rothe, C. (2018). Inference in regression discontinuity designs
    with a discrete running variable. American Economic Review, 108(8):2277-2304.
"""

__version__ = "0.0.1"

# Core functions
from .rdhonest import rd_honest, RDHonest
from .rd_bme import rd_honest_bme, RDHonestBME
from .cvb import cvb
from .plots import rd_scatter, RDScatter
from .cbound import rd_smoothness_bound
from .rd_opt import rd_t_efficiency_bound

# Alias for R users (CamelCase versions)
CVb = cvb
RDSmoothnessBound = rd_smoothness_bound
RDTEfficiencyBound = rd_t_efficiency_bound

# Data classes
from .utils import RDData, SRDData, FRDData, IPData, RDResults, create_rd_data

# Kernel utilities
from .kernels import eq_kern, triangular_kernel, epanechnikov_kernel, uniform_kernel

# Data loading functions
from .datasets import (
    load_lee08,
    load_cghs,
    load_rcp,
    load_headst,
    load_rebp,
)

__all__ = [
    # Main functions
    "rd_honest",
    "RDHonest",
    "rd_honest_bme",
    "RDHonestBME",
    "cvb",
    "CVb",
    "rd_scatter",
    "RDScatter",
    "rd_smoothness_bound",
    "RDSmoothnessBound",
    "rd_t_efficiency_bound",
    "RDTEfficiencyBound",
    # Data classes
    "RDData",
    "SRDData",
    "FRDData",
    "IPData",
    "RDResults",
    "create_rd_data",
    # Kernels
    "eq_kern",
    "triangular_kernel",
    "epanechnikov_kernel",
    "uniform_kernel",
    # Data loaders
    "load_lee08",
    "load_cghs",
    "load_rcp",
    "load_headst",
    "load_rebp",
]
