"""Top-level package for esgtoolkit."""

__author__ = """T. Moudiki"""
__email__ = "thierry.moudiki@gmail.com"
__version__ = "1.0.0"

from .simdiff import simdiff
from .simshocks import simshocks
from .esgcortest import esgcortest
from .esgdiscountfactor import esgdiscountfactor
from .esgfwdrates import esgfwdrates
from .esgmartingaletest import esgmartingaletest
from .esgmccv import esgmccv
from .esgmcprices import esgmcprices
from .esgplotbands import esgplotbands
from .esgplotshocks import esgplotshocks
from .esgplotts import esgplotts

__all__ = [
    "simdiff",
    "simshocks",
    "esgcortest",
    "esgdiscountfactor",
    "esgfwdrates",
    "esgmartingaletest",
    "esgmccv",
    "esgmcprices",
    "esgplotbands", 
    "esgplotshocks",
    "esgplotts"
]
