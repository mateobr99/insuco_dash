import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import geopandas as gpd
import os

# Configuración de la página
st.set_page_config(layout='wide', page_title="Portal de Indicadores")
st.title("Portal de Indicadores Sociodemográficos - Eje Cafetero")

# Ruta a la carpeta de datos
DATA_DIR = "datos"

@st.cache_data
def cargar_datos():
    try:
        # Construir ruta completa al archivo Excel
        excel_path = os.path.join(DATA_DIR, "BD_FINAL_20250617.xlsx")
        
        # Verificar si el archivo existe
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"No se encontró el archivo Excel en: {excel_path}")
        
        df = pd.read_excel(excel_path, sheet_name="3 Resultados")
        
        # Limpieza y conversión de tipos
        df['Subregion'] = df['Subregion'].astype(str).str.strip().replace('nan', np.nan)
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
        df['Año'] = pd.to_numeric(df['Año'], errors='coerce')
        df['Municipio'] = df['Municipio'].astype(str).str.strip().str.title()  # Convertir a formato título
        
        # --- MODIFICACIÓN: Corrección del nombre "Belén de Umbría" ---
        # Asegura que el nombre coincida con el del archivo geográfico
        correcciones = {
            'Belén De Umbría': 'Belén de Umbría',
        }
        df['Municipio'] = df['Municipio'].replace(correcciones)
        
        # Filtrar solo datos del Eje Cafetero
        departamentos_eje = ['CALDAS', 'QUINDIO', 'RISARALDA']  # Incluye acento en Quindío
        df = df[df['Departamento'].str.upper().isin(departamentos_eje)]
        
        return df.dropna(subset=['Valor', 'Año'])
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        st.stop()

@st.cache_data
def cargar_geodata():
    """Carga datos geográficos del Eje Cafetero conservando formato original"""
    try:
        geojson_path = os.path.join(DATA_DIR, "EjeCafetero.json")
        
        if not os.path.exists(geojson_path):
            raise FileNotFoundError(f"No se encontró el archivo GeoJSON en: {geojson_path}")
        
        # Cargar desde archivo local conservando caracteres originales
        eje_cafetero = gpd.read_file(geojson_path)
        
        # Normalizar nombres a formato tipo oración (conservando acentos)
        if 'MPIO_CNMBR' in eje_cafetero.columns:
            eje_cafetero['MPIO_CNMBR'] = eje_cafetero['MPIO_CNMBR'].str.title()
        
        if 'NOMBRE_DPT' in eje_cafetero.columns:
            eje_cafetero['NOMBRE_DPT'] = eje_cafetero['NOMBRE_DPT'].str.title()
        
        # Correcciones especiales de nombres
        correcciones = {
            'Anserma': 'Anserma',
            'Belén De Umbría': 'Belén de Umbría',
            'Quinchía': 'Quinchía',
            'Pueblo Rico': 'Pueblo Rico',
            'Santuario': 'Santuario'
        }
        
        if 'MPIO_CNMBR' in eje_cafetero.columns:
            eje_cafetero['MPIO_CNMBR'] = eje_cafetero['MPIO_CNMBR'].replace(correcciones)
        
        return eje_cafetero
    except Exception as e:
        st.error(f"Error cargando datos geográficos: {str(e)}")
        return None

# Cargar los datos
df = cargar_datos()
geo_data = cargar_geodata()

st.sidebar.header("Filtros")

# 1. Filtro de Dimensión
dimension = st.sidebar.selectbox(
    "Dimensión",
    options=sorted(df['Dimension'].unique())
)
df_filtrado = df[df['Dimension'] == dimension].copy()

# Verificar si la dimensión tiene datos geográficos
tiene_datos_municipales = not df_filtrado['Municipio'].dropna().empty
tiene_datos_subregion = not df_filtrado['Subregion'].dropna().empty

# 2. Filtro de Departamento
departamento = st.sidebar.selectbox(
    "Departamento",
    options=sorted(df_filtrado['Departamento'].dropna().unique())
)
df_filtrado = df_filtrado[df_filtrado['Departamento'] == departamento]

# 3. Filtros condicionales de Subregión y Municipio
if tiene_datos_subregion:
    subregion = st.sidebar.selectbox(
        "Subregión",
        options=sorted(df_filtrado['Subregion'].dropna().unique())
    )
    df_filtrado = df_filtrado[df_filtrado['Subregion'] == subregion]
else:
    subregion = None
    st.sidebar.info("Dimensión sin datos de subregión")

if tiene_datos_municipales:
    municipios_opciones = sorted(df_filtrado['Municipio'].dropna().unique())
    municipio = st.sidebar.selectbox(
        "Municipio",
        options=municipios_opciones
    )
    df_filtrado = df_filtrado[df_filtrado['Municipio'] == municipio]
else:
    municipio = None
    st.sidebar.info("Dimensión sin datos municipales")

# 4. Filtro de Variable
variable = st.sidebar.selectbox(
    "Variable",
    options=sorted(df_filtrado['Variable'].dropna().unique())
)
df_filtrado = df_filtrado[df_filtrado['Variable'] == variable]

# 5. Filtro de Análisis
analisis_opciones = sorted(df_filtrado['Analisis'].dropna().unique()) if 'Analisis' in df_filtrado.columns else ["Total"]
analisis = st.sidebar.selectbox(
    "Análisis",
    options=analisis_opciones,
    key="analisis_select"
)
df_filtrado = df_filtrado[df_filtrado['Analisis'] == analisis] if 'Analisis' in df_filtrado.columns else df_filtrado

