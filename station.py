import streamlit as st
import pandas as pd
import googlemaps
from streamlit_js_eval import get_geolocation

# Configuración de página
st.set_page_config(page_title="Policía Cerca HN", page_icon="🚨", layout="centered")
st.title("🚨 Localizador de Policía y Postas HN")

# 1. Cargar API Key
if "GOOGLE_MAPS_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
    try:
        gmaps = googlemaps.Client(key=API_KEY)
    except Exception as e:
        st.error(f"Error al inicializar Google Maps: {e}")
        st.stop()
else:
    st.error("⚠️ No se encontró la clave GOOGLE_MAPS_API_KEY en los Secrets de Streamlit.")
    st.stop()

# 2. Captura de GPS del dispositivo
loc = get_geolocation()
lat_user, lon_user = None, None

if loc and 'coords' in loc:
    lat_user = loc['coords']['latitude']
    lon_user = loc['coords']['longitude']
    st.success(f"📍 GPS detectado: Lat {round(lat_user, 4)}, Lon {round(lon_user, 4)}")

# Coordenadas manuales de respaldo
with st.expander("🌐 Ver / Ajustar Coordenadas Manuales"):
    col1, col2 = st.columns(2)
    with col1:
        lat_input = st.number_input("Latitud", value=float(lat_user) if lat_user else 14.1232, format="%.6f")
    with col2:
        lon_input = st.number_input("Longitud", value=float(lon_user) if lon_user else -87.9786, format="%.6f")

origen = (lat_input, lon_input)

# 3. Consultar la API y almacenar resultados en session_state
if st.button("🔎 Buscar Dependencias Policiales Cercanas") or "top3_data" in st.session_state:
    
    if "top3_data" not in st.session_state or st.session_state.get("last_origen") != origen:
        with st.spinner("Consultando Google Maps..."):
            try:
                places_result = gmaps.places_nearby(
                    location=origen,
                    rank_by='distance',
                    keyword='policia'
                )
                
                resultados_raw = places_result.get('results', [])
                if not resultados_raw:
                    st.warning("No se encontraron dependencias policiales cercanas.")
                    st.stop()

                destinos = []
                lista_lugares = []
                for place in resultados_raw[:10]:
                    plat = place['geometry']['location']['lat']
                    plon = place['geometry']['location']['lng']
                    destinos.append((plat, plon))
                    lista_lugares.append({
                        "Nombre": place.get('name', 'Policía'),
                        "Dirección": place.get('vicinity', 'Sin dirección'),
                        "lat": plat,
                        "lon": plon
                    })

                matrix = gmaps.distance_matrix(origen, destinos, mode="driving")
                
                resultados_finales = []
                for idx, lugar in enumerate(lista_lugares):
                    element = matrix['rows'][0]['elements'][idx]
                    dist_km = element['distance']['value'] / 1000.0 if element['status'] == 'OK' else float('inf')
                    tiempo = element['duration']['text'] if element['status'] == 'OK' else "N/D"
                    
                    resultados_finales.append({
                        "id": idx,
                        "Nombre_Raw": lugar["Nombre"],
                        "Dirección": lugar["Dirección"],
                        "Distancia": f"{round(dist_km, 2)} km",
                        "Tiempo": tiempo,
                        "dist_num": dist_km,
                        "lat": lugar["lat"],
                        "lon": lugar["lon"]
                    })
                
                df_top3 = pd.DataFrame(resultados_finales).sort_values("dist_num").head(3).reset_index(drop=True)
                st.session_state["top3_data"] = df_top3
                st.session_state["last_origen"] = origen

            except Exception as e:
                st.error(f"❌ Error al consultar la API: {e}")
                st.stop()

    df_top3 = st.session_state["top3_data"]

    # 4. Obtener cuál fue seleccionado mediante el parámetro URL (?sel=0, ?sel=1, etc.)
    query_params = st.query_params
    sel_id = int(query_params.get("sel", 0))

    if sel_id >= len(df_top3):
        sel_id = 0

    # 5. Formatear la columna 'Dependencia Policial' como hipervínculo interno
    df_tabla = df_top3.copy()
    
    # Asignamos la URL con el parámetro 'sel' directamente en el valor del nombre
    df_tabla["Dependencia Policial"] = [
        f"?sel={i}" for i in range(len(df_tabla))
    ]

    st.subheader("Top 3 Puntos Policiales Más Cercanos")
    
    # 6. Configurar la columna de nombres como enlace interactivo
    st.dataframe(
        df_tabla[["Dependencia Policial", "Dirección", "Distancia", "Tiempo"]],
        use_container_width=True,
        column_config={
            "Dependencia Policial": st.column_config.LinkColumn(
                "Dependencia Policial", 
                help="Haz clic sobre el nombre para mostrar su ruta en el mapa",
                display_text=r".*"  # Utiliza expresión regular para mostrar los nombres originales
            )
        }
    )

    # Reemplazar visualmente las etiquetas de los enlaces con los nombres reales
    # Asignamos el nombre visible directamente
    df_tabla["Dependencia Policial Text"] = df_top3["Nombre_Raw"]

    # Renderizar mapa de la opción seleccionada
    estacion_elegida = df_top3.iloc[sel_id]
    dest_lat, dest_lon = estacion_elegida["lat"], estacion_elegida["lon"]
    
    gmaps_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={origen[0]},{origen[1]}&destination={dest_lat},{dest_lon}&mode=driving"
    
    st.subheader(f"🗺️ Ruta a: {estacion_elegida['Nombre_Raw']}")
    st.components.v1.iframe(gmaps_embed_url, height=450)
