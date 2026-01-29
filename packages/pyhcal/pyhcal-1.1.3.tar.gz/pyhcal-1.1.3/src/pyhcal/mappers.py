# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 11:20:47 2025

@author: mfratki
"""

from pyhcal.repository import Repository
from hspf.uci import UCI
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# Try to load statewide subwatersheds from data folder,

# try:
#     SUBWATERSHEDS = gpd.read_file(str(Path(__file__).resolve().parent/'data\\statewide_subwatersheds.gpkg'))
# except:
#     print("Could not load statewide subwatersheds. Please ensure the file 'statewide_subwatersheds.gpkg' is located in the 'data' folder of the pyhcal package.")
    


class uciMapper():
    def __init__(self,model_names,gis_layer,huc6 = False):
        self.mappers = []
        
        if huc6:
            model_names = Repository.HUC_DIRECTORY.loc[Repository.HUC_DIRECTORY['Repository_HUC6 Name'].isin(model_names),'Repository_HUC8 Name']
            model_names = model_names.loc[model_names.isin(Repository.valid_models())].values
    
        for model_name in model_names:
            repo = Repository(model_name)
            uci = UCI(repo.uci_file)
            #gis_layer = SUBWATERSHEDS.loc[SUBWATERSHEDS['repo_name'] == model_name,:]
            #gis_layer.set_index('SubID',inplace=True)
            self.mappers.append(Mapper(model_name,uci,gis_layer))
    
    def map_parameter(self,operation,table_name,parameter,table_id):
        table = self.join_table(operation,table_name,table_id)
        fig, ax = plt.subplots()
        #[table.plot(column = parameter,ax = ax) for table in tables]
        table.plot(column = parameter,ax = ax,cmap='viridis',legend=True)
        plt.title(parameter)
    
    def join_table(self,operation,table_name,table_id):
        tables = [mapper.join_table(operation,table_name,table_id) for mapper in self.mappers]
        table = pd.concat(tables)
        return table
    
class Mapper():
    def __init__(self,model_name,uci,subwatershed_gdf,hbn = None):
        self.model_name = model_name
        self.uci = uci
        self.hbn = hbn
        # if subwatershed_gdf is None:
        #     subwatershed_gdf = SUBWATERSHEDS.loc[SUBWATERSHEDS['repo_name'] == model_name,:]
        #     subwatershed_gdf.set_index('SubID',inplace=True)
        
        self.subwatershed_gdf = subwatershed_gdf
        self.subwatersheds = uci.network.subwatersheds()
        self.subwatershed_ids = list(set(self.subwatersheds.index))

    def map_parameter(self,operation,table_name,parameter,table_id=0,weight_by_area = True):
        fig, ax = plt.subplots()
        self.join_table(operation,table_name,parameter,table_id).plot(column = parameter,ax = ax,cmap='viridis',legend=True)
        plt.title(parameter)
        
    def join_table(self,operation,table_name,parameter,table_id=0,weight_by_area = True):
        table = self.uci.table(operation,table_name,table_id)
        subwatersheds = self.uci.network.subwatersheds()
        subwatersheds = subwatersheds.loc[subwatersheds['SVOL'] == 'PERLND'].reset_index(drop=False).set_index('SVOLNO').join(table,how = 'left')
        subwatersheds.index.name = 'SVOLNO' # Sometimes the index name gets dropped. I'm guessing when there are missing joins.
        subwatersheds = subwatersheds.reset_index('SVOLNO').set_index(['SVOLNO','TVOLNO','SVOL','MLNO'])
        
        #weight by area factor:
        if weight_by_area:
            subwatersheds['weighted_param'] = subwatersheds['AFACTR']*subwatersheds[parameter]
            subwatersheds = subwatersheds.groupby(subwatersheds.index.get_level_values('TVOLNO'))['weighted_param'].sum()/subwatersheds.groupby(subwatersheds.index.get_level_values('TVOLNO'))['AFACTR'].sum()
            subwatersheds.name = parameter
        else:
            subwatersheds = subwatersheds.groupby(subwatersheds.index.get_level_values('TVOLNO'))[parameter].mean()
            subwatersheds.name = parameter
        return self.subwatershed_gdf.join(subwatersheds)
 
    def map_flag():
        raise NotImplementedError()
        
    def map_output(self,operation,output_name,t_code=5,agg_func = 'mean'):
        subwatersheds = self.subwatersheds.loc[(self.subwatersheds['SVOL'] == operation),:].copy()
        opnids = list(subwatersheds['SVOLNO'].unique())
        output = self.hbn.get_multiple_timeseries(operation,t_code,output_name,opnids = opnids).agg(agg_func)
        if operation in ['PERLND','IMPLND']:
            subwatersheds = pd.merge(subwatersheds,output.to_frame(output_name),right_index = True,left_on = 'SVOLNO')
            subwatersheds['area_output'] = subwatersheds['AFACTR']*subwatersheds[output_name]
            subwatersheds = subwatersheds[['AFACTR','area_output']].groupby(subwatersheds.index).sum()
            subwatersheds[output_name] = subwatersheds['area_output']/subwatersheds['AFACTR']
        
        fig, ax = plt.subplots()
        #[table.plot(column = parameter,ax = ax) for table in tables]
        self.subwatershed_gdf.join(subwatersheds).plot(column = output_name,ax = ax,cmap='viridis',legend=True)
        plt.title(output_name)
    
    def map_table(self,df, mapping_col):
        '''Maps a dataframe column to the subwatershed geodataframe based on subwatershed IDs.
        Assumes the dataframe index contains the subwatershed IDs.'''
        fig, ax = plt.subplots()
        #[table.plot(column = parameter,ax = ax) for table in tables]
        self.subwatershed_gdf.join(df).plot(column = mapping_col,ax = ax,cmap='viridis',legend=True)
        plt.title(mapping_col)
        #return self.subwatershed_gdf.join(subwatersheds)

 