# -*- coding: utf-8 -*-
"""
Module constants.py
===========================================

This module specifies the Fundamental Dimensional Units (FDUs) available by default in *PyDASA*. The default framework are the Physical FDUs.

The three main types of FDUs are:
    1. Physical FDUs: in `PHY_FDU_PREC_DT` representing the standard physical dimensions.
    2. Digital FDUs: in `COMPU_FDU_PREC_DT` representing dimensions relevant to computation.
    3. Software Architecture FDUs: in `SOFT_FDU_PREC_DT` representing dimensions specific to software architecture.

The fourth FDU framework is:
    4. Custom FDUs: user-defined FDUs that can be specified as needed.
"""
# python native modules

# global variables

# Default config folder name + settings
# :attr: DFLT_CFG_FOLDER
DFLT_CFG_FOLDER: str = "cfg"
# :attr: DFLT_CFG_FILE
DFLT_CFG_FILE: str = "default.json"
"""
*PyDASA* default configuration folder and file names.
"""
