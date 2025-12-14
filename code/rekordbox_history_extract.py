# Importamos los paquetes necesarios
import pandas as pd
import xml.etree.ElementTree as ET

def get_history(rekordbox_xml_path):
    print('Extrayendo historial de sets\n')
    # Creamos el objeto en el que vamos a iterar 'tree'
    tree = ET.parse(rekordbox_xml_path)
    root = tree.getroot()
    
    # Revisamos el path donde se ubican los sets, el objetivo es extraer la playlist para cada dj set
    sets_path = root.find('./PLAYLISTS/NODE')
    
    # Creamos una lista de 'sets' que contendra la lista de 'tracks' en cada nodo que empiece por 'HISTORY'
    sets = []
    for node in sets_path:
        node_name = node.attrib['Name']
        # Verificamos el nodo sea uno que empice por 'HISTORY', ya que es lo que nos sirve
        if node_name.startswith('HISTORY'):
            set_info = node.attrib
            key_tracks = []
            # En cada nodo 'HISTORY' iteramos por cada nodo 'TRACK'
            for track in node.findall('TRACK'):
                # Verificamos que cada nodo 'TRACK' solo tenga un atributo y que este sea 'Key'
                if (len(track.attrib) == 1) and (list(track.attrib.keys())[0]== 'Key'):
                    key_tracks.append(int(list(track.attrib.values())[0]))
                else:
                    # En caso de que no cumpla con lo requerido, imprimimos mensaje para revisar manualmente
                    print(f"La lista: '{node_name}' tiene inconsistencias al momento de exportar la lista de tracks")
    
            if (int(node.attrib['Entries']) != len(node.findall('TRACK'))):
                print(f"Para el set de nombre:'{node_name}' la lista de track no coincide con lo registrado")
            
            set_info['track_list'] = key_tracks
            sets.append(set_info)
    
    # Transformamos a dataframe
    sets = pd.DataFrame(sets)

    # Mostramos cuantos sets se extrajeron
    print(f'Se copiaron exitosamente {sets.shape[0]} set(s).\n')

    # Eliminamos columnas innecesarias
    sets = sets.drop(columns=['Type','KeyType','Entries'])
    
    # Extendemos la columna 'tracklist', cada celda sera una
    # fila de ahora en adelante manteniendo las columnas restantes intactas
    sets = sets.explode('track_list').reset_index(drop= True)
    
    # Extraemos la fecha de creación del set
    sets['date'] = sets['Name'].str.extract(r"(\d{4}-\d{2}-\d{2})")
    sets['date'] = pd.to_datetime(sets['date']).dt.date
    
    # Ordenamos por 'date' y 'Name' de forma ascendente
    sets = sets.sort_values(by = ['date','Name'], ascending=[True, True])
    
    # Asginamos de forma ascendente un numero a cada set
    sets['set_number'] = sets.groupby(['date','Name']).ngroup()
    
    # Agregamos timestamp
    sets['rbh_extract_timestamp'] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Cambiamos el nombre de la columna name, para que sea mas facil trabajar con ella
    sets = sets.rename(columns={'Name': 'rbh_set_name',
                                'track_list':'rbh_track_id',
                                'date':'rbh_created_date',
                                'set_number':'rbh_set_number'})
        
    # Guardamos a un CSV
    sets.to_csv(f'./data/rekordbox/rekordbox_history.csv',sep=',',index=False,encoding='utf-8')
    print('Extraccion de sets exitosa!!\n')
    