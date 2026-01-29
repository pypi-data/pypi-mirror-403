"""
pydcce - Dynamic Common Correlated Effects Estimation for Panel Data
=====================================================================

A Python implementation of the Stata xtdcce2 package for estimating
heterogeneous coefficient models with cross-sectional dependence.

Author: Dr. Merwan Roudane
Email: merwanroudane920@gmail.com
GitHub: https://github.com/merwanroudane/pydecce2

Main Components
---------------
Estimators:
    - MeanGroup: Mean Group Estimator (Pesaran & Smith, 1995)
    - CCE: Common Correlated Effects Estimator (Pesaran, 2006)
    - DynamicCCE: Dynamic CCE Estimator (Chudik & Pesaran, 2015)
    - PooledCCE: Pooled CCE Estimator
    - ECM: Error Correction Model (PMG)
    - CSDL: Cross-Section Augmented Distributed Lag
    - CSARDL: Cross-Section Augmented ARDL

Tests:
    - CDTest: Cross-Sectional Dependence Tests
      - CD (Pesaran, 2015)
      - CDw (Juodis & Reese, 2021)
      - CDw+ (Power Enhanced)
      - CD* (Pesaran & Xie, 2021)
    
    - ExponentEstimator: Alpha Exponent Estimation (BKP, 2016)

References
----------
- Pesaran, M.H. (2006). Econometrica, 74(4), 967-1012.
- Chudik, A., & Pesaran, M.H. (2015). Journal of Econometrics, 188(2), 393-420.
- Ditzen, J. (2018). The Stata Journal, 18(3), 585-617.
"""

__version__ = "1.0.0"
__author__ = "Dr. Merwan Roudane"
__email__ = "merwanroudane920@gmail.com"

# Core estimators
from pydcce.estimators.mean_group import MeanGroup
from pydcce.estimators.cce import CCE, DynamicCCE
from pydcce.estimators.pooled import PooledCCE
from pydcce.estimators.ecm import ECM
from pydcce.estimators.csdl import CSDL
from pydcce.estimators.csardl import CSARDL

# Tests
from pydcce.tests.cd_test import CDTest
from pydcce.tests.exponent import ExponentEstimator

# Utilities
from pydcce.utils.panel import PanelData

# Output
from pydcce.output.tables import ResultsTable

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Estimators
    "MeanGroup",
    "CCE",
    "DynamicCCE",
    "PooledCCE",
    "ECM",
    "CSDL",
    "CSARDL",
    # Tests
    "CDTest",
    "ExponentEstimator",
    # Utilities
    "PanelData",
    "ResultsTable",
]
