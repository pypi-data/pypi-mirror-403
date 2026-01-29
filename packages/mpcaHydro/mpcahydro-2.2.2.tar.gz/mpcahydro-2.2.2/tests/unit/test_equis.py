
#%%
from mpcaHydro import equis
from mpcaHydro import outlets



#%%
model_name = 'Rum'
equis_stations = outlets.equis_stations(model_name)
equis.connect('MFRATKI',password = 'DeltaT#MPCA3')

df = equis.download(equis_stations)

df_normalized = equis.normalize(df.copy())
expected_columns = ['station_id', 'constituent', 'cas_rn', 'datetime', 'value', 'unit']

assert all(col in df_normalized.columns for col in expected_columns)
# %%
