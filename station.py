import streamlit as st
import pandas as pd
import googlemaps
from streamlit_js_eval import get_geolocation

# 1. Configurar tu API Key de Google Cloud
API_KEY = "AIzaSyBxOLyStOQaJtay8gMRjjeA0byQVE4q9u8"  # Reemplaza con tu clave real
gmaps = googlemaps.Client(key=API_KEY)

# 2. Definir las coordenadas del usuario (Ejemplo: Intibucá / Jesús de Otoro)
lat_usuario = 14.1232
lon_usuario = -87.9786
origen = (lat_usuario, lon_usuario)

# Radio máximo deseado en kilómetros (para filtrar manualmente)
DISTANCIA_MAXIMA_KM = 50 

print(f"Buscando dependencias policiales desde las coordenadas: {origen}...\n")

try:
    # 3. Búsqueda en Places API ordenada estrictamente por CERCANÍA (rank_by='distance')
    # NOTA: Al usar rank_by='distance', NO se debe usar el parámetro 'radius'.
    # Es obligatorio incluir al menos 'keyword', 'type' o 'name'.
    resultado_places = gmaps.places_nearby(
        location=origen,
        rank_by='distance',
        keyword='policia'  # Puedes combinar o cambiar por type='police'
    )

    lugares_brutos = resultado_places.get('results', [])

    if not lugares_brutos:
        print("No se encontraron registros de policía cercanos.")
    else:
        print(f"Se encontraron {len(lugares_brutos)} resultados preliminares. Calculando distancias por carretera...\n")

        # Lista donde guardaremos los lugares procesados
        lista_lugares_cercanos = []

        # 4. Procesar cada lugar devuelto por Google
        for lugar in lugares_brutos:
            nombre = lugar.get('name', 'Estación sin nombre')
            lat_destino = lugar['geometry']['location']['lat']
            lng_destino = lugar['geometry']['location']['lng']
            destino = (lat_destino, lng_destino)
            direccion = lugar.get('vicinity', 'Dirección no disponible')

            # 5. Calcular la distancia real por carretera y tiempo estimado (Distance Matrix API)
            try:
                matriz = gmaps.distance_matrix(
                    origins=origen,
                    destinations=destino,
                    mode='driving'
                )
                
                elemento = matriz['rows'][0]['elements'][0]

                if elemento['status'] == 'OK':
                    distancia_texto = elemento['distance']['text']     # Ej: "12.5 km"
                    distancia_metros = elemento['distance']['value']    # Ej: 12500
                    duracion_texto = elemento['duration']['text']       # Ej: "18 mins"
                    
                    distancia_km = distancia_metros / 1000.0

                    # Filtrar si supera la distancia máxima que deseamos mostrar
                    if distancia_km <= DISTANCIA_MAXIMA_KM:
                        lista_lugares_cercanos.append({
                            'nombre': nombre,
                            'direccion': direccion,
                            'distancia_km': distancia_km,
                            'distancia_texto': distancia_texto,
                            'duracion_texto': duracion_texto,
                            'coordenadas': destino
                        })
            except Exception as err_matrix:
                print(f"Error al calcular matriz de distancia para {nombre}: {err_matrix}")

        # 6. Mostrar los resultados ordenados correctamente al usuario
        print(f"=== ESTACIONES Y POSTAS POLICIALES MÁS CERCANAS (Máx. {DISTANCIA_MAXIMA_KM} km) ===\n")
        
        for idx, item in enumerate(lista_lugares_cercanos, start=1):
            print(f"{idx}. {item['nombre']}")
            print(f"   📍 Dirección: {item['direccion']}")
            print(f"   🚗 Distancia por carretera: {item['distancia_texto']}")
            print(f"   ⏱️ Tiempo estimado: {item['duracion_texto']}")
            print(f"   🗺️ Coordenadas: {item['coordenadas']}")
            print("-" * 50)

except Exception as e:
    print(f"❌ Error durante la llamada a la API de Google: {e}")
