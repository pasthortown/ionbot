import os
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.escape import json_decode
from pymongo import MongoClient, DESCENDING
import datetime
from bson import json_util
import json
import uuid

mongo_bdd = os.getenv('mongo_bdd')
mongo_bdd_server = os.getenv('mongo_bdd_server')
mongo_user = os.getenv('mongo_user')
mongo_password = os.getenv('mongo_password')

database_uri='mongodb://'+mongo_user+':'+mongo_password+'@'+ mongo_bdd_server +'/'
client = MongoClient(database_uri)
db = client[mongo_bdd]

class DefaultHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def get(self):
        self.write({'response':'Administrador de Torneos Operativo', 'status':200})

class ActionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')
    
    def options(self, catalog, action):
        pass
    
    def post(self, catalog, action):
        content = json_decode(self.request.body)
        if (action == 'upload_items'):
            items = content['items']
            respuesta = upload_items(catalog, items)
        if (action == 'get_item'):
            item_id = content['item_id']
            output_model = content['output_model']
            respuesta = get_item(catalog, item_id, output_model)
        if (action == 'get_items'):
            output_model = content['output_model']
            respuesta = get_items(catalog, output_model)
        if (action == 'update_item'):
            item_id = content['item_id']
            item = content['item']
            respuesta = update_item(catalog, item_id, item)
        if (action == 'search_items'):
            attribute = content['attribute']
            value = content['value']
            output_model = content['output_model']
            respuesta = search_items(catalog, attribute, value, output_model)
        if (action == 'count'):
            respuesta = count_items(catalog)
        if (action == 'actualizar_estado_torneo'):
            id_torneo = content['id_torneo']
            nuevo_estado = content['estado']
            respuesta = actualizar_estado_torneo(catalog, id_torneo, nuevo_estado)
        if (action == 'saldo'):
            id_discord = content['id_discord']
            respuesta = saldo(catalog, id_discord)
        if (action == 'detalle_depositos_usuario'):
            id_discord = content['id_discord']
            respuesta = detalle_depositos_usuario(catalog, id_discord)
        if (action == 'estado_torneo'):
            id_torneo = content['id_torneo']
            respuesta = estado_torneo(catalog, id_torneo)
        if (action == 'detalle_torneo'):
            id_torneo = content['id_torneo']
            catalog_torneo = content['catalog_torneo']
            respuesta = detalle_torneo(catalog, catalog_torneo, id_torneo)
        if (action == 'delete_item'):
            item_id = content['item_id']
            deleted = delete_item(catalog, item_id)
            respuesta = {'response':'Elemento no encontrado', 'status':500}
            if (deleted == True):
                respuesta = {'response':'Elemento eliminado', 'status':200}
        self.write(respuesta)
        return

def actualizar_estado_torneo(catalog, id_torneo, nuevo_estado):
    collection = db[catalog]
    filtro = {"id_torneo": id_torneo}
    nuevo_valor = {"$set": {"estado": nuevo_estado}}
    resultado = collection.update_one(filtro, nuevo_valor)
    if resultado.modified_count > 0:
        return {'response':'Estado actualizado', 'status':200}
    else:
        return {'response':'Elemento no encontrado', 'status':200}
    
def saldo(catalog, id_discord):
    collection = db[catalog]
    query = {
        "id_discord": id_discord,
        "aprobado": True
    }
    documentos = list(collection.find(query))
    depositos_total = sum(doc.get("valor_deposito", 0) for doc in documentos)
    costo_total_eventos = sum(doc.get("costo_evento", 0) for doc in documentos)
    saldo_total = depositos_total - costo_total_eventos
    return {'response': saldo_total, 'status': 200}

def estado_torneo(catalog, id_torneo):
    collection = db[catalog]
    torneo = collection.find_one({'id_torneo': id_torneo})
    estado = torneo.get('estado', 'no encontrado')
    return {'response': {"estado": estado}, 'status': 200}

