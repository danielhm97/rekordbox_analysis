import streamlit as st
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import os
## Plotly library and functions

import plotly.express as px
import plotly.offline as pyo
import plotly.figure_factory as ff
from plotly import tools
from plotly.subplots import make_subplots
from plotly.offline import iplot
import plotly.graph_objects as go



# Carga y tratamiento de datos
@st.cache_data
def load_data_master():

    # Get the directory of the current script
    BASE_DIR = Path(os.getcwd()).resolve()
    print('THIS IS THE BASE DIR PATH')
    print(BASE_DIR)
    # Build absolute paths for streamlite
    master_collection_path = BASE_DIR / "data/master/master_collection.csv"
    master_history_path = BASE_DIR / "data/master/master_history.csv"

    # Optional: check paths
    print("Collection file exists:", master_collection_path.exists())
    print("History file exists:", master_history_path.exists())
    
    #master_collection_path = '../data/master/master_collection.csv'
    #master_history_path = '../data/master/master_history.csv'
    master_collection_df = pd.read_csv(master_collection_path, sep=',',encoding='utf-8')
    master_history_df = pd.read_csv(master_history_path, sep=',',encoding='utf-8')

    master_collection_df['rb_genre_to_graph'] = master_collection_df['rb_genre']
    master_collection_df['rb_genre_to_graph'] = master_collection_df['rb_genre_to_graph'].fillna('Sin Genero')

    master_history_df['rb_genre_to_graph'] = master_history_df['rb_genre']
    master_history_df['rb_genre_to_graph'] = master_history_df['rb_genre_to_graph'].fillna('Sin Genero')
    
    master_collection_df['rb_date_added_year_month'] = pd.to_datetime(master_collection_df['rb_date_added']).dt.to_period('M').astype(str)

    if master_collection_df['rb_genre_to_graph'].value_counts(dropna=False).shape[0] > 4:
        # Nos quedamos con el top 4
        top_4_genres = master_collection_df['rb_genre_to_graph'].value_counts().to_frame().reset_index().head(4)
        top_4_genres = top_4_genres['rb_genre_to_graph'].tolist()
        master_collection_df['rb_genre_to_graph'] = master_collection_df['rb_genre_to_graph'].where(master_collection_df['rb_genre'].isin(top_4_genres), 'Otros')

    return master_collection_df,master_history_df

# df para metricas de sets
def sets_metrics_df(history_df):
    sets_metrics = history_df.copy()
    sets_metrics['rbh_year'] = sets_metrics['rbh_created_date'].str[:4]

    
    sets_metrics = (sets_metrics.groupby(['rbh_set_name', 'rbh_set_number','rbh_year','rbh_created_date'], as_index=False)
                  .agg(avg_bpm=('rb_average_bpm','mean'),
                       set_duration = ('rb_duration_sec','sum'))
                  )
    
    sets_metrics['avg_bpm'] = sets_metrics['avg_bpm'].astype(int) 
    sets_metrics['set_duration'] = round(sets_metrics['set_duration']/60,2)
    sets_metrics['rbh_set_number'] = sets_metrics['rbh_set_number'] +1

    sets_metrics.columns = ['Nombre DJ Set', 'DJ Set','Año del DJ Set','Fecha del DJ Set','BPMs promedio','Duracion (min)']

    return sets_metrics

