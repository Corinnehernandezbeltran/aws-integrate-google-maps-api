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
import unittest
import datetime # Se incluye la librería datetime

#%% Configuración de credenciales AWS
AWS_ACCESS_KEY_ID = input("ATENCIÓN! Ingresa tu AWS_ACCESS_KEY_ID: ")
AWS_SECRET_ACCESS_KEY = input("ATENCIÓN! Ingresa tu AWS_SECRET_ACCESS_KEY: ")
AWS_DEFAULT_REGION = "us-east-2"

os.environ["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY_ID
os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_ACCESS_KEY
os.environ["AWS_DEFAULT_REGION"] = AWS_DEFAULT_REGION

print("Credenciales de AWS, cargadas.")

#%% Ingreso de clave de Google Maps API
GOOGLE_API_KEY = input("ATENCIÓN! Ingresa tu API key de Google Maps:  ")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

#%% Generación de datos para Bogotá (sólo formatos válidos)
def crear_direccion_bogota():
    """
    Inventa una dirección de Bogotá con el formato estándar colombiano (CRA/CLL # n-n)!
    Esto es solo para generar datos de prueba validos.
    """
    tipos_via = ["CRA", "CLL", "TRANSV"]
    via = random.choice(tipos_via)
    principal = random.randint(1, 120)
    secundaria = f"{random.randint(1, 120)}{random.choice(['', 'A', 'B'])}"
    interior = random.randint(1, 120)
    return f"{via} {principal} # {secundaria}-{interior}", "Bogotá"

generador = Faker("es_CO")
os.makedirs("documentos_clientes_wenia", exist_ok=True)

cantidad_clientes = 100
lista_clientes = []
nombre_bucket = "prueba-wenia" # Definición global del bucket

for i in range(cantidad_clientes):
    nombre = generador.name()
    direccion, ciudad = crear_direccion_bogota()
    correo = generador.email()

    lista_clientes.append({
        "id_cliente": i + 1,
        "nombre": nombre,
        "direccion": f"{direccion}, {ciudad}",
        "correo": correo,
    })
    ruta_pdf = f"documentos_clientes_wenia/cliente_wenialover{i+1}.pdf"
    pdf = canvas.Canvas(ruta_pdf, pagesize=letter)
    pdf.drawString(100, 750, f"Registro del cliente {nombre}")
    pdf.drawString(100, 710, f"Correo: {correo}")
    pdf.drawString(100, 670, f"Dirección: {direccion}, {ciudad}")
    pdf.save()

clientes_df = pd.DataFrame(lista_clientes)
ruta_excel = "clientes_simulados.xlsx"
clientes_df.to_excel(ruta_excel, index=False)
print(f"Generados {cantidad_clientes} clientes y sus PDFs.")

s3 = boto3.client("s3")

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
        raise e

try:
    s3.upload_file(ruta_excel, nombre_bucket, os.path.basename(ruta_excel))
    print(f"Subido a s3://{nombre_bucket}/{os.path.basename(ruta_excel)}")
except Exception as e:
    print("Error subiendo Excel:", e)

for archivo in os.listdir("documentos_clientes_wenia"):
    ruta_local = os.path.join("documentos_clientes_wenia", archivo)
    if os.path.isfile(ruta_local):
        try:
            s3.upload_file(ruta_local, nombre_bucket, f"documentos_clientes_wenia/{archivo}")
        except Exception as e:
            print(f"Error subiendo {archivo}:", e)

print("Todos los PDFs fueron subidos a S3 correctamente.")

#%% Función para extraer texto del OCR
def extraer_texto(archivo_bytes, nombre_archivo):
    """
    Saca el texto de un PDF.
    Devuelve todo el texto en MAYÚSCULAS y sin tildes.
    """
    nombre_archivo = nombre_archivo.lower()
    if not nombre_archivo.endswith(".pdf"):
        raise ValueError("El archivo no es un PDF válido.")
    texto_total = ""
    with pdfplumber.open(io.BytesIO(archivo_bytes)) as pdf:
        for pagina in pdf.pages:
            texto_pagina = pagina.extract_text() or ""
            if texto_pagina.strip():
                texto_total += texto_pagina + "\n"
                continue
            try:
                im = pagina.to_image(resolution=300).original
                texto_ocr = pytesseract.image_to_string(im, lang="spa")
                texto_total += texto_ocr + "\n"
            except Exception as e:
                print(f"Warning: OCR falló en {nombre_archivo} página {pagina.page_number}: {e}")
                continue
    return unidecode(texto_total).upper()

#%% Funcion para limpiar dirección
def limpiar_direccion(direccion):
    """
    Pone la dirección en mayúsculas, elimina tildes y símbolos raros (#, ., -), y corrige espacios dobles.
    """
    direccion = unidecode(direccion.upper().strip())
    direccion = re.sub(r'[\.\#,\-]', ' ', direccion)
    direccion = re.sub(r'\s+', ' ', direccion)
    return direccion.strip()

#%% Funcion para buscar dirección
def buscar_direccion(texto: str) -> list:
    """
    Busca la línea de texto que viene justo después de la etiqueta 'DIRECCION:'.
    """
    texto = unidecode(texto.upper())
    patron_especifico = r"DIRECCION:\s*(.*)"
    match = re.search(patron_especifico, texto)
    if match:
        direccion_encontrada = match.group(1).strip()
        return [direccion_encontrada]
    return []

#%% Función para generar variantes de una dirección
def generar_variantes(direccion: str):
    """
    Crea todas las formas posibles de escribir una dirección (Kra, Carrera, #, Nro, etc.) 
    basándose en el formato estándar.
    """
    direccion = direccion.strip().upper()
    patron = r'^(CRA|CLL|TRANSV)\s+(\d+)\s+#\s*([A-Z0-9]+)[ -]+(\d+)$'
    match = re.match(patron, direccion)
    if not match:
        raise ValueError(f"Dirección no válida: {direccion}")

    via, num_principal, sufijo, num_final = match.groups()
    sufijo = sufijo.upper()

    vias = ["Carrera", "Kra", "Calle", "Transversal", "Avenida"]
    numeros = ["#", "Num", "Numero", "Nro"]

    variantes = []
    for via_nombre in vias:
        for num_formato in numeros:
            if num_formato == "#":
                variante = f"{via_nombre} {num_principal} # {sufijo}-{num_final}"
            else:
                variante = f"{via_nombre} {num_principal} {num_formato} {sufijo}-{num_final}"
            variantes.append(variante)
    return variantes

#%% Función para compaación de variantes de la dirección
def comparar_variantes(original, variantes, umbral=90):
    """
    Compara la dirección original con todas sus variantes usando RapidFuzz. 
    Solo devuelve las variantes que superan el umbral (ej. 90%).
    """
    coincidencias = []
    for v in variantes:
        puntaje = fuzz.token_sort_ratio(limpiar_direccion(original), limpiar_direccion(v))
        if puntaje >= umbral:
            coincidencias.append((v, puntaje))
    return coincidencias

#%% Función para geocodificar las direcciones y variantes.
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_API_KEY"))

def geocodificar_direccion(direccion, ciudad="BOGOTA"):
    """
    Manda la dirección a Google Maps para que nos retorne la Latitud y Longitud exacta. 
    La búsqueda se restringe a la ciudad especificada.
    """
    try:
        resultado = gmaps.geocode(f"{direccion}, {ciudad}, Colombia")
        if not resultado:
            return None, None
        lat = resultado[0]["geometry"]["location"]["lat"]
        lng = resultado[0]["geometry"]["location"]["lng"]
        return lat, lng
    except Exception as e:
        print(f"Error geocodificando {direccion}: {e}")
        return None, None

def listar_todos_objetos_s3(s3_client, bucket_name, prefix=None):
    """
    Recorre tu bucket de AWS y devuelve la lista de todos los archivos que hay allí, manejando la paginación.
    """
    objetos = []
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix or "")
    for page in page_iterator:
        if "Contents" in page:
            objetos.extend(page["Contents"])
    return objetos

