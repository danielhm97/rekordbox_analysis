# Importamos los paquetes necesarios
import re
import spotipy
from difflib import SequenceMatcher
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials

# Función para tener la URL
def get_track_url(spotify_track_id):
    return f'https://open.spotify.com/track/{spotify_track_id}'

# Funcion para extraer URLs de portadas
def get_image_link(images_list):
    url_dict = {}
    if isinstance(images_list, list) and len(images_list)>0:
        for url in images_list:
            url_dict[f'url_{url['height']}_{url['width']}'] = url['url']
        return url_dict    
    else:
        return url_dict

# Función para extraer nombre de artista y id    
def get_artists_info(artists_list):
    result = []
    
    if isinstance(artists_list, list) and len(artists_list) > 0:
        for artist in artists_list:
            # safe access with get()
            artist_id = artist.get('id')
            artist_name = artist.get('name')
            if artist_id and artist_name:
                result.append({'artist_name': artist_name, 'id': artist_id})
    
    return result

# Funcion para quitar tags de la cancion
def clean_query(title):
    """
    Removemos tags from a track_query, como:
    (original mix), (extended), (extended mix)
    """
    if not isinstance(title, str):
        return title
    
    # Patrones a remover
    patterns = [
        r'\(original mix\)',
        r'\(extended mix\)',
        r'\(extended\)',
        '- original mix'
    ]
    
    # Remueve todos los patrones, ignora mayusculas/minusculas
    for p in patterns:
        title = re.sub(p, '', title, flags=re.IGNORECASE)
    
    # Removemos espacios extras
    title = title.strip()
    
    return title

# Funcion que mide la similaridad entre dos strings
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Extraemos artistas del json, de artistas que entrega spotify
def extract_artist_names(artists,lowercase=True):
    if not isinstance(artists, list):
        return None
    
    if lowercase == True:
        return ', '.join(a['name'].lower() for a in artists if 'name' in a)
    else:
        return ', '.join(a['name'] for a in artists if 'name' in a)
    

# Armamos el string a buscar para cada track
def get_track_query(row):
    if not (pd.isna(row['rb_track_name']) & pd.isna(row['rb_artists'])):
        return (f'{row['rb_artists']} - {row['rb_track_name']}').lower()
    elif not pd.isna(row['rb_file_name']):
        return (f'{row['rb_file_name']}').lower()
    else:
        return pd.NA

# Buscamos el track con el resultado de la función get_track_query, y guardamos los primeros 20 resultados
# Esto para maximizar la calidad de la busqueda.
def get_spotify_info(track_query, sp):
    print(f'Obteniendo data del track: {track_query}')
    if not pd.isna(track_query):
        results = sp.search(q=track_query, type='track',limit=20, market='us')
        results = results['tracks']['items']
        results_df = pd.DataFrame(results)
        results_df = results_df[['album','artists','duration_ms','external_ids','id','name','popularity']]
        results_df['album_type'] = results_df['album'].apply(lambda d: d.get('album_type'))
        print('Respuesta exitosa, validando información..')
        return results_df
    else:
        print(f'Track invalido: {track_query}')
        results_df = pd.DataFrame([])

# Cuando tenemos mas de una fila en los resultados debemos definir de alguna, forma, usaremos el
# coeficiente de similaridad
def define_result_by_similarity (row, results):
    results_structure = results.iloc[0:0]
    results['artists_spotify'] = results['artists'].apply(lambda x :extract_artist_names(x))
    results = results.assign(spotify_compare = (results['artists_spotify'] + ' - ' + results['name']).str.lower())
    results['track_query'] = get_track_query(row)
    results = results.assign(similarity = results.apply(lambda row: similarity(row['spotify_compare'],row['track_query']), axis=1))    
    results = results.sort_values('similarity', ascending=False).reset_index(drop=True)
    results = results.head(1)
    results = results[results_structure.columns]
    return results

