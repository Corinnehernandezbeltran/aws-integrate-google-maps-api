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

Python (Anaconda / Spyder) → desarrollo principal

Librerías: pandas, pdfplumber, pytesseract, boto3, googlemaps, folium, faker, reportlab, unidecode

AWS S3 → almacenamiento y gestión de archivos PDF

Excel y HTML (Folium) → exportación de resultados y visualización de mapas interactivos

## Requisitos previos: 

1. Debes tener una clave de API válida configurada como variable de entorno: 

        os.environ["GOOGLE_API_KEY"] = "TU_API_KEY_AQUI" # Se ingresa por input al ejecutar el script 
        
Puedes generar esta clave desde la Consola de Google Cloud: https://console.cloud.google.com/


2. Se requiere acceso a un bucket S3 llamado prueba-wenia:

🔹 Si ya tienes acceso: el código usará tus credenciales de AWS.

🔹 Si no tienes acceso: el script creará automáticamente el bucket prueba-wenia, pero igualmente debes ingresar tus credenciales válidas para que la conexión funcione.

        os.environ["AWS_ACCESS_KEY_ID"] = "TU_ACCESS_KEY"        # Se ingresa por input al ejecutar el script
        os.environ["AWS_SECRET_ACCESS_KEY"] = "TU_SECRET_KEY"    # Se ingresa por input al ejecutar el script
        os.environ["AWS_DEFAULT_REGION"] = "us-east-2"           # Ya configurada para la región Ohio (no requiere cambios)
        
La región us-east-2 (Ohio) ya está establecida en el código, por lo que no es necesario modificarla.
Solo asegúrate de ingresar tus Access Key y Secret Key cuando el programa las solicite.

---

## Cómo ejecutar el proyecto

1. Clonar el repositorio:
  git clone https://github.com/Corinnehernandezbeltran/prueba-wenia.git

2. Navegar al directorio
  cd prueba-wenia

3. Instalar dependencias:
4. 
   pip install -r requirements.txt
   
   También puedes instalarlas manualmente si lo prefieres:
   
   pip install pdfplumber pytesseract pillow boto3 googlemaps folium rapidfuzz openpyxl pandas faker reportlab unidecode
   
6. Ejecutar directamente el script:
   python corinne_hernandez_prueba_wenia.py

## Dependencias principales:

pdfplumber → extracción de texto desde PDFs

pytesseract → reconocimiento óptico de caracteres (OCR)

boto3 → conexión con AWS S3

googlemaps → geocodificación de direcciones

folium → generación de mapas interactivos

rapidfuzz → comparación de similitud entre textos

pandas, openpyxl → manejo y exportación de datos

faker, reportlab → generación de PDFs simulados

unidecode → limpieza de tildes y caracteres especiales

## Resultados

direcciones_resultado.xlsx: Contiene las direcciones procesadas y sus coordenadas geográficas.

mapa_direcciones_resultado.html: Mapa interactivo con las ubicaciones georreferenciadas.

Puedes ver el mapa interactivo generado aquí:  

👉 [Mapa interactivo de direcciones](https://corinnehernandezbeltran.github.io/prueba-wenia/mapa_direcciones.html)


Incluye métricas de similitud entre las direcciones originales y normalizadas para garantizar calidad en la georreferenciación.


## 👩‍💻 Autor

**Corinne Hernández Beltrán**  
---

**Lenguaje:** Python 🐍  
**Entorno de ejecución:** Spyder (Anaconda)  
**Repositorio:** [github.com/Corinnehernandezbeltran/prueba-wenia](https://github.com/Corinnehernandezbeltran/prueba-wenia)
