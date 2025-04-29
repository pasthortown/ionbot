import requests

class APIManager:
    def __init__(self, url_servidor):
        self.url_servidor = url_servidor

    def obtener_clave_admin(self, catalog):
        payload = {"output_model": {"clave_admin": True}}
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.url_servidor + catalog + '/get_items', json=payload, headers=headers)
        if response.status_code == 200:
            configuraciones = response.json()["response"]
            return configuraciones[0]["clave_admin"] if configuraciones else None
        else:
            return None
    
    def obtener_main_config(self, catalog):
        payload = {"output_model": {
                "clave_admin": True,
                "default_tournament_day_of_week": True,
                "default_tournament_hour": True,
                "default_tournament_minute": True,
                "default_tournament_country": True,
                "default_tournament_discord_channel": True,
                "default_tournament_game": True,
                "default_tournament_platform": True,
                "default_tournament_target": True,
                "default_tournament_mode": True,
                "default_tournament_price": True,
            }
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.url_servidor + catalog + '/get_items', json=payload, headers=headers)
        if response.status_code == 200:
            configuraciones = response.json()["response"]
            return configuraciones if configuraciones else None
        else:
            return None
    
    def get_torneos(self):
        catalog = 'torneos'
        payload = {"output_model": {
                "id_torneo": True,
                "fecha": True,
                "pais": True,
                "juego": True,
                "alcance": True,
                "plataforma": True,
                "costo": True,
                "estado": True,
                "channel": True,
                "etapas": True,
                "modalidad": True,
                "observacion": True
            }
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.url_servidor + catalog + '/get_items', json=payload, headers=headers)
        if response.status_code == 200:
            torneos = response.json()["response"]
            return torneos if torneos else None
        else:
            return None
        
    def count_items(self, catalog):
        url = self.url_servidor + catalog + '/count'
        payload = {}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return None
        
    def upload_items(self, catalog, items):
        url = self.url_servidor + catalog + '/upload_items'
        payload = {"items": items}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    
    def update_item(self, catalog, item_id, item):
        url = self.url_servidor + catalog + '/update_item'
        payload = {"item_id": item_id, "item": item}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    
    def detalle_torneo(self, catalog, catalog_torneo, id_torneo):
        url = self.url_servidor + catalog + '/detalle_torneo'
        payload = {"id_torneo": id_torneo, "catalog_torneo": catalog_torneo}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def detalle_depositos_usuario(self, catalog, id_discord):
        url = self.url_servidor + catalog + '/detalle_depositos_usuario'
        payload = {"id_discord": id_discord}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    
    def estado_torneo(self, catalog, id_torneo):
        url = self.url_servidor + catalog + '/estado_torneo'
        payload = {"id_torneo": id_torneo}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()        
    
    def actualizar_estado_torneo(self, catalog, id_torneo, nuevo_estado):
        url = self.url_servidor + catalog + '/actualizar_estado_torneo'
        payload = {"id_torneo": id_torneo, "estado": nuevo_estado}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()