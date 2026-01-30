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


def ycinter(
    matsin,
    matsout,
    yM=R_NULL,
    p=R_NULL,
    method="NS",
    typeres="rates",
    return_R_obj=False,
):
    """Yield curve or zero-coupon bonds prices curve interpolation using the Nelson-Siegel , Svensson, Smith-Wilson models and an Hermite cubic spline."""
    if not R_IS_INSTALLED:
        raise ImportError("R is not installed! \n" + USAGE_MESSAGE)

    if not RPY2_IS_INSTALLED:
        raise ImportError(RPY2_ERROR_MESSAGE + USAGE_MESSAGE)

    assert method in (
        "NS",
        "SV",
        "SW",
        "HCSPL",
    ), "method must be one of 'NS', 'SV', 'SW', 'HCSPL'"

    assert typeres in (
        "rates",
        "prices",
    ), "typeres must be one of 'rates', 'prices'"

    res = ESGTOOLKIT_PACKAGE.ycinter(
        yM=FLOATVECTOR(yM),
        p=FLOATVECTOR(p),
        matsin=FLOATVECTOR(matsin),
        matsout=FLOATVECTOR(matsout),
        method=method,
        typeres=typeres,
    )

    if return_R_obj:
        return res

    return pd.DataFrame(np.array(res), columns=res.colnames, index=r.time(res))
