# Importamos los paquetes necesarios
import pandas as pd
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote

# Importamos las funciones de rb_process.py
from rb_process import *

def get_collection(rekordbox_xml_path):
    print('Extrayendo colección de tracks')
    # Creamos el objeto en el que vamos a iterar 'tree'
    tree = ET.parse(rekordbox_xml_path)
    root = tree.getroot()

    # Revisamos el path donde se ubican los tracks
    tracks_path = root.find('./COLLECTION')

    # Revisamos que tag tienen los childs y cuantos de cada uno
    print("Para el path './COLLECTION' tenemos los siguientes nodos child.")
    print(f'{check_childs_n_freq(tracks_path)}\n')

    # Creamos una lista de 'tracks'
    tracks = []

    for track in tracks_path:
        # Verificamos que sea un track
        if track.tag == 'TRACK':
            info = track.attrib  # Copiamos los atributos de cada <TRACK ...>
            tracks.append(info)

    # Transformamos 'tracks'a una base de datos
    tracks_df = pd.DataFrame(tracks)

    # Eliminamos las siguientes columnas, ya que no seran utiles para nuestro analisis
    cols_to_ignore = (['Composer','Grouping','DiscNumber','TrackNumber',
                       'Comments','Rating','Remixer','Mix','BitRate','SampleRate'])

    tracks_df = tracks_df.drop(columns=cols_to_ignore)

    # Transformamos los nombres de las columnas de 'camelCase' a 'sneak_case'
    tracks_df.columns = (tracks_df.columns
                         .str.replace(r'(?<!^)([A-Z])', r'_\1', regex=True,n=1)
                         .str.lower())

    # verificamos cuantos nodos 'TRACK' se copiaron al dataframe
    print(f'Se copiaron exitosamente al dataframe {len(tracks_df)} track(s).\n')

    # Cambiaremos los nombres de las columnas para que sea mas comodo de trabajar
    tracks_df = tracks_df.rename(columns={'track_id':'rb_track_id',
                                          'name':'rb_track_name',
                                          'artist':'rb_artists',
                                          'album':'rb_album',
                                          'genre':'rb_genre',
                                          'kind':'rb_file_type',
                                          'size':'rb_file_size_bytes',
                                          'total_time':'rb_duration_sec',
                                          'year':'rb_year_release',
                                          'average_bpm':'rb_average_bpm',
                                          'date_added':'rb_date_added',
                                          'play_count':'rb_playcount',
                                          'location': 'rb_file_name',
                                          'tonality':'rb_tonality',
                                          'label':'rb_label'})

    # Realizaremos las transformaciones de tipos de dato necesarias
    tracks_df.rb_file_size_bytes = tracks_df.rb_file_size_bytes.astype(int)
    tracks_df.rb_duration_sec = tracks_df.rb_duration_sec.astype(int)
    tracks_df.rb_year_release = tracks_df.rb_year_release.astype(int)
    tracks_df.rb_average_bpm = tracks_df.rb_average_bpm.astype(float)
    tracks_df.rb_date_added = pd.to_datetime(tracks_df.rb_date_added).dt.date
    tracks_df.rb_playcount = tracks_df.rb_playcount.astype(int)

    
    # Transformamos la columna
    tracks_df.rb_file_name = tracks_df.rb_file_name.apply(lambda x: get_file_name(x))
    # Agregamos timestamp
    tracks_df['rb_extract_timestamp'] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    # Corregimos las columnas necesarias
    tracks_df['rb_file_type'] = tracks_df['rb_file_type'].str.replace(" File", "", regex=False)
    tracks_df['rb_genre'] = tracks_df['rb_genre'].replace({
        "Deep Tech": "Deep Tech, Minimal",
        "Minimal": "Deep Tech, Minimal"
        })
    
    # Mostramos las columnas que tienen celdas vacias ''
    empty_summary = tracks_df.apply(
        lambda col: sum(col.astype(str).str.strip().eq(""))
    )
    
    if empty_summary[empty_summary > 0].shape[0] > 0:
        print('Las columnas con valores vacios y sus frecuencias son las siguientes:')
        print(f'{empty_summary[empty_summary > 0]}\n')
    else: 
        print('No hay columnas con valores vacios.\n')
    # Mostramos las columnas que tienen celdas con NaN
    nas = tracks_df.isna().sum()
    # Nos quedamos con las columnas que solo tengan nas y su frecuencia
    if nas[nas > 0].shape[0] > 0:
        print('Las columnas con valores NaN y sus frecuencias son las siguientes:')
        print(f'{nas[nas > 0]}\n')
    else: 
        print('No hay columnas con valores NaN.\n')

    # Exportamos la base de datos de tracks que sera utilizada, posteriormente
    tracks_df.to_csv(f'./data/rekordbox/rekordbox_collection.csv',sep=',',index=False,encoding='utf-8')

    print('Extraccion de tracks exitosa!!\n')
