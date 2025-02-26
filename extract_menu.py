import os
import json
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# Cargar variables de entorno
load_dotenv()
FORM_RECOGNIZER_ENDPOINT = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
FORM_RECOGNIZER_KEY = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
MODEL_ID = os.getenv("MODEL_ID")
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

form_recognizer_client = DocumentAnalysisClient(FORM_RECOGNIZER_ENDPOINT, AzureKeyCredential(FORM_RECOGNIZER_KEY))
blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
container_name = "menus"

def obtener_blob_url(blob_name):
    try:
        # Obtener la URL del blob en el contenedor
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_url = blob_client.url
        print(f"URL generada del blob: {blob_url}")
        return blob_url
    except Exception as e:
        print(f"Error al obtener la URL del blob: {e}")
        return None

def procesar_pdf(blob_url):
    print(f"Procesando el archivo: {blob_url}")
    
    # Asegurarse de que la URL comience con 'https://'
    if not blob_url or not blob_url.startswith("https://"):
        raise ValueError("La URL del blob debe comenzar con 'https://'")

    try:
        # Realizar el análisis del documento utilizando la URL
        poller = form_recognizer_client.begin_analyze_document_from_url(MODEL_ID, blob_url)
        result = poller.result()

        json_result = {
            "restaurante": "N/A",
            "direccion": "N/A",
            "menu_del_dia": [],
            "bebida": "N/A",
            "precio": "N/A"
        }
        for document in result.documents:
            # Obtener datos básicos del restaurante
            json_result["restaurante"] = document.fields.get("nombre").value if document.fields.get("nombre") else "N/A"
            json_result["direccion"] = document.fields.get("direccion").value if document.fields.get("direccion") else "N/A"
            
            # Crear una lista de menús del día
            menu_del_dia = []

            # Buscar las etiquetas de los platos (primer plato, segundo plato, postre)
            if document.fields.get("plato"):
                primer_plato = {
                    "plato": "Primer Plato",
                    "nombre": document.fields.get("plato").value if document.fields.get("plato") else "N/A",
                    "ingredientes": document.fields.get("ingredientes").value if document.fields.get("ingredientes") else "N/A"
                }
                menu_del_dia.append(primer_plato)

            if document.fields.get("plato"):
                segundo_plato = {
                    "plato": "Segundo Plato",
                    "nombre": document.fields.get("plato").value if document.fields.get("plato") else "N/A",
                    "ingredientes": document.fields.get("ingredientes").value if document.fields.get("ingredientes") else "N/A"
                }
                menu_del_dia.append(segundo_plato)

            if document.fields.get("postre"):
                postre = {
                    "plato": "Postre",
                    "nombre": document.fields.get("postres").value if document.fields.get("postres") else "N/A",
                    "ingredientes": document.fields.get("postre-ingrediente").value if document.fields.get("postre-ingrediente") else "N/A"
                }
                menu_del_dia.append(postre)
            

            # Agregar la lista de menús del día al JSON final
            json_result["menu_del_dia"] = menu_del_dia

            # Bebida y precio (si están presentes en el documento)
            json_result["bebida"] = document.fields.get("bebida").value if document.fields.get("bebida") else "N/A"
            json_result["precio"] = document.fields.get("precio").value if document.fields.get("precio") else "N/A"
            print(json_result)
        return json_result
    except Exception as e:
        print(f"Ocurrió un error al procesar el archivo: {e}")
        return {}

# Nombre del archivo en tu contenedor
nombre_blob = "El Buen Sabor 1.pdf"

# Generar la URL del blob
blob_url = obtener_blob_url(nombre_blob)

# Verifica si la URL se genera correctamente antes de pasarla
if blob_url:
    # Procesar el PDF con la URL del blob
    resultado = procesar_pdf(blob_url)
    print(json.dumps(resultado, indent=4))
else:
    print("No se pudo obtener la URL del blob.")
