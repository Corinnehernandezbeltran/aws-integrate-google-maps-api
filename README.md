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

Python: Pandas, PyPDF2, Requests, Google Maps API
AWS S3: Almacenamiento de archivos PDF
Google colab.
Excel y HTML: Resultados de la extracción y visualización

## Resultados

direcciones_resultado.xlsx: Contiene las direcciones procesadas y sus coordenadas geográficas.
mapa_direcciones_resultado.html: Mapa interactivo con las ubicaciones georreferenciadas.
Incluye métricas de similitud entre las direcciones originales y normalizadas para garantizar calidad en la georreferenciación.

---

## Cómo ejecutar el proyecto

1. Clonar el repositorio:
  git clone https://github.com/Corinnehernandezbeltran/prueba-wenia.git

2. Navegar al directorio
  cd prueba-wenia

3. Instalar dependencias:
   pip install -r requirements.txt
   
4. Abrir el notebook
   jupyter notebook Corinne_Hernández_prueba_wenia.ipynb

5. Seguir los pasos dentro del notebook para cargar los PDFs, procesar las direcciones y generar resultados.
  Nota: Necesitarás una clave de API de Google Maps para ejecutar la geocodificación. Para el acceso al bucket se debe solicita al acceso al Autor.


Dependencias principales:
```bash
pip install pdfplumber pytesseract pillow boto3 googlemaps folium rapidfuzz openpyxl pandas faker reportlab


Se requiere:
-Credenciales válidas de AWS S3 configuradas (Access Key y Secret Key).
-Una Google Maps API Key activa almacenada como variable de entorno:
os.environ["GOOGLE_API_KEY"] = "TU_API_KEY_AQUI" # se genera de la configuracion de la api desde google

## Visualización del Mapa

Puedes ver el mapa interactivo generado aquí:  
👉 [Mapa interactivo de direcciones](https://corinnehernandezbeltran.github.io/prueba-wenia/mapa_direcciones.html)


Autor: Corinne Hernández Beltrán
Lenguaje: Python
Ejecución: Google Colab
