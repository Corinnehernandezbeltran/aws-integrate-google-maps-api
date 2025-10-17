# -*- coding: utf-8 -*-
"""
Script de prueba técnica - Wenia
Autor: Corinne Hernández

Genera direcciones simuladas de clientes, extrae texto desde PDFs almacenados en S3,
procesa direcciones mediante OCR y geocodificación en Google Maps, 
y genera un mapa interactivo con los resultados.
"""

#%%Importar librerias necesarias
import os
import io
import re
import random
import boto3
import pandas as pd
from faker import Faker
import pdfplumber
import pytesseract
from rapidfuzz import fuzz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import googlemaps
import folium
from folium.plugins import MarkerCluster
from unidecode import unidecode

#%%Configuracion credenciales AWS
AWS_ACCESS_KEY_ID = input("ATENCIÓN! Ingresa tu AWS_ACCESS_KEY_ID🔑: ")
AWS_SECRET_ACCESS_KEY = input("ATENCIÓN! Ingresa tu AWS_SECRET_ACCESS_KEY🕵️: ")
AWS_DEFAULT_REGION = "us-east-2"  # Region Ohio para el ejercicio.

os.environ["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY_ID
os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_ACCESS_KEY
os.environ["AWS_DEFAULT_REGION"] = AWS_DEFAULT_REGION

print("Credenciales cargadas de forma temporal y segura.")

#%% Se ingresa la clave de google api para utilizar el servicio.
GOOGLE_API_KEY = input("ATENCIÓN! Ingresa tu API key de Google Maps 🗺️:  ")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

#%%% Configuración de Faker, para generar dircciones falsas pero realistas
generador = Faker("es_CO")
os.makedirs("documentos_clientes_wenia", exist_ok=True)

def crear_direccion():
    tipos_via = ["CRA", "KRA", "CALLE", "AV", "TRANSVERSAL"]
    return f"{random.choice(tipos_via)} {random.randint(1,99)} # {random.randint(1,99)} - {random.randint(1,99)}"

cantidad_clientes = 40
lista_clientes = []
N_BOGOTA = 12

for i in range(cantidad_clientes):
    nombre = generador.name()

    # Las primeras N direcciones serán de Bogotá, el resto aleatorias
    if i < N_BOGOTA:
        ciudad = "Bogotá"
    else:
        ciudad = generador.city()

    direccion = f"{crear_direccion()}, {ciudad}"
    correo = generador.email()

    lista_clientes.append({
        "id_cliente": i + 1,
        "nombre": nombre,
        "direccion": direccion,
        "correo": correo,
    })

    # Generar PDF individual
    ruta_pdf = f"documentos_clientes_wenia/cliente_wenialover{i+1}.pdf"
    pdf = canvas.Canvas(ruta_pdf, pagesize=letter)
    pdf.drawString(100, 750, f"Registro del cliente {nombre}")
    pdf.drawString(100, 710, f"Correo: {correo}")
    pdf.drawString(100, 670, f"Dirección: {direccion}")
    pdf.save()

# Guardar base de datos simulada

clientes_df = pd.DataFrame(lista_clientes)
ruta_excel = "clientes_simulados.xlsx"
clientes_df.to_excel(ruta_excel, index=False)
print(f"Generados {cantidad_clientes} clientes y sus PDFs.")

# Subir archivos a S3

nombre_bucket = "prueba-wenia"
s3 = boto3.client("s3")

# Verificar si el bucket existe; si no, crearlo directamente en s3
try:
    s3.head_bucket(Bucket=nombre_bucket)
    print(f"El bucket '{nombre_bucket}' ya existe.")
except s3.exceptions.ClientError as e:
    error_code = e.response["Error"]["Code"]
    if error_code == "404":
        print(f"El bucket '{nombre_bucket}' no existe. Creándolo...")
        s3.create_bucket(
            Bucket=nombre_bucket,
            CreateBucketConfiguration={"LocationConstraint": AWS_DEFAULT_REGION}
        )
        print(f"Bucket '{nombre_bucket}' creado exitosamente.")
    else:
        raise e  # Si el error no es "no existe", se lanza para no ocultar otros problemas

# Subir Excel
try:
    s3.upload_file(ruta_excel, nombre_bucket, os.path.basename(ruta_excel))
    print(f"Subido a s3://{nombre_bucket}/{os.path.basename(ruta_excel)}")
except Exception as e:
    print("Error subiendo Excel:", e)

# Subir PDFs
for archivo in os.listdir("documentos_clientes_wenia"):
    ruta_local = os.path.join("documentos_clientes_wenia", archivo)
    if os.path.isfile(ruta_local):
        try:
            s3.upload_file(ruta_local, nombre_bucket, f"documentos_clientes_wenia/{archivo}")
        except Exception as e:
            print(f"Error subiendo {archivo}:", e)

print("Todos los PDFs fueron subidos a S3 correctamente, finaliza creación datos y cargue")


#%% En esta sección se definen las funciones utilizadas para:
# - Limpieza y estandarización de direcciones.
# - Generación de variantes para comparación de similitud.
# - Evaluación de similitud entre direcciones con RapidFuzz.
# - Geocodificación de direcciones usando la API de Google Maps.

#Función para extraer texto de archivos PDF
def extraer_texto(archivo_bytes, nombre_archivo):
    """Extrae el texto de un archivo PDF; si extract_text falla, aplica OCR por página."""
    nombre_archivo = nombre_archivo.lower()
    if not nombre_archivo.endswith(".pdf"):
        raise ValueError("El archivo no es un PDF válido.")

    texto_total = ""
    with pdfplumber.open(io.BytesIO(archivo_bytes)) as pdf:
        for pagina in pdf.pages:
            # Intento nativo de extracción
            texto_pagina = pagina.extract_text() or ""
            if texto_pagina.strip():
                texto_total += texto_pagina + "\n"
                continue

            # Si no hay texto, tomo la página como imagen y aplico OCR
            try:
                im = pagina.to_image(resolution=300).original  # PIL Image
                texto_ocr = pytesseract.image_to_string(im, lang="spa")
                texto_total += texto_ocr + "\n"
            except Exception as e:
                # Si falla OCR, continuar y reportar
                print(f"Warning: OCR falló en {nombre_archivo} página {pagina.page_number}: {e}")
                continue

    return unidecode(texto_total).upper()

#Funcion para limpieza de la dirección y estandarizar una dirección que ya fue identificada
def limpiar_direccion(direccion):
    """
    Limpia y estandariza una dirección eliminando tildes,
    símbolos innecesarios y espacios múltiples.
    """
    direccion = unidecode(direccion.upper().strip())  # elimina tildes y pone en MAYUS
    direccion = re.sub(r'[.#]', '', direccion)        # quita puntos y #
    direccion = re.sub(r'\s+', ' ', direccion)        # reemplaza espacios múltiples
    return direccion

#Funcion para  buscar dentro de un texto completo (pdf )la línea que contiene la dirección
def buscar_direccion(texto: str) -> list:
    """
    Busca el texto de la dirección que sigue a 'DIRECCION:' o 'DIRECCIÓN:' y lo devuelve
    limpio y estandarizado.
    """
    # Asegurar texto en mayúsculas y sin tildes
    texto = unidecode(texto.upper())  # <-- requiere importar unidecode

    # Patrón que busca tanto DIRECCION como DIRECCIÓN
    patron_especifico = r"DIRECCION:\s*(.*)"

    match = re.search(patron_especifico, texto)
    if match:
        direccion_encontrada = match.group(1).strip()
        direccion_limpia = limpiar_direccion(direccion_encontrada)
        return [direccion_limpia]
    return []

# Función crear diferentes versiones equivalentes de una misma dirección, para luego compararlas 
def generar_variantes(direccion):
    """
    Genera distintas versiones de una dirección, asegurando que estén limpias
    y listas para la comparación de similitud.
    """
    base = direccion.upper().strip()

    variantes = [
        # Las variantes deben estar limpias para igualar la 'base limpia' en la comparación
        limpiar_direccion(base), # Version base, limpia y sin dobles espacios
        limpiar_direccion(base.replace("CRA", "KRA")),
        limpiar_direccion(base.replace("CRA", "CARRERA")),
        limpiar_direccion(base.replace("#", "Nro")),
        limpiar_direccion(base.replace("-", " ")),
    ]

    #  set para eliminar duplicados
    return list(set(variantes))

#Funcion para comparar variantes de texto y medir similitud entre las mismas.
def comparar_variantes(original, variantes, umbral=90):
    """
    Compara una dirección original con un conjunto de variantes y calcula
    su nivel de similitud utilizando RapidFuzz.
    Retorna las variantes que superen el umbral definido, en este caso 90.
    """
    coincidencias = []
    for v in variantes:
        puntaje = fuzz.ratio(original, v)
        if puntaje >= umbral:
            coincidencias.append((v, puntaje))
    return coincidencias

#Función para conecta con la API de Google Maps y convierte una dirección de texto (latitud y longitud)
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_API_KEY")) #Ok clave ingresada arriba

def geocodificar_direccion(direccion, ciudad="BOGOTA"):
    """
    Usa la API de Google Maps para convertir una dirección en coordenadas geográficas.
    Todas las direcciones se restringen a la ciudad especificada
    """
    try:
        # Limitar el ámbito de búsqueda a la ciudad y a Colombia
        consulta = f"{direccion}, {ciudad}, Colombia"
        resultado = gmaps.geocode(consulta)

        if not resultado:
            return None, None

        ubicacion = resultado[0]['geometry']['location']
        return ubicacion['lat'], ubicacion['lng']

    except Exception as e:
        print("Error al geocodificar la dirección:", direccion, e)
        return None, None

#Funcion para listar todos los objetos (paginación)
def listar_todos_objetos_s3(s3_client, bucket_name, prefix=None):
    objetos = []
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix or "")
    for page in page_iterator:
        if "Contents" in page:
            objetos.extend(page["Contents"])
    return objetos

