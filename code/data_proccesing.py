import pandas as pd
import json
import os

def data_processing(rb_collection_path,rb_history_path,spotify_result_api_path,spotify_playcount_path):
    if (os.path.exists(rb_collection_path) and 
        os.path.exists(rb_history_path) and 
        os.path.exists(spotify_result_api_path) and
        os.path.exists(spotify_playcount_path)):

        # Leemos
        rekordbox_collection_df = pd.read_csv(rb_collection_path, sep=',', encoding='utf-8')
        rekordbox_history_df = pd.read_csv(rb_history_path, sep=',', encoding='utf-8')
        spotify_result_api_df = pd.read_csv(spotify_result_api_path, sep=',', encoding='utf-8')

        with open(spotify_playcount_path) as f:
            spotify_playcount_df = json.load(f)

        spotify_playcount_df = pd.DataFrame(spotify_playcount_df.items())
        spotify_playcount_df.columns = ['spotify_track_id','spotify_playcount']   

        # Hacemos los merge necesarios
        spotify_result_api_df = spotify_result_api_df.merge(spotify_playcount_df,on='spotify_track_id',how='left')
        master_collection_df = rekordbox_collection_df.merge(spotify_result_api_df, on ='rb_track_id', how='left')
        master_history_df = rekordbox_history_df.merge(master_collection_df, left_on='rbh_track_id',right_on='rb_track_id',how='left')

        # Guardamos la bases de datos MASTER
        master_collection_df.to_csv('./data/master/master_collection.csv',sep=',',encoding='utf-8',index=False)
        master_history_df.to_csv('./data/master/master_history.csv',sep=',',encoding='utf-8',index=False)
    else:
        print('Revise que todos los archivos requeridos existan en sus correspondientes directorios.')
