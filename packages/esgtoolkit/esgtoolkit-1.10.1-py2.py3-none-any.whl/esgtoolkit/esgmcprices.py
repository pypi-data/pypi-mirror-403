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


def esgmcprices(R, X, maturity=R_NULL, return_R_obj=False):
    """Stochastic discount factors or discounted values."""
    if not R_IS_INSTALLED:
        raise ImportError("R is not installed! \n" + USAGE_MESSAGE)

    if not RPY2_IS_INSTALLED:
        raise ImportError(RPY2_ERROR_MESSAGE + USAGE_MESSAGE)

    res = ESGTOOLKIT_PACKAGE.esgmcprices(R, X=X, maturity=maturity)

    if return_R_obj:
        return res

    return pd.DataFrame(np.asarray(res), index=r.time(res))
