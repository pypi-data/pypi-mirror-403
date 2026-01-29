#%%
from mpcaHydro.data_manager import dataManager
from pyhcal.repository import Repository
from mpcaHydro import outlets
import duckdb
from mpcaHydro import equis, warehouse, wiski
from hspf.hspfModel import hspfModel
from hspf.uci import UCI
from mpcaHydro import etlSWD


#%% 
'''
New approach. Directly load to warehouse from downloads. 
Store raw and processed data in warehouse. For large timeseries I could store
as parquet files. The transformations using pandas take a bit of time. I imagine doing them
within duckdb would be faster.

'''

# with warehouse.connect(db_path) as con:
#    df = con.execute("SELECT * FROM staging.wiski").df()
#    df = wiski.transform(df,filter_qc_codes = False)

#%%
model_name = 'Nemadji'
db_path = f'C:/Users/mfratki/Documents/{model_name}.duckdb'
start_year = 1996
end_year = 2030
replace = True
filter_qc_codes = True
equis_stations = outlets.equis_stations(model_name)
wiski_stations = outlets.wiski_stations(model_name)
equis.connect('MFRATKI',password = 'DeltaT#MPCA3')
warehouse.init_db(db_path,reset = True)


#%% Old approach. Store as indvidual processed station files then load to warehouse
#df_equis = equis.download(equis_stations)
#df_wiski = wiski.download(wiski_stations,start_year = start_year, end_year = end_year)

#%% equis




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


# Add to warehouse from custom df. Must contain required normalized columns.
with warehouse.connect(db_path,read_only = False) as con:
  if replace:
     warehouse.drop_station_id(con,station_id,station_origin='equis')
  warehouse.add_to_table(con,df, 'staging','equis_normalized')


  warehouse.load_df_to_staging(con,df, 'equis_raw',replace = replace)
  df = equis.normalize(df.copy())
  warehouse.add_to_table(con,df, 'staging','equis_normalized')
  df = equis.transform(df)
  warehouse.add_to_table(con,df, 'analytics','equis')



#%% swd

df = etlSWD.download(equis_stations)

with warehouse.connect(db_path,read_only = False) as con:
  warehouse.load_df_to_staging(con,df, 'equis_raw',replace = replace)
  df = equis.normalize(df.copy())
  warehouse.add_to_table(con,df, 'staging','equis_normalized')
  df = equis.transform(df)
  warehouse.add_to_table(con,df, 'analytics','equis')
#%% wiski



      if station_origin == 'wiski':
          df = wiski.download(station_ids,start_year = start_year, end_year = end_year)
          warehouse.load_df_to_staging(con,df, 'wiski_raw', replace = replace)
          df = wiski.normalize(df.copy())
          warehouse.add_to_table(con,df, 'staging','wiski_normalized')
          df = wiski.transform(df,filter_qc_codes = filter_qc_codes)
          warehouse.add_to_table(con,df, 'analytics','wiski') # method includes normalization

      if station_origin == 'swd':
          df = pd.concat([etlSWD.download(station_id) for station_id in station_ids])
          warehouse.load_df_to_staging(con,df, 'equis_raw', replace = replace)
          df = etlSWD.transform(df.copy())
          warehouse.add_to_table(con,df, 'analytics','equis')
      warehouse.update_views(con)

with warehouse.connect(db_path) as con:
  warehouse.update_views(con)


#%%

import requests
url = 'http://ifrshiny.seas.umich.edu/mglp/'
requests.get(url)


 
db_path = 'C:/Users/mfratki/Documents/Rum.duckdb'
modl_db.build_outlet_db(db_path)
con = duckdb.connect(db_path)
con.execute("SELECT * FROM station_reach_pairs").df()
con.execute('SELECT * FROM station_reach_pairs WHERE outlet_id = 76').df()

# Need to remove duplicates from MODL_DB
modl_db.MODL_DB.loc[modl_db.MODL_DB.duplicated(['station_id','source'])]

#%%
dm = dataManager('C:/Users/mfratki/Documents/')
dm._build_warehouse()
equis_stations = modl_db.equis_stations('Nemadji')
wiski_stations = modl_db.wiski_stations('Nemadji')

#%% Old approach. Store as indvidual processed station files then load to warehouse
for station_id in equis_stations:
    dm._download_station_data(station_id,'equis', True)
    
for station_id in wiski_stations:
    dm._download_station_data(station_id,'wiski', True)










#%% Adding HSPF outputs to warehouse











con = duckdb.connect(db_path)

model_name = 'Nemadji'
outlets = [group for _, group in modl_db.MODL_DB.query('repository_name == @model_name').groupby(by = ['opnids','repository_name'])]

for outlet in outlets:
    1+1


dfs = []
for constituent in ['Q','TSS','TP','N','OP','TKN']:
    opnids = modl_db.split_opnids([opnid.split(',') for opnid in set(outlet['opnids'].tolist())])
    for opnid in opnids:
        df = mod.hbns.get_reach_constituent(constituent,opnids,time_step='h')
        df.columns = ['value']
        df['constituent'] = constituent
        df['operation'] = operation
        df['opnid'] = opnid
        dfs.append(df)
        
df = pd.concat(dfs).reset_index()
df['model_name'] = model_name



station_ids = ['H05018001','S006-214','S015-102']
target_constituent = 'TSS'
flow_constituent = 'Q'

# build placeholders for the IN list (one ? per station id)
placeholders = ','.join(['?'] * len(station_ids))

sql = f'''
SELECT o.*, f.datetime AS flow_datetime, f.value AS flow, f.baseflow, f.station_id AS flow_station_id, f.station_origin AS flow_station_origin  
FROM analytics.observations o
JOIN analytics.observations f
  ON o.datetime = f.datetime
WHERE o.constituent = ?
  AND o.station_id IN ({placeholders})
  AND f.constituent = ?;
'''

# parameter order must match the ? positions in the query
params = [target_constituent] + station_ids + [flow_constituent]

df = con.execute(sql, params).df()

outlet_id: station_ids

outlet_id: opnid


outlets = []
for index, (_, group) in enumerate(modl_db.MODL_DB.groupby(by = ['opnids','repository_name'])):
    group['outlet_id'] = index
    group.reset_index(drop=True, inplace=True)
    outlets.append(group)


    for _, row in group.iterrows():
        opnids = group.split_opnids(row['opnids'].str.split(',').to_list())
        row*len(opnids)
