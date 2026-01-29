"""PostgreSQL logging handler.

Provides a custom logging handler that writes log records to a PostgreSQL
database table for centralized log storage and analysis.
"""

import logging
import datetime as dt
import psycopg2 as psg
from mynk_etl.utils.common.constants import Constants
from mynk_etl.utils.common.genUtils import fetch_db_dtl


postgres_dtl = fetch_db_dtl('Postgresql')

try:
    connection = psg.connect(host=postgres_dtl['hostname'], dbname=postgres_dtl['db'], user=postgres_dtl['username'], password=postgres_dtl['password'], port=postgres_dtl['port'])
except (Exception, psg.DatabaseError) as e:
    print("RDBMS connection failed to database : " + str(e))
else:
    cursor = connection.cursor()


def execute_query(qry: str) -> None:
    """Execute a SQL query against PostgreSQL database.

    Args:
        qry (str): SQL query string to execute

    Raises:
        Exception: Query execution errors are caught and logged,
                   but not propagated
    """
    try:
        cursor.execute(qry)
        connection.commit()
    except Exception as e:
        print(f'Error {e}')
        print('Anything else that you feel is useful')
        connection.rollback()


def close_connection():
    """Close PostgreSQL database connection and cursor."""
    cursor.close()
    connection.close()


log_tbl: str = f"""CREATE TABLE IF NOT EXISTS {postgres_dtl['schema']}.{postgres_dtl['table']} (
    run_id BIGINT NOT NULL,
    job_type VARCHAR(200) NOT NULL,
    level_name VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    logger VARCHAR(200) NOT NULL,
    module VARCHAR(200) NOT NULL,
    function_name VARCHAR(200) NOT NULL,
    filename VARCHAR(200) NOT NULL,
    line_num VARCHAR(200) NOT NULL,
    log_time VARCHAR(200) NOT NULL,
    PRIMARY KEY(run_id, log_time)
);"""

execute_query(log_tbl)


class CustomHandler(logging.StreamHandler):
    """Custom logging handler that writes logs to PostgreSQL database.

    Extends StreamHandler to insert formatted log records into a PostgreSQL
    table for centralized logging and audit trail.
    """

    def __init__(self):
        """Initialize the PostgreSQL logging handler."""
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        """Write log record to PostgreSQL database.

        Formats the log record and inserts it into the configured database table
        with run ID, log level, message, and file location information.

        Args:
            record (logging.LogRecord): The log record to write
        """
        if record:
            msg = record.getMessage()
            if msg.startswith('"') and msg.endswith('"'):
                msg = msg[1:-1]
            msg = msg.replace("'", "`")
            execute_query(f"INSERT INTO {postgres_dtl['schema']}.{postgres_dtl['table']} (run_id, job_type, level_name, message, logger, module, function_name, filename, line_num, log_time) VALUES ({Constants.RUN_ID.value},'pyStream','{record.levelname}','{msg}','{record.name}','{record.module}','{record.funcName}','{record.filename}',{record.lineno},'{dt.datetime.fromtimestamp(record.created, tz=None).isoformat()}')")
