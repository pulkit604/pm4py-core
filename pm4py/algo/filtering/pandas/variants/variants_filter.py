'''
    This file is part of PM4Py (More Info: https://pm4py.fit.fraunhofer.de).

    PM4Py is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    PM4Py is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PM4Py.  If not, see <https://www.gnu.org/licenses/>.
'''
from pm4py.algo.filtering.common import filtering_constants
from pm4py.util.constants import CASE_CONCEPT_NAME
from pm4py.statistics.traces.generic.pandas import case_statistics
from pm4py.statistics.traces.generic.pandas.case_statistics import get_variants_df
from pm4py.util.constants import PARAMETER_CONSTANT_CASEID_KEY, PARAMETER_CONSTANT_ACTIVITY_KEY
from enum import Enum
from pm4py.util import exec_utils
from copy import copy
import deprecation
from typing import Optional, Dict, Any, Union, Tuple, List
import pandas as pd


class Parameters(Enum):
    CASE_ID_KEY = PARAMETER_CONSTANT_CASEID_KEY
    ACTIVITY_KEY = PARAMETER_CONSTANT_ACTIVITY_KEY
    DECREASING_FACTOR = "decreasingFactor"
    POSITIVE = "positive"


@deprecation.deprecated("2.2.11", "3.0.0", details="Removed")
def apply_auto_filter(df, parameters=None):
    """
    Apply an automatic filter on variants

    Parameters
    -----------
    df
        Dataframe
    parameters
        Parameters of the algorithm, including:
            Parameters.CASE_ID_KEY -> Column that contains the Case ID
            Parameters.ACTIVITY_KEY -> Column that contains the activity
            variants_df -> If provided, avoid recalculation of the variants dataframe
            Parameters.DECREASING_FACTOR -> Decreasing factor that should be passed to the algorithm

    Returns
    -----------
    df
        Filtered dataframe
    """
    if parameters is None:
        parameters = {}
    case_id_glue = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, CASE_CONCEPT_NAME)
    decreasing_factor = exec_utils.get_param_value(Parameters.DECREASING_FACTOR, parameters,
                                                   filtering_constants.DECREASING_FACTOR)
    variants_df = case_statistics.get_variants_df(df, parameters=parameters)
    parameters["variants_df"] = variants_df
    variants = case_statistics.get_variant_statistics(df, parameters=parameters)

    admitted_variants = []
    if len(variants) > 0:
        current_variant_count = variants[0][case_id_glue]

        for i in range(len(variants)):
            if variants[i][case_id_glue] >= decreasing_factor * current_variant_count:
                admitted_variants.append(variants[i]["variant"])
            else:
                break
            current_variant_count = variants[i][case_id_glue]

    return apply(df, admitted_variants, parameters=parameters)


def apply(df: pd.DataFrame, admitted_variants: List[List[str]], parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> pd.DataFrame:
    """
    Apply a filter on variants

    Parameters
    -----------
    df
        Dataframe
    admitted_variants
        List of admitted variants (to include/exclude)
    parameters
        Parameters of the algorithm, including:
            Parameters.CASE_ID_KEY -> Column that contains the Case ID
            Parameters.ACTIVITY_KEY -> Column that contains the activity
            Parameters.POSITIVE -> Specifies if the filter should be applied including traces (positive=True)
            or excluding traces (positive=False)
            variants_df -> If provided, avoid recalculation of the variants dataframe

    Returns
    -----------
    df
        Filtered dataframe
    """
    if parameters is None:
        parameters = {}

    case_id_glue = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, CASE_CONCEPT_NAME)
    positive = exec_utils.get_param_value(Parameters.POSITIVE, parameters, True)
    variants_df = parameters["variants_df"] if "variants_df" in parameters else get_variants_df(df,
                                                                                                parameters=parameters)
    variants_df = variants_df[variants_df["variant"].isin(admitted_variants)]
    i1 = df.set_index(case_id_glue).index
    i2 = variants_df.index
    if positive:
        ret = df[i1.isin(i2)]
    else:
        ret = df[~i1.isin(i2)]

    ret.attrs = copy(df.attrs) if hasattr(df, 'attrs') else {}
    return ret
