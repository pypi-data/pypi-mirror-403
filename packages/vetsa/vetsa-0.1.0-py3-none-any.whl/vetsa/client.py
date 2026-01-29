import requests
import base64
from typing import Optional, Dict, Union

class VetsaClient:
    """
    Cliente oficial para interactuar con la API de Vetsa Intelligence.
    Basado en Vetsa Cloud v1.2.0
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # CORRECCIÓN 1: La URL correcta según la documentación
        self.endpoint = "https://api.vetsa.site/v1/generate"
        
        # CORRECCIÓN 2: El header correcto es 'x-api-key', no 'Authorization'
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "VetsaPythonSDK/0.1.0"
        }

    def _request(self, payload: Dict):
        """Método interno para manejar las peticiones HTTP"""
        try:
            response = requests.post(self.endpoint, json=payload, headers=self.headers)
            
            # Manejo de errores basado en códigos de estado de la documentación
            if response.status_code == 401:
                raise PermissionError("Error 401: No autorizado. Verifica tu API Key.")
            elif response.status_code == 402:
                raise BlockingIOError("Error 402: Cuota excedida (Payment Required).")
            elif response.status_code == 429:
                raise ConnectionError("Error 429: Demasiadas peticiones (Rate Limit).")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión con Vetsa Cloud: {e}")

    def generate(self, model: str, contents: str, options: Optional[Dict] = None):
        """
        Método genérico para llamar a cualquier modelo de Vetsa.
        """
        payload = {
            "model": model,
            "contents": contents
        }
        if options:
            payload["options"] = options
            
        return self._request(payload)

    def chat(self, message: str, model: str = "spaik-pro", search: bool = False):
        """
        Helper para chat de texto rápido.
        """
        options = {}
        if search:
            options["search"] = True
            
        return self.generate(model=model, contents=message, options=options)

    def text_to_speech(self, text: str, voice: str = "jonas"):
        """
        Convierte texto a audio y devuelve los bytes del audio decodificados.
        """
        options = {
            "output": "audio",
            "voice": voice,
            "format": "mp3" # Formato recomendado por la documentación
        }
        
        response = self.generate(model="spaik-pro", contents=text, options=options)
        
        # CORRECCIÓN 3: Manejo correcto del audio según sección "Solución de Problemas"
        # La API devuelve 'audioContent', no 'audioBase64'
        audio_b64 = response.get("data", {}).get("audioContent")
        
        if not audio_b64:
            raise ValueError("La respuesta de la API no contiene datos de audio.")
            
        return base64.b64decode(audio_b64)