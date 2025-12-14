# -*- coding: utf-8 -*-
"""
Plantilla Básica de Streamlit
Autor: Iñigo Asensio
Fecha: 2025
Descripción: Plantilla base para crear aplicaciones Streamlit
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plots import *


# Cargamos data antes de la cargar la app
collection_df, history_df = load_data_master()

#########################
## CONFIGURACIÓN DE PÁGINA
#########################
st.set_page_config(
    page_title="Rekordbox Analysis",
    page_icon="🎧",
    layout="wide",  # "centered" o "wide"
    initial_sidebar_state="expanded"
)

# Elegimos color y opacidad
fill_color = '#1f77b4'
fill_opacity = 0.9
line_color = '#0d2a4a'

#########################
## ESTILOS PERSONALIZADOS (OPCIONAL)
#########################
# st.markdown("""
#     <style>
#     .main {
#         background-color: #f5f5f5;
#     }
#     </style>
# """, unsafe_allow_html=True)

#########################
## SIDEBAR (MENÚ LATERAL)
#########################
with st.sidebar:
    st.title("🎧 Rekordbox")
    st.divider()

    # Selector de página/sección
    pagina = st.selectbox(
        "Selecciona una sección",
        ["🏠 Inicio", '💿 Colección',"🗓️ Historial"]
    )

    st.divider()
    st.caption("© 2025 - Daniel Huarita")

#########################
## CONTENIDO PRINCIPAL
#########################

# Título principal

#########################
## PÁGINA: INICIO
#########################
if pagina == "🏠 Inicio":
    st.header("🎧 Rekordbox Analysis")
    st.markdown("**Bienvenido**, identifica puntos de mejora como DJ, de la mano de los datos.")
    st.divider()

    # Contenido principal
    st.subheader("Bienvenido")
    st.write("""
    - Preparate para conocer tu colección de Track, y comprarlos con las metricas de spotify.
    - Tambien puedes conocer como han ido evolucionando tus DJ Sets a traves del tiempo.
    - Para este dashboard se utilizaron los datos de [Daniel Moll](https://www.instagram.com/_danielmoll), gracias por su colaboración.
    """)

#########################
## PÁGINA: COLECCION
#########################
elif pagina == "💿 Colección":

    tab_collection, tab_spotify = st.tabs([
        "💿 Colección",
        "🎧 Colección vs Spotify"
    ])

    with tab_collection:
        st.subheader('Conoce tu colección')
        st.caption('Conoce tu colección y mejora con ayuda de los datos')

        n_tracks_collection = collection_df.shape[0]
        n_genre_collection = collection_df['rb_genre'].dropna().unique().shape[0]
        total_duration = round(collection_df['rb_duration_sec'].sum()/3600,1)
        average_bpm = round(collection_df['rb_average_bpm'].mean())

        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric('🎵 Tracks', f'{n_tracks_collection}')
        with col2:
            st.metric('📚 Generos', f'{n_genre_collection}')
        with col3:
            st.metric('⌚ Duración total (hrs)', f'{total_duration}', help='Suma total de la duración de todos los tracks')
        with col4:
            st.metric('🥁 BPMs en promedio', f'{average_bpm}')

        st.divider()

        # Graficamos la serie de tiempo
        collection_time_serie(collection_df)

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            collection_duration_boxplot(collection_df)
        with col2:
            camelot_wheel(collection_df)    

        st.divider()    

        # --- Genre filter ---
        # Get unique genres and sort them
        collection_df['rb_genre_filter'] = collection_df['rb_genre'].fillna('Sin Genero')

        # Calculate frequencies
        genre_counts = collection_df['rb_genre_filter'].value_counts().sort_values(ascending=False)

        # Build options with counts
        genre_options = ([f'Todos ({collection_df['rb_genre_filter'].shape[0]})'] + 
                         [f"{genre} ({count})" for genre, count in genre_counts.items()])

        # Streamlit selectbox or multiselect
        selected_genre_w_count = st.selectbox("Filtrar por Género:", genre_options)

        # Filter dataframe based on selection
        if selected_genre_w_count != f'Todos ({collection_df['rb_genre_filter'].shape[0]})':
            selected_genre = selected_genre_w_count.split(' (')[0]
            filtered_df = collection_df[collection_df['rb_genre_filter'] == selected_genre]
        else:
            filtered_df = collection_df.copy()

        # Creamos 2 columnas
        col1, col2 = st.columns(2)

        with col1:
            file_type_bar(filtered_df)
        with col2:
            bpm_hist(filtered_df,collection_df)



    with tab_spotify:
        st.subheader("Comparativa con Spotify")
        st.caption("Comparación entre tu colección local y métricas de Spotify")
        st.caption("Solo se utilizaron los Tracks de tu colección que se pudieron encontrar en Spotify")

        n_tracks_spotify_2 = collection_df['spotify_track_id'].notna().sum()
        match_rate = round(collection_df['spotify_track_id'].notna().mean() * 100)
        avg_similarity = round(collection_df['similarity'].mean(),2)
        exact_duration_match_rate = round(collection_df['spotify_quality_result'].str.startswith('exact_duration_', na=False).sum()*100/collection_df.shape[0])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🎵 Tracks", f"{n_tracks_spotify_2}")
        col2.metric("✅ % Match", f"{match_rate}%")
        col3.metric("🔗 Similitud promedio", f"{avg_similarity:.2f}",help='La similitud indica en cuanto se asemejan, los tracks de tu colección y los tracks encontrados en spotify')
        col4.metric("⌚ Misma duración", f"{exact_duration_match_rate}%")

        st.divider()

        collection_df_spotify = collection_df[collection_df['spotify_track_id'].notna()].copy()
        # Calculate frequencies
        genre_counts_spotify = collection_df_spotify['rb_genre_filter'].value_counts().sort_values(ascending=False)

        # Build options with counts
        genre_options_spotify = ([f'Todos ({collection_df_spotify['rb_genre_filter'].shape[0]})'] + 
                                 [f"{genre} ({count})" for genre, count in genre_counts_spotify.items()])

        # Streamlit selectbox or multiselect
        selected_genre_w_count_2 = st.selectbox("Filtrar por Género: ", genre_options_spotify)


        # Filter dataframe based on selection
        if selected_genre_w_count_2 != f'Todos ({collection_df_spotify['rb_genre_filter'].shape[0]})':
            selected_genre_2 = selected_genre_w_count_2.split(' (')[0]
            filtered_df_2 = collection_df_spotify[(collection_df_spotify['rb_genre_filter'] == selected_genre_2)]
        else:
            filtered_df_2 = collection_df_spotify.copy()

        # Creamos 2 columnas
        col1, col2 = st.columns(2)

        with col1:
            sim_hist(filtered_df_2, collection_df_spotify)
            st.caption('Indice de similitud va entre (0-1), mientras mas cercano a 1 mejor',text_alignment='center')

        with col2:
            pop_hist(filtered_df_2, collection_df_spotify)
            st.caption('Indice de popularidad (0-100), mientras mas cercano a 100 más popular es un Track',text_alignment='center')

        st.divider()

        st.subheader("Top 5 Tracks, con más reproducciones en spotify.")
        # Graficamos la tabla con el top 5 de spotify
        top_5_spotify(filtered_df_2) 
        st.caption('Los colores de la tabla indican que tan confiables son los datos'+
                    ' obtenidos desde spotify basados en el indice de similitud.')
        
        st.divider()

        year_release_bar(filtered_df_2)

        st.caption('Porcentaje calculado en base al total de tracks, segun el filtro utilizado')

        

