
import pandas as pd
#from abc import abstractmethod
from pathlib import Path
from mpcaHydro import equis, wiski, warehouse
import duckdb





#%%
'''
This modules contains classes and functions to manage data downloads and storage into a local data warehouse.


'''

def get_db_path(warehouse_path:Path,db_name:str = 'observations')->Path:
    '''
    Constructs the full path to the database file within the warehouse directory.

    Parameters:
    warehouse_path (Path): The path to the warehouse directory.
    db_name (str): The name of the database file.

    Returns:
    Path: The full path to the database file.
    '''
    return Path(warehouse_path) / db_name

def construct_database(db_path:Path,db_name:str = 'observations')->Path:
    '''
    Constructs the full path to the database file within the warehouse directory.

    Parameters:
    warehouse_path (Path): The path to the warehouse directory.
    db_name (str): The name of the database file.

    Returns:
    Path: The full path to the database file.
    '''
    db_path = Path(db_path) / db_name
    warehouse.init_db(warehouse_path=db_path)


def create_normalized_wiski_view(con: duckdb.DuckDBPyConnection):
    """
    Create a view in the database that contains normalized WISKI data.
    """
    con.execute("""
    CREATE OR REPLACE VIEW analytics.normalized_wiski AS
    SELECT
        *""")