#%% Procesar y graficar SOLO la mejor similitud
def procesar_archivos_y_generar_mapa(bucket_name="prueba-wenia", ciudad="BOGOTA", umbral_similitud=90):
    """
    Orquesta la descarga, el filtrado estricto por ciudad, la búsqueda de variantes, 
    la geocodificación y el guardado final de resultados (Excel y mapa HTML) en la carpeta local descargas y S3.
    """
    s3 = boto3.client("s3")
    respuesta = listar_todos_objetos_s3(s3, bucket_name)

    if not respuesta:
        print("No se encontraron archivos en el bucket.")
        return None, None

    filas = []
    for obj in respuesta:
        clave = obj["Key"]
        if not clave.lower().endswith(".pdf"):
            continue

        archivo = io.BytesIO()
        s3.download_fileobj(bucket_name, clave, archivo)
        archivo.seek(0)

        texto = extraer_texto(archivo.getvalue(), clave)
        direcciones = buscar_direccion(texto)
        if not direcciones:
            continue

        for direccion in direcciones:
            if ',' in direccion:
                partes = direccion.rsplit(',', 1)
                direccion_sin_ciudad = partes[0].strip()
                ciudad_original = partes[1].strip()
            else:
                direccion_sin_ciudad = direccion.strip()
                ciudad_original = ""

            ciudad_objetivo_norm = unidecode(ciudad).upper()

            if ciudad_original:
                if ciudad_original.upper() != ciudad_objetivo_norm:
                    continue
            else:
                ciudad_original = ciudad_objetivo_norm

            try:
                variantes = generar_variantes(direccion_sin_ciudad)
            except Exception as ex:
                print(f"Dirección '{direccion_sin_ciudad}' no válida para variantes. Saltando. Error: {ex}")
                continue
            coincidencias = comparar_variantes(direccion_sin_ciudad, variantes, umbral_similitud)

            if coincidencias:
                mejor_coincidencia, mejor_similitud = max(coincidencias, key=lambda x: x[1])
                lat, lng = geocodificar_direccion(mejor_coincidencia, ciudad=ciudad_objetivo_norm)
                if lat is not None and lng is not None:
                    filas.append({
                        "archivo": clave,
                        "direccion_original": direccion,
                        "ciudad_original": ciudad_original,
                        "direccion_similar": mejor_coincidencia,
                        "similitud": mejor_similitud,
                        "lat": lat,
                        "lng": lng
                    })

    if not filas:
        print(f"No se encontraron direcciones válidas en {ciudad}.")
        return None, None

    df = pd.DataFrame(filas)

    # Guardar localmente y subir a S3 (ambos archivos) 
    
    carpeta_descargas = os.path.expanduser(r"C:\Users\user\Downloads") 
    os.makedirs(carpeta_descargas, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nombres de archivo base
    excel_file_name = f"direcciones_resultado_{timestamp}.xlsx"
    map_file_name = f"mapa_direcciones_{timestamp}.html"
    
    # Rutas locales (en carpeta_descargas)
    excel_path = os.path.join(carpeta_descargas, excel_file_name)
    mapa_path = os.path.join(carpeta_descargas, map_file_name)

    # Guardar Excel localmente
    df.to_excel(excel_path, index=False)
    print(f"Resultados guardados localmente en '{excel_path}'")
    
    # Generar y guardar mapa localmente
    lat_centro = df["lat"].mean()
    lng_centro = df["lng"].mean()
    mapa = folium.Map(location=[lat_centro, lng_centro], zoom_start=12)
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
        
    mapa.save(mapa_path) 
    print(f"Mapa generado y guardado en '{mapa_path}'")
    
    # Subir a S3 
    try:
        # Subir Excel
        s3.upload_file(excel_path, bucket_name, excel_file_name)
        print(f"Subido Excel a s3://{bucket_name}/{excel_file_name}")
        
        # Subir Mapa HTML
        s3.upload_file(mapa_path, bucket_name, map_file_name)
        print(f"Subido Mapa a s3://{bucket_name}/{map_file_name}")
        
    except Exception as e:
        print(f"Error subiendo archivos a S3:", e)

    return df, mapa_path

#%% Pruebas unitarias
class TestDireccionesBogota(unittest.TestCase):

    def test_generar_variantes_cantidad(self):
        direccion = "CLL 45 # 56-89"
        variantes = generar_variantes(direccion)
        self.assertEqual(len(variantes), 20)
        for via in ["Calle", "Carrera", "Kra", "Transversal", "Avenida"]:
            self.assertTrue(any(via in v for v in variantes), f"Falta via {via}")
        for num_f in ["#", "Nro", "Num", "Numero"]:
            self.assertTrue(any(f" {num_f} " in v or f" {num_f}# " in v for v in variantes), f"Falta num formato {num_f}")

    def test_generar_variantes_no_original(self):
        direccion = "CRA 88 # 11A-17"
        variantes = generar_variantes(direccion)
        self.assertNotIn("CRA 88 # 11A-17", variantes)
        self.assertNotIn("Cra 88 # 11A-17", variantes)

    def test_generar_variantes_format_invalido(self):
        with self.assertRaises(ValueError):
            generar_variantes("AV 12 # 34-56")
        with self.assertRaises(ValueError):
            generar_variantes("CALLE 90#20A-15")

    def test_limpiar_direccion(self):
        inp = "Cll. 80 # 34-12, Bogotá"
        esperado = "CLL 80 34 12 BOGOTA"
        resultado = limpiar_direccion(inp)
        self.assertEqual(resultado, esperado)

    def test_similitud(self):
        v1 = "Carrera 12 # 90-45"
        variantes = generar_variantes("CRA 12 # 90-45")
        simis = comparar_variantes(v1, variantes, umbral=96)
        self.assertTrue(any("Carrera 12 # 90-45" in v[0] for v in simis))
        simis_baja = comparar_variantes("Calle 99 # 99-99", variantes, umbral=96)
        self.assertFalse(simis_baja)

    def test_buscar_direccion(self):
        texto = "Direccion: CLL 51 # 12B-66\nOtra cosa"
        lista = buscar_direccion(texto)
        self.assertTrue(lista)
        self.assertEqual(lista[0], "CLL 51 # 12B-66")

#%% MAIN ejecutable
if __name__ == "__main__": 
    resultado_df, mapa_path = procesar_archivos_y_generar_mapa(bucket_name="prueba-wenia", ciudad="BOGOTA")
    if resultado_df is not None:
        print(resultado_df.head(8))
        import webbrowser
        webbrowser.open(mapa_path)