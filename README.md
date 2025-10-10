# Proyecto Wenia - Procesamiento de Direcciones🌏

Este proyecto fue desarrollado como parte de una **prueba técnica para Wenia**.  
Su objetivo es automatizar el procesamiento de archivos PDF almacenados en AWS S3, extraer direcciones, estandarizarlas y
 obtener sus coordenadas geográficas mediante la API de Google Maps.

---

## Funcionalidades principales

- Lectura de archivos **PDF** con datos de clientes.  
- Extracción de texto y detección de **direcciones**.  
- Normalización y comparación de variantes de dirección.  
- Geocodificación automática con **Google Maps API**.  
- Generación de un archivo Excel con los resultados.  
- Creación de un **mapa interactivo HTML** con las ubicaciones detectadas.

---

## Requisitos

El proyecto está diseñado para ejecutarse en **Google Colab** .
Se ingresan las credenciales del perfil creador pero permanecen ocultas, en caso de requerir ejecutarlo, se debe solicitar 
el permiso al bucket de s3 y habilitar el API de Google.

Dependencias principales:
```bash
pip install pdfplumber pytesseract pillow boto3 googlemaps folium rapidfuzz openpyxl pandas faker reportlab


Se requiere:
-Credenciales válidas de AWS S3 configuradas (Access Key y Secret Key).
-Una Google Maps API Key activa almacenada como variable de entorno:
os.environ["GOOGLE_API_KEY"] = "TU_API_KEY_AQUI" # se genera de la configuracion de la api desde google


EJECUCION PASO A PASO:
Clonar o descargar este repositorio:
git clone https://github.com/Corinnehernandezbeltran/prueba-wenia
cd prueba-wenia

Abrir el archivo principal en Google Colab (.ipynb).

-Ejecutar las celdas en orden:
-Generación de datos y PDFs.
-Subida de archivos a S3.
-Procesamiento de direcciones.
-Generación de mapa y Excel.

El resultado incluye:
-direcciones_resultado.xlsx → listado de direcciones y coordenadas.
-mapa_direcciones.html → mapa interactivo con las ubicaciones.
-El sistema imprime por consola el número de archivos procesados exitosamente y genera los archivos finales con los resultados de validación

## Visualización del Mapa

Puedes ver el mapa interactivo generado aquí:  
👉 [Mapa interactivo de direcciones](https://corinnehernandezbeltran.github.io/prueba-wenia/mapa_direcciones.html)


Autor: Corinne Hernández Beltrán
Lenguaje: Python
Ejecución: Google Colab
