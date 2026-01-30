import numpy as np
import pandas as pd
from .config import (
    R_IS_INSTALLED,
    RPY2_IS_INSTALLED,
    RPY2_ERROR_MESSAGE,
    USAGE_MESSAGE,
    ESGTOOLKIT_PACKAGE,
    FLOATMATRIX,
    FLOATVECTOR,
    STRVECTOR,
    R_NULL,
)
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri, r

base = importr("base")
stats = importr("stats")


def simshocks(
    n=10,
    horizon=5,
    frequency="annual",
    method="classic",
    family=R_NULL,
    par=R_NULL,
    par2=R_NULL,
    RVM=R_NULL,
    type="CVine",
    start=R_NULL,
    seed=123,
    return_R_obj=True,
):
    """Simulations of diffusion processes, that are building blocks for various risk factors' models."""
    if not R_IS_INSTALLED:
        raise ImportError("R is not installed! \n" + USAGE_MESSAGE)

    if not RPY2_IS_INSTALLED:
        raise ImportError(RPY2_ERROR_MESSAGE + USAGE_MESSAGE)

    assert frequency in (
        "annual",
        "semi-annual",
        "quarterly",
        "monthly",
        "weekly",
        "daily",
    ), "frequency must be one of ('annual', 'semi-annual', 'quarterly', 'monthly', 'weekly', 'daily')"

    assert type in (
        "CVine",
        "DVine",
        "RVine",
    ), "type must be one of ('CVine', 'DVine', 'RVine')"

    assert method in (
        "classic",
        "antithetic",
        "mm",
        "hybridantimm",
        "TAG",
    ), 'method must be one of ("classic", "antithetic", "mm", "hybridantimm", "TAG")'

    res = ESGTOOLKIT_PACKAGE.simshocks(
        n=n,
        horizon=horizon,
        frequency=frequency,
        method=method,
        family=family,
        par=par,
        par2=par2,
        RVM=RVM,
        type=type,
        start=start,
        seed=seed,
    )

    if return_R_obj:
        return res

    # convert R object to pandas dataframe
    return pd.DataFrame(
        np.asarray(res), columns=res.colnames, index=r.time(res)
    )