def detalle_torneo(catalog, catalog_torneo, id_torneo):
    collection = db[catalog]
    participantes_torneo = []
    cursor = collection.find({'id_torneo': id_torneo, 'aprobado': True})
    for documento in cursor:
        usuario_discord = documento['usuario_discord']
        id_discord = documento['id_discord']
        participantes_torneo.append({"usuario_discord": usuario_discord, "id_discord": id_discord})
    collection_torneos = db[catalog_torneo]
    torneo = json.loads(json_util.dumps(collection_torneos.find_one({'id_torneo': id_torneo})))
    participantes_torneo = list(participantes_torneo)
    return {'response': {"cantidad_participantes": len(participantes_torneo), "participantes_torneo": participantes_torneo, "torneo": torneo}, 'status': 200}

def detalle_depositos_usuario(catalog, id_discord):
    collection = db[catalog]
    query = {
        "id_discord": id_discord,
        "aprobado": True
    }
    documentos = list(collection.find(query).sort("timestamp", DESCENDING))
    depositos_total = sum(doc.get("valor_deposito", 0) for doc in documentos)
    costo_total_eventos = sum(doc.get("costo_evento", 0) for doc in documentos)
    saldo_total = depositos_total - costo_total_eventos
    depositos = json.loads(json_util.dumps(documentos))
    return {'response': {"depositos": depositos, "saldo": saldo_total}, 'status': 200}

def count_items(catalog):
    collection = db[catalog]
    documents_count = collection.count_documents({})
    return {'response':documents_count, 'status':200}

def upload_items(catalog, items):
    collection = db[catalog]
    log = []
    for item in items:
        item_id = str(uuid.uuid4())
        item['item_id'] = item_id
        item['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        collection.insert_one(item)
        log.append(item)
    toReturn = json.loads(json_util.dumps(log))
    return {'response':toReturn, 'status':200}

def search_items(catalog, attribute, value, output_model):
    collection = db[catalog]
    output_model['_id'] = False
    output_model['item_id'] = True
    output_model['timestamp'] = True
    filter = {}
    filter[attribute] = value
    items = collection.find(filter, output_model)
    items_to_return = json.loads(json_util.dumps(items))
    if (len(items_to_return)>0):
        toReturn = items_to_return
        status = 200
    else:
        toReturn = 'Elemento no encontrado'
        status = 500
    return {'response':toReturn, 'status':status}

def get_item(catalog, item_id, output_model):
    collection = db[catalog]
    output_model['_id'] = False
    output_model['item_id'] = True
    output_model['timestamp'] = True
    filter = {"item_id":item_id}
    items = collection.find(filter, output_model)
    items_to_return = json.loads(json_util.dumps(items))
    if (len(items_to_return)>0):
        toReturn = items_to_return[0]
        status = 200
    else:
        toReturn = 'Elemento no encontrado'
        status = 500
    return {'response':toReturn, 'status':status}

def get_items(catalog, output_model):
    collection = db[catalog]
    output_model['_id'] = False
    output_model['item_id'] = True
    output_model['timestamp'] = True
    items = collection.find({}, output_model)
    items_to_return = json.loads(json_util.dumps(items))
    return {'response':items_to_return, 'status':200}

def update_item(catalog, item_id, item):
    collection = db[catalog]
    filter = {"item_id": item_id}
    prev_items = collection.find(filter)
    previous_items = json.loads(json_util.dumps(prev_items))
    if (len(previous_items) == 0):
        return {'response': 'Elemento no encontrado', 'status':500}
    else:
        item['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        collection.update_one(filter, {'$set':item})
        log = []
        log.append(item)
        toReturn = json.loads(json_util.dumps(log))
        return {'response':toReturn, 'status':200}

def delete_item(catalog, item_id):
    collection = db[catalog]
    filter = {"item_id":item_id}
    items = collection.find(filter, {
        "item_id": True, 
        "_id": False
    })
    items_to_return = json.loads(json_util.dumps(items))
    if (len(items_to_return)>0):
        collection.delete_one(filter)
        toReturn = True
    else:
        toReturn = False
    return toReturn

def make_app():
    urls = [
        ("/", DefaultHandler),
        ("/([^/]+)/([^/]+)", ActionHandler)
    ]
    return Application(urls, debug=True)
    
if __name__ == '__main__':
    app = make_app()
    app.listen(5050)
    IOLoop.instance().start()