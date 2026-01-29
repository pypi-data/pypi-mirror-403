#%% Imports
from mpcaHydro.data_manager import dataManager
from pathlib import Path
import duckdb
THIS_DIR = Path(__file__).parent
WISKI_STATIONS = ['E05011002']
EQUIS_STATIONS = ['S001-235','S005-115']

#%%
def test_build_warehouse():
    dm = dataManager(THIS_DIR)
    dm._build_warehouse()

test_build_warehouse()
# %%
def test_equis_data_download():
    dm = dataManager(THIS_DIR, 
                     oracle_username = 'MFRATKI',
                     oracle_password = 'DeltaT#MPCA3', 
                     reset=True)
    
    dm.connect_to_oracle()
    dm._download_equis_data(EQUIS_STATIONS)

test_equis_data_download()
#%%
def test_wiski_data_download():
    dm = dataManager(THIS_DIR, reset=True)
    dm._download_wiski_data(WISKI_STATIONS)


test_wiski_data_download()

#%%
dm = dataManager(THIS_DIR, reset=False)
with duckdb.connect(dm.db_path, read_only=True) as con:
    df = con.execute('SELECT * FROM analytics.outlet_observations').fetch_df()
    assert(df['outlet_id'].isnull().sum() == 0)

with duckdb.connect(dm.db_path, read_only=True) as con:
    df = con.execute('SELECT * FROM analytics.outlet_observations_with_flow').fetch_df()
    assert(df['outlet_id'].isnull().sum() == 0)
    assert(df['value'].isnull().sum() == 0)
# %%
dm = dataManager(THIS_DIR, reset=False)


def test_wiski_download():
    dm = dataManager(THIS_DIR, reset=False)
    wiski_stations = WISKI_STATIONS
    dm._download_wiski_data(wiski_stations)
    return dm

test_wiski_download()


with duckdb.connect(dm.db_path, read_only=True) as con:
    df = con.execute('SELECT * FROM analytics.outlet_observations_with_flow').fetch_df()
    assert(df['outlet_id'].isnull().sum() == 0)

# %%
