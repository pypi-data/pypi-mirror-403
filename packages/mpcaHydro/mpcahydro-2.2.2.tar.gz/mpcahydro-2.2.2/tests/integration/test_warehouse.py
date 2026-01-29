#%% Imports
from mpcaHydro import warehouse
from mpcaHydro import equis,wiski
from mpcaHydro import outlets
from pathlib import Path
THIS_DIR = Path(__file__).parent

#%%

db_path = THIS_DIR /'test_warehouse.duckdb'
warehouse.init_db(db_path, reset=True)



#%%
def test_init_db():
    db_path = THIS_DIR /'test_warehouse.duckdb'
    warehouse.init_db(db_path, reset=True)

    with warehouse.connect(db_path) as con:
        result = con.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = [row[0] for row in result]
        expected_tables = [
            'equis_raw',
            'wiski_raw',
            'equis',
            'wiski'
        ]
        for table in expected_tables:
            assert table in table_names, f"Table {table} not found in database."

        expected_views = [
            'observations',
            'outlet_observations',
            'outlet_observations_with_flow',
            'wiski_qc_count',
            'constituent_summary',
            'outlet_constituent_summary'
        ]

        result = con.execute("""SELECT
                                    *
                                FROM
                                    duckdb_views
                                WHERE
                                    NOT internal;""").fetchall()
        view_names = [row[4] for row in result] # TODO: Should use a more robust way to get view names
        #print(view_names)
        for view in expected_views:
            assert view in view_names, f"View {view} not found in database."

# %%
#%%
model_name = 'Nemadji'
db_path = f'C:/Users/mfratki/Documents/{model_name}.duckdb'
start_year = 1996
end_year = 2030
replace = True
filter_qc_codes = True
equis_stations = outlets.equis_stations(model_name)
#wiski_stations = outlets.wiski_stations(model_name)
equis.connect('MFRATKI',password = 'DeltaT#MPCA3')

db_path = THIS_DIR /'test_warehouse.duckdb'
warehouse.init_db(db_path, reset=True)


wiski_df = wiski.download(['E05011002'])
equis_df = equis.download(equis_stations)

#%%


with warehouse.connect(db_path,read_only = False) as con:
    if not equis_df.empty:
      warehouse.load_df_to_table(con,equis_df, 'staging.equis',replace = replace)
      warehouse.load_df_to_table(con,equis.transform(equis_df.copy()), 'analytics.equis',replace = replace)
    else:
      print('No data neccesary for HSPF calibration available from equis for stations:',station_ids)

with warehouse.connect(db_path,read_only = False) as con:
    if not wiski_df.empty:
      warehouse.load_df_to_table(con,wiski_df, 'staging.wiski', replace = replace)
      warehouse.load_df_to_table(con,wiski.transform(wiski_df.copy()), 'analytics.wiski',replace = replace)
    else:
      print('No data neccesary for HSPF calibration available from wiski for stations:',station_ids)

with warehouse.connect(db_path) as con:
   warehouse.update_views(con)

#%%

def test_equis_raw_column_names():
    with warehouse.connect(dm.db_path) as con:
        warehouse.get_column_names(con,'staging.equis')

def download_equis_data(db_path,station_ids,replace = False):
  with warehouse.connect(db_path,read_only = False) as con:
    df = equis.download(station_ids)
    if not df.empty:
      warehouse.load_df_to_table(con,df, 'staging.equis',replace = replace)
      warehouse.load_df_to_table(con,equis.transform(df), 'analytics.equis',replace = replace)
    else:
      print('No data neccesary for HSPF calibration available from equis for stations:',station_ids)

def download_wiski_data(db_path,station_ids,replace = False):
  with warehouse.connect(db_path,read_only = False) as con:
    df = wiski.download(station_ids,start_year = start_year, end_year = end_year)
    if not df.empty:
      warehouse.load_df_to_table(con,df, 'staging.wiski', replace = replace)
      warehouse.load_df_to_table(con,wiski.transform(df), 'analytics.wiski',replace = replace)
    else:
      print('No data neccesary for HSPF calibration available from wiski for stations:',station_ids)
