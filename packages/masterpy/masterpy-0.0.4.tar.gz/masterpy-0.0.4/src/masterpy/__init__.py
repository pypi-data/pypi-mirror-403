#!/usr/bin/env python
"""
__init__
===========
Initializes masterpy package and discovers all modules.

Authors:   Michael Landis, Ammon Thompson
Copyright: (c) 2022-2023, Michael Landis and Ammon Thompson
License:   MIT
"""

__project__ = 'masterpy'
__version__ = '0.0.4'
__author__ = 'Michael Landis and Ammon Thompson'
__copyright__ = '(c) 2022-2023, Michael Landis and Ammon Thompson'

# DEFAULT
MASTERPY_VERSION = __version__

from . import util
from .util import (
    get_xml_run_spec,
    get_xml_output_spec,
    convert_phy2dat_nex,
    blank_phy2dat_nex,
    convert_phy2dat_nex_geosse,
    events2df,
    load,
    param_dict_to_str,
    write_to_file,
    sort_binary_vectors,
    get_popSize_at_t,
    get_combined_popSize_at_t,
    get_sim_time,
    #get_json_stats,
    remove_stem_branch,
    get_age_most_recent_tip,
    make_extant_phy,
    #states2df,
    log_params,
    logit_params,
    States,
    Event,
)

from . import models
from .models import (
    model
)