# Serie de tiempo, coleccion
def collection_time_serie(collection_df):
    total_collection = None

    if collection_df['rb_genre_to_graph'].value_counts(dropna=False).shape[0] >= 2:
        # Preparamos el contador total
        total_collection = (collection_df.groupby('rb_date_added_year_month')
                                         .size()
                                         .reset_index(name='monthly_count'))
        total_collection['cumulative_count'] = total_collection['monthly_count'].cumsum()
        total_collection['rb_genre_to_graph'] = 'Total'
    
    # Preparamos el contador por genero
    tracks_by_genre = (collection_df.groupby(['rb_date_added_year_month', 'rb_genre_to_graph'])
                                   .size()
                                   .reset_index(name='monthly_count'))
    tracks_by_genre['cumulative_count'] = tracks_by_genre.groupby('rb_genre_to_graph')['monthly_count'].cumsum()    

    if total_collection is not None:
        all_tracks = pd.concat([tracks_by_genre, total_collection], ignore_index=True)
    else:
        all_tracks = tracks_by_genre
    all_tracks.columns = ['Añadido el', 'Genero', 'monthly_count','Cantidad de tracks']    
    # Count frequencies
    freq = all_tracks.groupby('Genero')['monthly_count'].sum('monthly_count')
    # Separate 'Otros'
    if 'Otros' in list(freq.index):
        otros_count = freq.pop('Otros')
    else:
        otros_count = 0
    # Separate 'Total'
    if 'Total' in list(freq.index):
        total_count = freq.pop('Total')
    else:
        total_count = 0
    sorted_order = list(freq.index)
    if total_count != 0:
        # Agregamos 'Total' en 1era posición
        sorted_order = ['Total'] + sorted_order
    if otros_count != 0:
        # Agregamos 'Otros' en 1era posición
        sorted_order = sorted_order + ['Otros']
    # Transformamos la columna a una categorica
    all_tracks['Genero'] = pd.Categorical(all_tracks['Genero'], categories=sorted_order, ordered=True)
    all_tracks['Añadido el'] = all_tracks['Añadido el'].astype(str)
    all_tracks = all_tracks.sort_values('Añadido el', ascending=True).reset_index(drop=True)

    # Graficamos
    collection_time_serie = px.line(
        all_tracks,
        x='Añadido el',
        y='Cantidad de tracks',
        color='Genero',
        title='Crecimiento total de la colección y top 4 géneros',
        markers=True,
        category_orders={'Genero': sorted_order} 
    )
    if total_count >0 :
        # Optional: make Total line stand out
        collection_time_serie.update_traces(selector=dict(name='Total'), line=dict(width=4, dash='dash'),visible='legendonly')
    
    # Axis styling
    collection_time_serie.update_layout(
        xaxis=dict(title=dict(text='Mes - Año',font=dict(color='black', size=16)), tickfont=dict(color='black')),
        yaxis=dict(title=dict(text='Total de Tracks',font=dict(color='black', size=16)), tickfont=dict(color='black'),showgrid=True, gridcolor='lightgray',dtick=100),
        title=dict(font=dict(color='black', size=22),x=0.5,xanchor = 'center'),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return st.plotly_chart(collection_time_serie, use_container_width=True)

# Barras tipo de archivo
def file_type_bar(filtered_df):
    rb_file_type = filtered_df
    rb_file_type = filtered_df['rb_file_type'].value_counts().to_frame().reset_index()
    # Elegimos color y opacidad
    fill_color = '#1f77b4'
    fill_opacity = 0.9
    line_color = '#0d2a4a'
    # Creamos el grafico de barras
    file_type_bar = px.bar(
            rb_file_type,
            x='rb_file_type',
            y='count',
            labels={'rb_file_type': 'Formato del Track', 'count': 'Número de Tracks'},
            title='Tracks por formato'
            )
    file_type_bar.update_traces(
    marker_line_color='black',  # border color
    marker_line_width=0.5,        # border width
    marker_color=fill_color,    # fill color
    opacity=fill_opacity,
    text=rb_file_type['count'],               # show values
    textposition='outside',
    textfont=dict(
        color='black'
    )
    )
    #Agregamos espacio en el eje Y
    max_count = rb_file_type['count'].max()
    file_type_bar.update_yaxes(
        range=[0, max_count * 1.10]  # add 15% padding above the tallest bar
    )
    # Personalizamos el texto del grafico
    file_type_bar.update_layout(
        paper_bgcolor='white',  # background outside the plot
        plot_bgcolor='white',
        title=dict(
            font=dict(color='black', size=22),x=0.5,xanchor = 'center'
        ),
        xaxis=dict(
            title=dict(font=dict(color='black', size=16)),
            tickfont=dict(color='black')
        ),
        yaxis=dict(
            title=dict(font=dict(color='black', size=16)),
            tickfont=dict(color='black')
        ))
    
    return st.plotly_chart(file_type_bar, use_container_width=True)

# Histograma BPMs
def bpm_hist(filtered_df,collection_df):
    # Elegimos color y opacidad
    fill_color = '#1f77b4'
    fill_opacity = 0.9
    line_color = '#0d2a4a'
    # Creamos el histograma
    bpm_df = filtered_df
    bpm_df['bpm_bin'] = bpm_df['rb_average_bpm'].round(0)
    bpm_hist = px.histogram(
    bpm_df,
    x='bpm_bin',
    nbins=50,
    labels={
        'rb_average_bpm': 'BPM' # Change the y-axis label
    },
    title='Histograma de los BPM'
    )
    # Personalizamos el texto del grafico
    bpm_hist.update_layout(
    paper_bgcolor='white',  # background outside the plot
    plot_bgcolor='white',    
    title=dict(
        text='Histograma de los BPM',
        font=dict(color='black', size=22), x=0.5, xanchor = 'center'
    ),
    xaxis=dict(
        title=dict(text='BPM', font=dict(color='black', size=16)),
        tickfont=dict(color='black')
    ),
    yaxis=dict(
        title=dict(text='Frecuencia', font=dict(color='black', size=16)),
        tickfont=dict(color='black')
    ))

    # Personalizamos el grafico
    bpm_hist.update_traces(
    marker_line_color='black',  # border color
    marker_line_width=0.5,        # border width
    marker_color=fill_color,    # fill color
    opacity=fill_opacity,
    hovertemplate="BPMs: %{x}<br>Frecuencia: %{y}<extra></extra>"
    )
    mean_bpm = round(collection_df['rb_average_bpm'].mean(),1)
    bpm_hist.add_vline(
        x=mean_bpm,
        line_width=2,
        line_dash="dash",
        line_color=line_color,
        annotation_text=f"Promedio Colección: {mean_bpm}",
        annotation_position="top"
    )

    return st.plotly_chart(bpm_hist, use_container_width=True)

# Duracion Top 4 generos
def collection_duration_boxplot(collection_df):
    
    duration_box_df = collection_df[collection_df['rb_genre_to_graph']!='Otros'].copy()

    genre_counts_box = duration_box_df['rb_genre_to_graph'].value_counts()

    genre_order_box = genre_counts_box.index.tolist()

    genre_labels_box = [f"{g} ({genre_counts_box[g]})" for g in genre_order_box]

    label_map = dict(zip(genre_order_box, genre_labels_box))
    duration_box_df['rb_genre_to_graph'] = duration_box_df['rb_genre_to_graph'].map(label_map)

    duration_box = px.box(
        duration_box_df,
        x='rb_genre_to_graph',
        y='rb_duration_sec',
        color='rb_genre_to_graph',
        points='all',
        labels={
            'rb_duration_sec': 'Duración (segundos)',
            'rb_genre_to_graph': 'Género'
        },
        category_orders={'rb_genre_to_graph': genre_labels_box}
    )

    duration_box.update_layout(
        title=dict(
            text="Duración Tracks, Top 4 géneros",
            font=dict(size=22, color='black'),
            x=0.5,
            xanchor='center'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        yaxis=dict(
            title=dict(text='Duración (segundos)',font=dict(color='black', size=16)),
            tickfont=dict(color='black')
        ),
        xaxis=dict(
            title=None,
            tickfont=dict(color='black')
        )
    )

    return st.plotly_chart(duration_box, use_container_width=True)

# Rueda de camelot
def camelot_wheel(collection_df):
    camelot_numbers = [str(i) for i in range(1, 13)]

    camelot_df = (
        collection_df
        .dropna(subset=['rb_tonality'])
        .assign(
            number=lambda d: d['rb_tonality'].str[:-1],
            mode=lambda d: d['rb_tonality'].str[-1]
        )
        .query("number in @camelot_numbers and mode in ['A','B']")
        .groupby(['number', 'mode'])
        .size()
        .reset_index(name='count')
    )

    camelot_df['number'] = camelot_df['number'].astype(int)
    camelot_df['r'] = camelot_df['mode'].map({'A': 15, 'B': 10})
    camelot_df['tonality'] = camelot_df['number'].astype(str)+ camelot_df['mode']
    camelot_df = camelot_df.sort_values(by=['number','mode'],ascending=[True,True])
    camelot_df['number'] = camelot_df['number'].astype(str)

    camelot_df['perc'] = round(camelot_df['count']*100/camelot_df['count'].sum(),2)
    camelot_df['perc'] = camelot_df['perc'].astype(str) + '%'


    def map_to_colors(values, colorscale):
        """Map a list of values to a colorscale"""
        norm = (values - np.min(values)) / (np.max(values) - np.min(values) + 1e-9)
        idx = (norm * (len(colorscale)-1)).astype(int)
        return [colorscale[i] for i in idx]

    # Dividir A y B
    df_A = camelot_df[camelot_df['mode'] == 'A']
    df_B = camelot_df[camelot_df['mode'] == 'B']

    colors_A = map_to_colors(df_A['count'].values, px.colors.sequential.Oranges)
    colors_B = map_to_colors(df_B['count'].values, px.colors.sequential.Blues)

    # Crear figura
    camelot_fig = go.Figure()

    # Anillo interno = Menor (A)
    camelot_fig.add_trace(go.Pie(
        labels=df_A['tonality'], 
        values=df_A['r'],
        name='Menor (A)',
        hole=0,                     # radio interno
        marker=dict(colors = colors_A, line=dict(color='black', width=1)),
        texttemplate=df_A['tonality']+ "<br>(" + df_A['count'].astype(str) + ")",
        textposition='inside',
        sort=False,                   # mantener orden Camelot
        direction='clockwise',
        hovertemplate=('Porcentaje sobre el total: '+df_A['perc']+'<br>'+
                       'Tonalidad o Key: '+df_A['tonality']+'<br>'+
                       'Tracks: '+df_A['count'].astype(str)+'<br><extra></extra>'),
        domain={'x':[0.2,0.8], 'y':[0.2,0.8]}  # mantener centrado
    ))

    # Anillo externo = Mayor (B)
    camelot_fig.add_trace(go.Pie(
        labels=df_B['tonality'], 
        values=df_B['r'], 
        name='Mayor (B)',
        hole=0.6,                     # radio interno más grande para anillo externo
        marker=dict(colors = colors_B, line=dict(color='black', width=1)),
        texttemplate=df_B['tonality']+ "<br>(" + df_B['count'].astype(str) + ")",
        textposition='inside',
        sort=False,
        direction='clockwise',
        hovertemplate=('Porcentaje sobre el total: '+df_B['perc']+'<br>'+
                       'Tonalidad o Key: '+df_B['tonality']+'<br>'+
                       'Tracks: '+df_B['count'].astype(str)+'<br><extra></extra>')
    ))

    # Layout
    camelot_fig.update_layout(
        paper_bgcolor='white',  # background outside the plot
        plot_bgcolor='white',
        title=dict(
            text="Distribución armónica – Camelot Wheel",
            font=dict(size=22, color='black'),
            x=0.5,
            xanchor = 'center'
        ),
        showlegend=False
    )

    return st.plotly_chart(camelot_fig, use_container_width=True)

# Histograma de similitud
def sim_hist(filtered_df_2,collection_df_spotify):
    # Elegimos color y opacidad
    fill_color = '#1f77b4'
    fill_opacity = 0.9
    line_color = '#0d2a4a'

    sim_hist = px.histogram(
    filtered_df_2,
    x='similarity',
    nbins=30,
    labels={
        'similarity': 'Similitud' # Change the y-axis label
    },
    title='Histograma de Similitud'
    )
    # Personalizamos el texto del grafico
    sim_hist.update_layout(
    paper_bgcolor='white',  # background outside the plot
    plot_bgcolor='white',    
        title=dict(
        text='Histograma, indice de similitud',
        font=dict(color='black', size=22),x=0.5,xanchor = 'center'
    ),
    xaxis=dict(
        title=dict(text='Similitud', font=dict(color='black', size=16)),
        tickfont=dict(color='black')
    ),
    yaxis=dict(
        title=dict(text='Frecuencia', font=dict(color='black', size=16)),
        tickfont=dict(color='black')
    ))
    # Personalizamos el grafico
    sim_hist.update_traces(
    marker_line_color='black',  # border color
    marker_line_width=0.5,        # border width
    marker_color=fill_color,    # fill color
    opacity=fill_opacity,
    hovertemplate="Similitud: %{x}<br>Frecuencia: %{y}<extra></extra>"
    )
    mean_sim = round(collection_df_spotify['similarity'].mean(),1)
    sim_hist.add_vline(
        x=mean_sim,
        line_width=2,
        line_dash="dash",
        line_color=line_color,
        annotation_text=f"Promedio Colección: {mean_sim}",
        annotation_position="top"
    )

    return st.plotly_chart(sim_hist, use_container_width=True)

# Histograma de popularidad
def pop_hist(filtered_df_2,collection_df_spotify):
    # Elegimos color y opacidad
    fill_color = '#1f77b4'
    fill_opacity = 0.9
    line_color = '#0d2a4a'

    pop_hist = px.histogram(
    filtered_df_2,
    x='spotify_popularity',
    nbins=30,
    labels={
        'spotify_popularity': 'Popularidad' # Change the y-axis label
    }
    )
    # Personalizamos el texto del grafico
    pop_hist.update_layout(
        paper_bgcolor='white',  # background outside the plot
        plot_bgcolor='white',
        title=dict(
        text='Histograma, indice de popularidad Spotify',
        font=dict(color='black', size=22),x=0.5,xanchor = 'center'
    ),
    xaxis=dict(
        title=dict(text='Popularidad', font=dict(color='black', size=16)),
        tickfont=dict(color='black')
    ),
    yaxis=dict(
        title=dict(text='Frecuencia', font=dict(color='black', size=16)),
        tickfont=dict(color='black')
    ))
    # Personalizamos el grafico
    pop_hist.update_traces(
        marker_line_color='black',  # border color
        marker_line_width=0.5,        # border width
        marker_color=fill_color,    # fill color
        opacity=fill_opacity,
        hovertemplate="Popularidad: %{x}<br>Frecuencia: %{y}<extra></extra>"
    )
    mean_pop = round(collection_df_spotify['spotify_popularity'].mean(),1)

    pop_hist.add_vline(
        x=mean_pop,
        line_width=2,
        line_dash="dash",
        line_color=line_color,
        annotation_text=f"Promedio Colección: {mean_pop}",
        annotation_position="top"
    )
    return st.plotly_chart(pop_hist, use_container_width=True)

# top_5_spotify
def top_5_spotify(filtered_df_2):
    def similarity_row_style(row):
        if row['Similitud'] > 0.95:
            color = 'background-color: rgb(80, 200, 120)'
        elif row['Similitud'] > 0.85:
            color = 'background-color: rgb(170, 220, 150)'
        elif row['Similitud'] > 0.7:
            color = 'background-color: rgb(240, 220, 120)'
        else:
            color = 'background-color: rgb(220, 120, 120)'
        return [color] * len(row)


    top5 = filtered_df_2.sort_values('spotify_playcount',ascending=False).head(5).reset_index(drop=True)
    top5 = top5[['spotify_artists','spotify_name','spotify_playcount','rb_genre_filter','similarity']]
    top5['spotify_playcount'] = top5['spotify_playcount'].astype(int)
    top5.columns = ['Artista(s)', 'Track', 'Reproducciones','Genero', 'Similitud']

    top5 = (
        top5
        .style
        .format({'Similitud': '{:.2f}','Reproducciones': lambda x: f"{x:,}".replace(",", ".")})
        .apply(similarity_row_style, axis=1)
        .set_properties(**{'color': 'black'})
    )
    return st.dataframe(top5, hide_index=True, use_container_width=True)

# Grafico de barras vertical para tracks, por año de lanzamiento
def year_release_bar(filtered_df_2):
    year_release_spotify = filtered_df_2['spotify_release_date'].str[:4].value_counts()
    year_release_spotify = year_release_spotify.reset_index(name='Tracks')
    year_release_spotify = year_release_spotify.sort_values('spotify_release_date', ascending=True).reset_index(drop=True)
    year_release_spotify['Porcentaje'] = (year_release_spotify['Tracks']*100/year_release_spotify['Tracks'].sum()).round(2)
    year_release_spotify['Porcentaje'] = year_release_spotify['Porcentaje'].astype(str) + '%'
    year_release_spotify.rename(columns={"spotify_release_date": "Año"}, inplace=True)
    year_release_spotify['Año'] = pd.Categorical(
        year_release_spotify['Año'],
        categories=sorted(year_release_spotify['Año']),
        ordered=True
    )

    # Elegimos color y opacidad
    fill_color = '#1f77b4'
    fill_opacity = 0.9
    line_color = '#0d2a4a'

    year_release_bar = px.bar(
        year_release_spotify,
        y="Año",
        x="Tracks",
        text="Tracks",
        title="Tracks por Año de lanzamiento",
        orientation='h',
        color_discrete_sequence=[fill_color],
        hover_data={
            "Año": False,
            "Tracks": False,
            "Porcentaje": True
        }
    )

    year_release_bar.update_layout(
        paper_bgcolor='white',  # background outside the plot
        plot_bgcolor='white',
        title=dict(font=dict(color='black', size=22),x=0.5,xanchor = 'center'),
        xaxis=dict(
            title=None,
            tickfont=dict(color='black'),
            showgrid=True,         # enable horizontal grid lines
            gridcolor='lightgrey', # grid line color
            gridwidth=1
        ),
        yaxis=dict(
            title=dict(text='Año', font=dict(color='black', size=16)),
            tickfont=dict(color='black')
        )

    )

    year_release_bar.update_traces(
        textposition='outside',
        marker=dict(line=dict(color=line_color, width=1), opacity=fill_opacity)
    )

    year_release_bar.update_yaxes(
        tickmode='array',
        tickvals=year_release_spotify['Año'],
        ticktext=year_release_spotify['Año']
    )

    return st.plotly_chart(year_release_bar, use_container_width=True)

# Bolas sets por año
def sets_per_year(sets_per_year):
    # Elegimos color y opacidad
    fill_color = '#1f77b4'
    line_color = '#0d2a4a'
    
    data = [go.Scatter(x = sets_per_year['Año del DJ Set'],
                       y = sets_per_year['DJ Sets'],
                       mode = 'markers+text',
                       text = sets_per_year['DJ Sets'],
                       hoverinfo='skip',
                       textfont=dict(color='black', size=15),
                       marker = dict(size = sets_per_year['DJ Sets'] * 8,
                                     color = fill_color,
                                     showscale = False,
                                     opacity = 0.5,
                                     line = dict(color = line_color,
                                                 width = 0.5)))]
    
    layout = go.Layout(title=dict(
                           text='DJ Sets realizados por año',
                           font=dict(color='black', size=22), x=0.5, xanchor = 'center'
                       ),
                        paper_bgcolor='white',  # background outside the plot
                        plot_bgcolor='white',                      
                       xaxis = dict(title = None,showgrid = False,
                                    tickfont=dict(color='black')),
                       yaxis = dict(title =dict(text ='DJ Sets por año',font=dict(color='black')),
                                    tickfont=dict(color='black')),
                       template ='plotly_white')
    
    sets_per_year_balls = go.Figure(data = data, layout = layout)
    return st.plotly_chart(sets_per_year_balls, use_container_width=True)

# Histograma BPMs DJ Set
def bpm_hist_sets(sets_metrics):
    # Elegimos color y opacidad
    fill_color = '#1f77b4'
    fill_opacity = 0.9
    line_color = '#0d2a4a'
    # Creamos el histograma
    bpm_df = sets_metrics
    
    bpm_hist = px.histogram(
    bpm_df,
    x='BPMs promedio',
    nbins=50
    )
    # Personalizamos el texto del grafico
    bpm_hist.update_layout(
    paper_bgcolor='white',  # background outside the plot
    plot_bgcolor='white',    
    title=dict(
        text='BPMs promedio en tus DJ Sets',
        font=dict(color='black', size=22), x=0.5, xanchor = 'center'
    ),
    xaxis=dict(
        title=dict(text=None),
        tickfont=dict(color='black')
    ),
    yaxis=dict(
        title=dict(text='Frecuencia', font=dict(color='black', size=16)),
        tickfont=dict(color='black')
    ))

    # Personalizamos el grafico
    bpm_hist.update_traces(
    marker_line_color='black',  # border color
    marker_line_width=0.5,        # border width
    marker_color=fill_color,    # fill color
    opacity=fill_opacity,
    hovertemplate="BPMs: %{x}<br>Frecuencia: %{y}<extra></extra>"
    )
    mean_bpm = round(sets_metrics['BPMs promedio'].mean(),1)
    bpm_hist.add_vline(
        x=mean_bpm,
        line_width=2,
        line_dash="dash",
        line_color=line_color,
        annotation_text=f"Promedio total BPMs: {mean_bpm}",
        annotation_position="top"
    )
    return st.plotly_chart(bpm_hist, use_container_width=True)

# Histograma Duración DJ Set
def duration_hist_sets(sets_metrics):
    # Elegimos color y opacidad
    fill_color = '#1f77b4'
    fill_opacity = 0.9
    line_color = '#0d2a4a'
    # Creamos el histograma
    bpm_df = sets_metrics
    
    duration_hist = px.histogram(
    bpm_df,
    x='Duracion (min)',
    nbins=50
    )
    # Personalizamos el texto del grafico
    duration_hist.update_layout(
    paper_bgcolor='white',  # background outside the plot
    plot_bgcolor='white',    
    title=dict(
        text='Duración promedio en tus DJ Sets (min)',
        font=dict(color='black', size=22), x=0.5, xanchor = 'center'
    ),
    xaxis=dict(
        title=dict(text=None),
        tickfont=dict(color='black')
    ),
    yaxis=dict(
        title=dict(text='Frecuencia', font=dict(color='black', size=16)),
        tickfont=dict(color='black')
    ))

    # Personalizamos el grafico
    duration_hist.update_traces(
    marker_line_color='black',  # border color
    marker_line_width=0.5,        # border width
    marker_color=fill_color,    # fill color
    opacity=fill_opacity,
    hovertemplate="Duración: %{x}<br>Frecuencia: %{y}<extra></extra>"
    )
    mean_bpm = round(sets_metrics['Duracion (min)'].mean(),1)
    duration_hist.add_vline(
        x=mean_bpm,
        line_width=2,
        line_dash="dash",
        line_color=line_color,
        annotation_text=f"Promedio DJ sets: {mean_bpm} min",
        annotation_position="top"
    )
    
    return st.plotly_chart(duration_hist, use_container_width=True)

# df top 5 tracks mas usados en el historial
def top_5_tracks_history(history_df):
    top5_tracks = history_df.groupby(['rb_track_id','rb_artists','rb_track_name','rb_genre_to_graph'],as_index=False).size()
    top5_tracks = top5_tracks.drop('rb_track_id', axis=1)
    top5_tracks = top5_tracks.sort_values('size', ascending=False).reset_index(drop=True)
    top5_tracks = top5_tracks.head(5)
    top5_tracks.columns = ['Artista(s)','Track','Género','Reproducciones']
    top5_tracks = top5_tracks.style
    return st.dataframe(top5_tracks, hide_index=True, use_container_width=True)