# 6. Filtro de Desagregación
desagregacion_opciones = sorted(df_filtrado['Desagregacion'].dropna().unique()) if 'Desagregacion' in df_filtrado.columns else ["Total"]
desagregacion = st.sidebar.selectbox(
    "Desagregación",
    options=desagregacion_opciones,
    key="desagregacion_select"
)
df_filtrado = df_filtrado[df_filtrado['Desagregacion'] == desagregacion] if 'Desagregacion' in df_filtrado.columns else df_filtrado

# --------------------------------------------------
# Visualización principal
# --------------------------------------------------
if not df_filtrado.empty:
    # Título dinámico
    titulo = f"{variable} - {departamento}"
    if subregion:
        titulo += f" ({subregion})"
    if municipio:
        titulo += f", {municipio}"
    st.subheader(titulo)
    
    # Mostrar metadatos
    metadata = []
    if 'Analisis' in df_filtrado.columns:
        metadata.append(f"Análisis: {analisis}")
    if 'Desagregacion' in df_filtrado.columns:
        metadata.append(f"Desagregación: {desagregacion}")
    if metadata:
        st.caption(" | ".join(metadata))
    
    # Gráfico de evolución temporal
    fig = px.line(
        df_filtrado.sort_values('Año'),
        x='Año',
        y='Valor',
        title=f"Evolución de {variable}",
        markers=True,
        height=500
    )
    
    # Añadir línea vertical en el último año disponible
    ultimo_anio = df_filtrado['Año'].max()
    fig.add_vline(
        x=ultimo_anio, 
        line_dash="dash", 
        line_color="red",
        annotation_text="Último año disponible",
        annotation_position="top left"
    )
    
    fig.update_layout(
        xaxis_title='Año',
        yaxis_title='Valor',
        hovermode='x unified',
        showlegend=False
    )
    
    # Mostrar gráfico temporal
    st.plotly_chart(fig, use_container_width=True)
    
    # --------------------------------------------------
    # Sección de mapa geográfico del Eje Cafetero
    # --------------------------------------------------
    if geo_data is not None:
        try:
            # Preparar datos para el mapa
            df_map = df_filtrado.copy()
            df_map = df_map[df_map['Año'] == ultimo_anio]
            
            # Hacer el merge conservando todos los municipios
            geo_merged = geo_data.merge(
                df_map,
                left_on='MPIO_CNMBR',
                right_on='Municipio',
                how='left'
            )
            
            # Creamos un mapa base con todos los municipios en gris claro
            fig_mapa = px.choropleth(
                geo_merged,
                geojson=geo_merged.geometry,
                locations=geo_merged.index,
                color_discrete_sequence=['lightgrey'],
                hover_name='MPIO_CNMBR',
                hover_data={
                    'MPIO_CNMBR': False,
                },
                custom_data=['MPIO_CNMBR', 'Valor', 'Año'],
                projection="mercator",
                title=f"Distribución geográfica en el Eje Cafetero ({ultimo_anio})",
                scope='south america',
                height=600
            )
            
            if not df_map.empty and municipio:
                # Filtrar el geo-dataframe para el municipio seleccionado
                highlight_data = geo_merged[geo_merged['MPIO_CNMBR'] == municipio].copy()
            
                # Crear un segundo mapa solo para el municipio seleccionado con la escala 'Viridis'
                highlight_map = px.choropleth(
                    highlight_data,
                    geojson=highlight_data.geometry,
                    locations=highlight_data.index,
                    color='Valor',
                    hover_name='MPIO_CNMBR',
                    custom_data=['MPIO_CNMBR', 'Valor', 'Año'],
                    color_continuous_scale='Viridis',
                    projection="mercator",
                )
            
                # Añadir el mapa de realce como una traza al mapa base
                fig_mapa.add_trace(highlight_map.data[0])
            
            # Personalizar la apariencia del mapa
            fig_mapa.update_geos(
                visible=False,
                center=dict(lon=-75.5, lat=5.5),
                projection_scale=20,
                bgcolor='rgba(0,0,0,0)'
            )
            
            # Resaltar el municipio seleccionado con un borde
            if municipio:
                municipio_index = geo_merged[geo_merged['MPIO_CNMBR'] == municipio].index
                fig_mapa.add_trace(
                    px.choropleth(
                        geo_merged.loc[municipio_index],
                        geojson=geo_merged.loc[municipio_index].geometry,
                        locations=geo_merged.loc[municipio_index].index,
                        color_discrete_sequence=['rgba(0,0,0,0)'],
                        hover_name='MPIO_CNMBR'
                    ).data[0].update(
                        marker_line_width=3,
                        marker_line_color='red'
                    )
                )
            
            # Configurar la barra de color
            fig_mapa.update_layout(
                margin={"r":0,"t":60,"l":0,"b":0},
                coloraxis_colorbar=dict(
                    title="Valor",
                    thickness=20,
                    len=0.75
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                )
            )
            
            # Personalizar los tooltips
            fig_mapa.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br><br>" +
                              "Valor: %{customdata[1]:.2f}<br>" +
                              "Año: %{customdata[2]}<extra></extra>"
            )
            
            st.plotly_chart(fig_mapa, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error generando mapa: {str(e)}")
    
else:
    st.warning("No se encontraron datos con los filtros seleccionados")