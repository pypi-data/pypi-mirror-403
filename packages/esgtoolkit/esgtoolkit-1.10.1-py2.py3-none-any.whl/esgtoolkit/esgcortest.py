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


def esgcortest(
    x,
    alternative="two.sided",
    method="pearson",
    conf_level=0.95,
    return_R_obj=False,
):
    if not R_IS_INSTALLED:
        raise ImportError("R is not installed! \n" + USAGE_MESSAGE)

    if not RPY2_IS_INSTALLED:
        raise ImportError(RPY2_ERROR_MESSAGE + USAGE_MESSAGE)

    assert alternative in (
        "two.sided",
        "less",
        "greater",
    ), "alternative must be one of ('two.sided', 'less', 'greater')"

    assert method in (
        "pearson",
        "kendall",
        "spearman",
    ), "method must be one of ('pearson', 'kendall', 'spearman')"

    assert conf_level > 0 and conf_level < 1, "conf_level must be > 0 and < 1"

    if return_R_obj:
        return ESGTOOLKIT_PACKAGE.esgcortest(
            x, alternative=alternative, method=method, conf_level=conf_level
        )

    # return a dictionary of dataframes
    res = ESGTOOLKIT_PACKAGE.esgcortest(
        x, alternative=alternative, method=method, conf_level=conf_level
    )
    res_dict = {}
    res_dict["cor.estimate"] = pd.DataFrame(
        np.array(res.rx2("cor.estimate")),
        columns=["cor.estimate"],
        index=r.time(res.rx2("cor.estimate")),
    )
    res_dict["conf.int"] = pd.DataFrame(
        np.array(res.rx2("conf.int")),
        columns=["lower", "upper"],
        index=r.time(res.rx2("cor.estimate")),
    )

    return res_dict
