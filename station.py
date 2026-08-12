import googlemaps

# 1. Tu API Key
API_KEY = "AIzaSyBxOLyStOQaJtay8gMRjjeA0byQVE4q9u8"
gmaps = googlemaps.Client(key=API_KEY)

# 2. Coordenadas de prueba
origen = (14.1232, -87.9786)
DISTANCIA_MAXIMA_KM = 50 

print("--> Iniciando script de prueba...")

try:
    # Búsqueda por cercanía
    print("--> Solicitando lugares a Google Places API...")
    resultado_places = gmaps.places_nearby(
        location=origen,
        rank_by='distance',
        type='police'  # Cambiamos a type='police' que es más estándar en la API
    )

    lugares_brutos = resultado_places.get('results', [])
    status = resultado_places.get('status')
    
    print(f"--> Respuesta de API recibida. Estado: '{status}'. Lugares devueltos: {len(lugares_brutos)}")

    if status != 'OK' and status != 'ZERO_RESULTS':
        print(f"⚠️ Advertencia: La API devolvió el estado: {status}")

    if not lugares_brutos:
        print("❌ No se encontraron estaciones de policía registradas cerca de estas coordenadas.")
    else:
        lista_lugares_cercanos = []

        for lugar in lugares_brutos:
            nombre = lugar.get('name', 'Sin nombre')
            lat_destino = lugar['geometry']['location']['lat']
            lng_destino = lugar['geometry']['location']['lng']
            destino = (lat_destino, lng_destino)
            direccion = lugar.get('vicinity', 'Dirección no disponible')

            # Calcular distancia por carretera
            try:
                matriz = gmaps.distance_matrix(origins=origen, destinations=destino, mode='driving')
                elem = matriz['rows'][0]['elements'][0]

                if elem['status'] == 'OK':
                    dist_m = elem['distance']['value']
                    dist_km = dist_m / 1000.0
                    
                    if dist_km <= DISTANCIA_MAXIMA_KM:
                        lista_lugares_cercanos.append({
                            'nombre': nombre,
                            'direccion': direccion,
                            'distancia_texto': elem['distance']['text'],
                            'duracion_texto': elem['duration']['text'],
                            'distancia_km': dist_km
                        })
            except Exception as e_mat:
                print(f"Error en Distance Matrix: {e_mat}")

        # Mostrar resultados
        print(f"\n=== RESULTADOS FILTRADOS (< {DISTANCIA_MAXIMA_KM} KM) ===")
        print(f"Total en rango: {len(lista_lugares_cercanos)}\n")

        if len(lista_lugares_cercanos) == 0:
            print(f"⚠️ Se encontraron {len(lugares_brutos)} lugares, pero ninguno está a menos de {DISTANCIA_MAXIMA_KM} km por carretera.")
        else:
            for idx, item in enumerate(lista_lugares_cercanos, start=1):
                print(f"{idx}. {item['nombre']}")
                print(f"   📍 {item['direccion']}")
                print(f"   🚗 Distancia: {item['distancia_texto']} ({item['duracion_texto']})")
                print("-" * 40)

except Exception as e:
    print(f"❌ Error crítico al ejecutar el script: {e}")