# Función que reintenta una busqueda una vez que no se encontro la canción buscada con una duración similar,
# se redefine la query y se intenta de nuevo, ahora el criterio deja de ser la duración sino la similitud
def check_name_similarity(row,sp):
    row_details = pd.DataFrame({
                'rb_track_id': [row['rb_track_id']],
                'track_query': [clean_query(get_track_query(row))]
                })
    
    track_query = clean_query(get_track_query(row))
    results = get_spotify_info(track_query,sp)
    results['duration_sec'] = results['duration_ms']//1000
    
    row_details = [row_details]*len(results)
    row_details = pd.concat(row_details, ignore_index=True).reset_index(drop=True)
    results = pd.concat([row_details, results], axis=1).reset_index(drop=True)

    results_structure = results.iloc[0:0]
    results_columns = results_structure.columns.tolist()
    results_columns.append('similarity')
    results['artists_spotify'] = results['artists'].apply(lambda x :extract_artist_names(x))
    results = results.assign(spotify_compare = (results['artists_spotify'] + ' - ' + results['name']).str.lower())
    results = results.assign(track_query_clean = results['track_query'].apply(lambda x: clean_query(x)))
    results = results.assign(similarity = results.apply(lambda row: similarity(row['spotify_compare'],row['track_query_clean']), axis=1))
    
    results = results[results['similarity'] >= 0.7]
    
    if results.shape[0]>=1:
        results = results.sort_values(by=['similarity','popularity'], ascending=[False,False]).reset_index(drop=True)
        results = results.head(1).reset_index(drop=True)
        results = results[results_columns]
        results['quality_result'] = ['coef_similarity_mult_results']
        print(f'Extracción exitosa para el track: {track_query}')
        return results
    else:
        results = results_structure
        results['similarity'] = pd.NA
        results = pd.concat([results,row_details.loc[0].to_frame().T], ignore_index=True)
        results['quality_result'] = ['track_not_found']
        print(f'Extracción fallida para el track: {track_query}')
        return results


# Formateamos el resultado de la api
def get_results_spotify(row,sp):
    track_query = get_track_query(row)
    results = get_spotify_info(track_query,sp)
    rb_duration_sec = row['rb_duration_sec']

    row_details = pd.DataFrame({
            'rb_track_id': [row['rb_track_id']],
            'track_query': [track_query]
            })

    if results.shape[0]>0:
        # Calculamos duración en segundos, solo parte entera
        results['duration_sec'] = results['duration_ms']//1000
        # Calculamos indice de similaridad, respecto a la query
        results['artists_spotify'] = results['artists'].apply(lambda x :extract_artist_names(x))
        results = results.assign(spotify_compare = (results['artists_spotify'] + ' - ' + results['name']).str.lower())
        results = results.assign(similarity = results.apply(lambda row: similarity(row['spotify_compare'],track_query), axis=1))
        results = results.sort_values('similarity', ascending=False).reset_index(drop=True)
        # Como minimo la similaridad debe ser de 0.6, si cumple con los requisitos de duracion
        results = results[results['similarity']>=0.6].reset_index(drop=True)
        
        # Verificamos que alguno de los resultados tenga la misma duración que el archivo en local
        # guardamos 1 solo registro
        if len(results[results['duration_sec'] == rb_duration_sec])==1:
            results = results[results['duration_sec'] == rb_duration_sec].reset_index(drop=True)
            results = pd.concat([row_details, results], axis=1)
            results['quality_result'] = ['exact_duration_unique_result']
            results['spotify_timestamp'] = [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")]
            print(f'Extracción exitosa para el track: {track_query}')
            return results
        elif len(results[results['duration_sec'] == rb_duration_sec])>1:
            results = results[results['duration_sec'] == rb_duration_sec].reset_index(drop=True)
            results = results.sort_values(by=['similarity','popularity'], ascending=[False,False]).reset_index(drop=True)
            results = results.head(1).reset_index(drop=True)
            results = pd.concat([row_details,results],axis=1)
            results['quality_result'] = ['exact_duration_multiple_result']
            results['spotify_timestamp'] = [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")]
            print(f'Extracción exitosa para el track: {track_query}')
            return results
        # Verificamos la duración con un gap de +-10 segundos
        # guardamos 1 solo registro
        elif len(results[results['duration_sec'].between(rb_duration_sec-10, rb_duration_sec+10)])>=1:
            results = results[results['duration_sec'].between(rb_duration_sec-10, rb_duration_sec+10)].reset_index(drop=True)
            results = results.sort_values(by=['similarity','popularity'], ascending=[False,False]).reset_index(drop=True)
            results = results.head(1).reset_index(drop=True)
            results = pd.concat([row_details,results],axis=1)
            results['quality_result'] = ['10_sec_gap_multiple_result']
            results['spotify_timestamp'] = [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")]
            print(f'Extracción exitosa para el track: {track_query}')
            return results
        else:
            print(f'Extracción fallida para el track: {track_query}')
            results = check_name_similarity(row,sp)
            results['spotify_timestamp'] = [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")]
            return results
