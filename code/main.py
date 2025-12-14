from rekordbox_collection_extract import get_collection
from rekordbox_history_extract import get_history
from spotify_api import spotify_api
from spotify_scraper import spotify_scraper
from data_proccesing import data_processing

# Path para el archivo rekordbox.xml
rekordbox_xml_path = './data/rekordbox/rekordbox.xml'
# Path para el archivo 'rekordbox_collection.csv'
rb_collection_path = './data/rekordbox/rekordbox_collection.csv'
# Path para la data extraida de la API
spotify_data_path = './data/spotify/spotify_result.csv'
# Path para el historial de rekordbox
rb_history_path = './data/rekordbox/rekordbox_history.csv'
# Path para el contador de reproducciones de spotify
spotify_playcount_path = './data/spotify/spotify_playcount.json'



def main():
    # Obtenemos la coleccion desde el XML
    get_collection(rekordbox_xml_path)
    # Obtenemos el historial desde el XML
    get_history(rekordbox_xml_path)
    # Obtenemos informacion desde la API de Spotify
    spotify_api(rb_collection_path)
    # Scrapeamos Spotify para obtener el numero de reproducciones cuando es posible
    spotify_scraper(spotify_data_path)
    # Procesamos toda la data y consolidamos en dos archivos
    # maste_collection.csv y master_history ambos seran creados en './data/master'
    data_processing(rb_collection_path,rb_history_path, spotify_data_path, spotify_playcount_path)

if __name__ == "__main__":
    main()
