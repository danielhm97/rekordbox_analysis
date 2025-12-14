# Importamos los paquetes necesarios
import os
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Importamos las funciones de spotify_process.py
from spotify_process import *

def spotify_api(rb_collection_path):
    # Credenciales
    client_id = '0da8e80195a24af3a03d202268f41566'
    client_secret = '223278d9e5f04f4cb134079c8a7035c0'

    spc = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=spc)

    if os.path.exists(rb_collection_path):
        # Leemos el dataframe
        rb_collection_df = pd.read_csv(rb_collection_path, sep=',', encoding='utf-8', header=0)
        # Obtenemos resultado para cada canción
        results_api = pd.concat(rb_collection_df.apply(lambda row: get_results_spotify(row,sp), axis=1).tolist(), ignore_index=True)
        results_api.reset_index(drop=True)
        # Resumen respecto a la calidad de los resultados
        print('Resumen respecto a la calidad de los resultados')
        print(results_api['quality_result'].value_counts())

        # Hacemos las transformaciones necesarias
        results_api = results_api.assign(spotify_artists = results_api['artists'].apply(lambda x:extract_artist_names(x,lowercase=False)))
        results_api = results_api.assign (spotify_isrc_id = results_api['external_ids'].str.get('isrc'))
        results_api = results_api.assign(spotify_release_date = results_api['album'].str.get('release_date'))
        results_api = results_api.assign(spotify_release_date_precision = results_api['album'].str.get('release_date_precision')) 
        results_api = results_api.assign(spotify_album_covers = results_api['album'].str.get('images').apply(lambda x: get_image_link(x)) )
        results_api = results_api.assign(spotify_artist_info = results_api['artists'].apply(get_artists_info))

        # Nos quedamos solo con las columnas necesarias
        useful_columns = ['rb_track_id', 'track_query','id','name', 'spotify_artists','similarity',
                      'album_type','duration_ms','duration_sec', 'popularity', 'quality_result',
                      'spotify_release_date', 'spotify_release_date_precision',
                      'spotify_isrc_id','spotify_artist_info','spotify_album_covers','spotify_timestamp']

        results_api = results_api[useful_columns]

        # Renombramos las columnas para mantener una consistencia
        results_api = results_api.rename(columns={
        'id': 'spotify_track_id',
        'name': 'spotify_name',
        'album_type': 'spotify_album_type',
        'duration_ms': 'spotify_duration_ms',
        'duration_sec': 'spotify_duration_sec',
        'popularity':'spotify_popularity',
        'quality_result' : 'spotify_quality_result',
        })

        # Guardamos la información recopilada a un csv
        results_api.to_csv(f'./data/spotify/spotify_result.csv',sep=',',index=False,encoding='utf-8')
    else:
        print("El archivo 'rekordbox_collection.csv' no existe, no se puede ejecutar este proceso sin el.")