#########################
## PÁGINA: HISTORIAL
#########################
elif pagina == "🗓️ Historial":
    tab_history, tab_history_spotify = st.tabs([
        "🗓️ Historial de DJ Sets",
        "🎧 Historial vs Spotify"
    ])

    with tab_history:
        st.subheader('Conoce tu historial')
        st.caption('Identifica puntos de mejora, y llega al siguiente nivel')

        n_sets =history_df['rbh_set_number'].unique().shape[0]
        perc_collection = round(history_df['rbh_track_id'].unique().shape[0]*100/collection_df.shape[0])
        avg_duration_set = round((history_df['rb_duration_sec'].sum()/n_sets)/60)
        tracks_per_set = history_df.shape[0]//n_sets

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🎚️ DJ Sets", f"{n_sets}")
        col2.metric("🗃️ Uso de la colección", f"{perc_collection}%",help='Porcentaje de tracks que has utilizado de toda tu colección en tus DJ sets')
        col3.metric("⌚ Duracion promedio (min)", f"{avg_duration_set}",help='La similitud indica en cuanto se asemejan, los tracks de tu colección y los tracks encontrados en spotify')
        col4.metric("💿 Tracks por DJ set", f"{tracks_per_set}")

        st.divider()

        sets_metrics = sets_metrics_df(history_df)

        sets_per_year_df = sets_metrics['Año del DJ Set'].value_counts().reset_index(name='DJ Sets')
        sets_per_year_df = sets_per_year_df.sort_values('Año del DJ Set', ascending=True)



        # Graficamos cantidad de set por año
        sets_per_year(sets_per_year_df)

        st.divider()

        # Filtro por año
        # Calculate frequencies
        year_count = sets_metrics['Año del DJ Set'].value_counts().sort_values(ascending=False)
        # Build options with counts
        year_options = ([f'Todos ({sets_metrics['Año del DJ Set'].shape[0]})'] + 
                        [f"{year} ({count})" for year, count in year_count.items()])

        # Streamlit selectbox or multiselect
        selected_year_w_count = st.selectbox("Filtrar por Año:", year_options)

        # Filter dataframe based on selection
        if selected_year_w_count != f'Todos ({sets_metrics['Año del DJ Set'].shape[0]})':
            selected_year = selected_year_w_count.split(' (')[0]
            filtered_history_df = history_df[history_df['rbh_created_date'].str[:4] == selected_year]
        else:
            filtered_history_df = history_df.copy()

        sets_metrics_filtered = sets_metrics_df(filtered_history_df)

        # Graficamos historgamas de BPM y duración
        col1, col2, = st.columns(2)
        with col1:
            bpm_hist_sets(sets_metrics_filtered)
        with col2:
            duration_hist_sets(sets_metrics_filtered)   

        st.divider()
        st.subheader("Top 5 Tracks, más utilizados en tus DJ Sets")
        #Graficamos top 5 Tracks mas usados
        top_5_tracks_history(filtered_history_df)
        
    with tab_history_spotify:
        st.subheader('Explora tus sets con metricas de Spotify')
        st.caption('Estamos trabajando para ti, vuelve pronto..')


#########################
## PIE DE PÁGINA
#########################
st.divider()
st.caption("Desarrollado con ❤️ usando Streamlit | © 2025")