# Función principal para procesar los archivos del bucket y generar el mapa de direcciones
def procesar_archivos_y_generar_mapa(bucket_name="prueba-wenia", ciudad="BOGOTA", umbral_similitud=90):
    """
    Procesa archivos PDF de un bucket S3, extrae direcciones y genera un mapa.

    Pasos principales:
    1. Descarga PDFs desde S3 y extrae direcciones mediante OCR.
    2. Filtra direcciones por ciudad (por defecto: BOGOTA).
    3. Calcula similitud entre variantes de dirección.
    4. Geocodifica direcciones válidas y genera un mapa con Folium.
    5. Guarda resultados en un archivo Excel y un mapa HTML, y los sube al bucket.

    Parámetros:
        bucket_name (str): Nombre del bucket S3 origen y destino.
        ciudad (str): Ciudad objetivo para filtrar direcciones.
        umbral_similitud (float): Valor mínimo de similitud para considerar coincidencias.

    Retorna:
        pd.DataFrame: DataFrame con columnas [archivo, direccion_original, ciudad_original,
        direccion_similar, similitud, lat, lng].
    """
    s3 = boto3.client("s3")
    respuesta = listar_todos_objetos_s3(s3, bucket_name)

    if not respuesta:
        print("No se encontraron archivos en el bucket.")
        return None

    filas = []  

    for obj in respuesta:
        clave = obj["Key"]

        # Filtrar solo archivos PDF
        if not clave.lower().endswith(".pdf"):
            continue

        # Descargar el archivo desde S3 en memoria
        archivo = io.BytesIO()
        s3.download_fileobj(bucket_name, clave, archivo)
        archivo.seek(0)

        # Extraer texto del PDF
        texto = extraer_texto(archivo.getvalue(), clave)
        direcciones = buscar_direccion(texto)
        if not direcciones:
            continue

        # Filtro y geocodificación
        for direccion in direcciones:
            direccion_limpia = limpiar_direccion(direccion)  # aqui se hace unidecode + upper

            if ',' in direccion_limpia:
                partes = direccion_limpia.rsplit(',', 1)
                direccion_sin_ciudad = partes[0].strip()
                ciudad_original = partes[1].strip()
            else:
                direccion_sin_ciudad = direccion_limpia
                ciudad_original = ""

            ciudad_objetivo_norm = unidecode(ciudad).upper()

            # Asegurar comparación en mayúsculas
            if not ciudad_original:
                ciudad_original = ciudad_objetivo_norm
            elif ciudad_objetivo_norm not in ciudad_original.upper():
                continue

            direccion_para_geo = f"{direccion_sin_ciudad}, {ciudad_objetivo_norm}"

            variantes = generar_variantes(direccion_para_geo)
            coincidencias = comparar_variantes(direccion_para_geo, variantes, umbral_similitud)

            for coincidencia, puntaje in coincidencias:
                # Manejo de errores en geocodificación
                try:
                    lat, lng = geocodificar_direccion(coincidencia, ciudad=ciudad_objetivo_norm)
                except Exception as e:
                    print(f"Error al geocodificar {coincidencia}: {e}")
                    lat, lng = None, None

                if lat is not None and lng is not None:
                    filas.append({
                        "archivo": clave,
                        "direccion_original": direccion,
                        "ciudad_original": ciudad_original,
                        "direccion_similar": coincidencia,
                        "similitud": puntaje,
                        "lat": lat,
                        "lng": lng
                    })

    # Validación de resultados
    if not filas:
        print(f"No se encontraron direcciones válidas en {ciudad}.")
        return None

    df = pd.DataFrame(filas)
    df.to_excel("direcciones_resultado.xlsx", index=False)
    print(f"Resultados guardados en 'direcciones_resultado.xlsx'")

    # Subir a S3
    s3.upload_file("direcciones_resultado.xlsx", bucket_name, "direcciones_resultado.xlsx")
    print(f"Archivo subido a s3://{bucket_name}/direcciones_resultado.xlsx")

    # Generar mapa
    mapa = folium.Map(location=[df["lat"].mean(), df["lng"].mean()], zoom_start=12)
    marker_cluster = MarkerCluster().add_to(mapa)

    for _, fila in df.iterrows():
        color = "green" if fila["similitud"] >= 90 else "orange"
        popup = (
            f"<b>Dirección:</b> {fila['direccion_similar']}<br>"
            f"<b>Similitud:</b> {fila['similitud']:.2f}%<br>"
            f"<b>Ciudad:</b> {fila['ciudad_original']}"
        )
        folium.Marker(
            location=[fila["lat"], fila["lng"]],
            popup=popup,
            icon=folium.Icon(color=color)
        ).add_to(marker_cluster)

    mapa.save("mapa_direcciones.html")
    print(f"Mapa generado para {ciudad} y guardado como 'mapa_direcciones.html'")

    return df

#%% Generación  del mapa
if __name__ == "__main__":
    resultado_df = procesar_archivos_y_generar_mapa(bucket_name="prueba-wenia", ciudad="BOGOTA")
    if resultado_df is not None:
        print(resultado_df.head(8))
        import webbrowser
        webbrowser.open("mapa_direcciones.html")