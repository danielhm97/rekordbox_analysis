import pandas as pd
import os 
import json
import time
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# Importamos las funciones de spotify_process.py
from spotify_process import get_track_url

def spotify_scraper(spotify_data_path):
    
    spotify_data = pd.read_csv(spotify_data_path,sep=',',encoding='utf-8')
    # Solo nos quedamos con lo necesario
    spotify_data = spotify_data[['rb_track_id','spotify_track_id']]
    
    spotify_playcount_path = './data/spotify/spotify_playcount.json'
    spotify_playcount_error_path = './data/spotify/spotify_playcount_error.json'
    # Revisamos si existe el archivo con los contadores de reproducción,
    # en caso de que no exista se crea un diccionario vacio
    if os.path.exists(spotify_playcount_path):
        with open(spotify_playcount_path, "r") as f:
            spotify_playcount = json.load(f)
    else:
        spotify_playcount = {}    
    
    # Revisamos si existe el archivo con los errores,
    # en caso de que no exista se crea un diccionario vacio
    if os.path.exists(spotify_playcount_error_path):
        with open(spotify_playcount_error_path, "r") as f:
            spotify_playcount_error = json.load(f)
    else:
        spotify_playcount_error = {} 
    
    
    # Obtenemos los ids de tracks a scrapear
    spotify_track_ids = spotify_data['spotify_track_id'][spotify_data['spotify_track_id'].notna()].tolist()
    
    # Creamos las instancias de selenium necesarias
    options = webdriver.ChromeOptions()
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    count = 0
    for spotify_track_id in spotify_track_ids:
        # Si el spotify_track_id no existe en el diccionario, scrapeamos y guardamos el resultado
        if not (spotify_track_id in spotify_playcount) and not (spotify_track_id in spotify_playcount_error):        
            if count < 100:
                count +=1
                # Generamos la URL
                track_url = get_track_url(spotify_track_id)     
                try:
                    # Cargamos la pagina de la canción
                    driver.get(track_url)
    
                    # Esperamos a que el contador este presente
                    playcount_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, 'span[data-testid="playcount"]')
                        )
                    )
    
                    # Extraemos el HTML completo
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    # Extraemos el contador con beutiful soup
                    span = soup.find("span", {"data-testid": "playcount"})
                    playcount = int(span.text.replace(",", "")) if span else None
    
                    if playcount > 0:
                        spotify_playcount[spotify_track_id] = playcount
                        # Luego de scrapear exitosamente guardamos el diccionario actualizado              
                        with open(spotify_playcount_path, "w") as f:
                            json.dump(spotify_playcount, f)
                        print(spotify_track_id, playcount)
    
                    # Polite delay
                    time.sleep(1.2) 
                except TimeoutException:
                    spotify_playcount_error[spotify_track_id] = 'error'
                    with open(spotify_playcount_error_path, "w") as f:
                            json.dump(spotify_playcount_error, f)
                    print(f'Error extrayendo el contador para key: {spotify_track_id}')
            else :
                break           
            
    driver.quit()
