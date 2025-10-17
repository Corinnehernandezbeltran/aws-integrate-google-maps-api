# aws-integrate-google-maps-api🌏

Este proyecto automatiza la extracción y georreferenciación de direcciones contenidas en archivos PDF almacenados en AWS S3, generando un mapa interactivo y un archivo Excel con los resultados.
El flujo completo permite pasar de datos sin procesar a resultados listos para análisis y visualización de manera eficiente y reproducible.

---

## El flujo del proyecto incluye:

Cargar archivos PDF desde un bucket en S3.
Extraer texto de los PDFs para obtener direcciones.
Normalizar y estandarizar las direcciones para mejorar la precisión.
Georreferenciar las direcciones usando la API de Google Maps.
Generar un Excel con coordenadas y un mapa interactivo HTML.

## Tecnologías y Herramientas

Python: Pandas, PyPDF2, Requests, Google Maps API, Anaconda.
AWS S3: Almacenamiento de archivos PDF
Excel y HTML: Resultados de la extracción y visualización

## Resultados

direcciones_resultado.xlsx: Contiene las direcciones procesadas y sus coordenadas geográficas.
mapa_direcciones_resultado.html: Mapa interactivo con las ubicaciones georreferenciadas.
Incluye métricas de similitud entre las direcciones originales y normalizadas para garantizar calidad en la georreferenciación.

---

## Cómo ejecutar el proyecto

Requisitos previos: 
-Debes tener una clave de API válida configurada como variable de entorno: os.environ["GOOGLE_API_KEY"] = "TU_API_KEY_AQUI" Puedes generar esta clave desde la Consola de Google Cloud
-Se requiere acceso a un bucket S3 (prueba-wenia). Configura tus credenciales antes de ejecutar el script, si no tienes acceso al bucket solo con las credenciales se crea la carpeta en tu s3. O solicitar permiso 
a autor, Corinne Hernández.
        os.environ["AWS_ACCESS_KEY_ID"] = "TU_ACCESS_KEY" --Ingresar TU_ACCESS_KEY (son inputs en el .py)
        os.environ["AWS_SECRET_ACCESS_KEY"] = "TU_SECRET_KEY" --Ingresar TU_ACCESS_KEY (son inputs en el .py)
        os.environ["AWS_DEFAULT_REGION"] = "us-east-2" Ya está configurada en ohio no se debe hacer nada.

1. Clonar el repositorio:
  git clone https://github.com/Corinnehernandezbeltran/prueba-wenia.git

2. Navegar al directorio
  cd prueba-wenia

3. Instalar dependencias:
   pip install -r requirements.txt
   También puedes instalarlas manualmente si lo prefieres:
   pip install pdfplumber pytesseract pillow boto3 googlemaps folium rapidfuzz openpyxl pandas faker reportlab unidecode
   
5. Ejecutar directamente el script:
   python corinne_hernandez_prueba_wenia.py

Dependencias principales:

pdfplumber → extracción de texto desde PDFs
pytesseract → reconocimiento óptico de caracteres (OCR)
boto3 → conexión con AWS S3
googlemaps → geocodificación de direcciones
folium → generación de mapas interactivos
rapidfuzz → comparación de similitud entre textos
pandas, openpyxl → manejo y exportación de datos
faker, reportlab → generación de PDFs simulados
unidecode → limpieza de tildes y caracteres especiales

## Visualización del Mapa

Puedes ver el mapa interactivo generado aquí:  
👉 [Mapa interactivo de direcciones](https://corinnehernandezbeltran.github.io/prueba-wenia/mapa_direcciones.html)


👩‍💻 Corinne Hernández Beltrán
Lenguaje: Python
Entorno de ejecución: Spyder (Anaconda)
Repositorio: github.com/Corinnehernandezbeltran/prueba-wenia
