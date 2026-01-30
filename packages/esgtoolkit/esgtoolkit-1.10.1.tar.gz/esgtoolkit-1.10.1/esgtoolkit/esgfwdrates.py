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


def esgfwdrates(
    in_maturities,
    in_zerorates,
    n,
    horizon,
    out_frequency="annual",
    method="fmm",
    return_R_obj=False,
    **kwargs,
):
    """Simulations of diffusion processes, that are building blocks for various risk factors' models."""
    if not R_IS_INSTALLED:
        raise ImportError("R is not installed! \n" + USAGE_MESSAGE)

    if not RPY2_IS_INSTALLED:
        raise ImportError(RPY2_ERROR_MESSAGE + USAGE_MESSAGE)

    assert out_frequency in (
        "annual",
        "semi-annual",
        "quarterly",
        "monthly",
        "weekly",
        "daily",
    ), "out_frequency must be one of 'annual', 'semi-annual', 'quarterly', 'monthly', 'weekly', 'daily'"

    assert method in (
        "fmm",
        "periodic",
        "natural",
        "monoH.FC",
        "hyman",
        "HCSPL",
        "SW",
    ), "method must be one of 'fmm', 'periodic', 'natural', 'monoH.FC', 'hyman', 'HCSPL', 'SW'"

    res = ESGTOOLKIT_PACKAGE.esgfwdrates(
        FLOATVECTOR(in_maturities),
        FLOATVECTOR(in_zerorates),
        n=n,
        horizon=horizon,
        out_frequency=out_frequency,
        method=method,
        **kwargs,
    )

    if return_R_obj:
        return res

    return pd.DataFrame(np.array(res), columns=res.colnames, index=r.time(res))
