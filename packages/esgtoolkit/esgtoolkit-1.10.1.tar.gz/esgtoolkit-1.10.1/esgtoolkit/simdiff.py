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
from rpy2.robjects import conversion, default_converter, pandas2ri, r


base = importr("base")
stats = importr("stats")


def simdiff(
    n=10,
    horizon=5,
    frequency="annual",
    model="GBM",
    x0=100,
    theta1=0.06,
    theta2=1.5,
    theta3=0.2,
    lam=R_NULL,
    mu_z=R_NULL,
    sigma_z=R_NULL,
    p=R_NULL,
    eta_up=R_NULL,
    eta_down=R_NULL,
    eps=R_NULL,
    start=R_NULL,
    seed=123,
    return_R_obj=False,
):
    """Simulations of diffusion processes, that are building blocks for various risk factors' models."""
    if not R_IS_INSTALLED:
        raise ImportError("R is not installed! \n" + USAGE_MESSAGE)

    if not RPY2_IS_INSTALLED:
        raise ImportError(RPY2_ERROR_MESSAGE + USAGE_MESSAGE)

    #assert frequency in (
    #    "annual",
    #    "semi-annual",
    #    "quarterly",
    #    "monthly",
    #    "weekly",
    #    "daily",
    #), "frequency must be one of ('annual', 'semi-annual', 'quarterly', 'monthly', 'weekly', 'daily')"

    #assert model in (
    #    "GBM",
    #    "CIR",
    #    "OU",
    #), "model must be one of ('GBM', 'CIR', 'OU')"    

    res = ESGTOOLKIT_PACKAGE.simdiff(
        n=n,
        horizon=horizon,
        frequency=frequency,
        model=model,
        x0=x0,
        theta1=theta1,
        theta2=theta2,
        theta3=theta3,
        lam=lam,
        mu_z=mu_z,
        sigma_z=sigma_z,
        p=p,
        eta_up=eta_up,
        eta_down=eta_down,
        eps=eps,
        start=start,
        seed=seed,
    )

    if return_R_obj:
        return res

    # convert R object to pandas dataframe
    return pd.DataFrame(
        np.asarray(res), columns=res.colnames, index=r.time(res)
    )
