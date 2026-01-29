
"""General utility functions for configuration and database operations.

Provides helper functions for initializing parameters from configuration
and fetching database connection details.
"""

from typing import Any
from mynk_etl.utils.common.constants import Constants


def param_init(key: str) -> Any:
    """Initialize and parse configuration parameters from key.

    Extracts configuration components from a composite key and returns
    the relevant configuration dictionaries.

    Args:
        key (str): Configuration key in format 'table_group.table_name'

    Returns:
        tuple: A tuple containing:
            - prop_key (str): Table name extracted from key
            - conf_dict (dict): Infrastructure configuration for the table group
            - prop_dict (dict): Table-specific configuration
    """

    conf_key = key.split('.')[0]
    prop_key = key.split('.')[1]
    conf_dict = Constants.INFRA_CFG.value[conf_key]
    prop_dict = Constants.TBL_CFG.value[conf_key][prop_key]

    return prop_key, conf_dict, prop_dict


def fetch_db_dtl(db_type: str) -> dict[str, str | int]:
    """Fetch database connection details from configuration.

    Args:
        db_type (str): Database type identifier (e.g., 'Postgresql')

    Returns:
        dict[str, str | int]: Database configuration containing hostname,
                             port, username, password, database, schema
    """
    db_dtl = Constants.INFRA_CFG.value[db_type]
    return db_dtl

