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


def esgmartingaletest(R, X, p0, alpha=0.05, return_R_obj=False):
    """Martingale and market consistency (t-)tests."""

    if not R_IS_INSTALLED:
        raise ImportError("R is not installed! \n" + USAGE_MESSAGE)

    if not RPY2_IS_INSTALLED:
        raise ImportError(RPY2_ERROR_MESSAGE + USAGE_MESSAGE)

    res = ESGTOOLKIT_PACKAGE.esgmartingaletest(R, X=X, p0=p0, alpha=alpha)

    if return_R_obj:
        return res

    res_dict = dict(zip(res.names, list(res)))
    res_dict["t"] = np.array(res.rx2("t"))
    res_dict["p.value"] = np.array(res.rx2("p.value"))
    res_dict["samplemean"] = np.array(res.rx2("samplemean"))
    res_dict["conf.int"] = pd.DataFrame(
        np.array(res.rx2("conf.int")),
        columns=["lower", "upper"],
        index=r.time(res.rx2("conf.int")),
    )
    res_dict["truemean"] = np.array(res.rx2("truemean"))
    res_dict["true_prices"] = np.array(res.rx2("true_prices"))
    res_dict["mc.prices"] = np.array(res.rx2("mc.prices"))
    return res_dict
