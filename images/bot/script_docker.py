import os
import discord
from discord.ext import commands
import datetime
from tournament import definir_enfrentamientos
from image_gen import generar_imagen_campeon, generar_imagen_enfrentamiento, generar_imagen_torneo, reportar_imagen_etapa
from api_manager import APIManager
import jwt
import random
import asyncio
from datetime import datetime
import time
import requests
import base64
import pandas as pd

palabras_clave_saludo = [
    "bot",
    "información",
    "info"
]

app_secret = os.getenv('app_secret')
url_servidor = os.getenv('url_servidor')
TOKEN = os.getenv('discord_token')
url_inscripciones = os.getenv('url_inscripciones')
url_torneo = os.getenv('url_torneo')
manager = APIManager(url_servidor)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

valor_clave_admin = manager.obtener_clave_admin('configuraciones')

torneo_por_defecto_creado = False

def validate_key(key):
    valor_clave_admin = manager.obtener_clave_admin('configuraciones')
    return key == valor_clave_admin

def get_main_config():
    return manager.obtener_main_config('configuraciones')
    
def generate_token(payload):
    return jwt.encode(payload, app_secret, algorithm='HS256')

@bot.event
async def on_ready():
    print("Bot Conectado a discord!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if any(palabra in message.content.lower() for palabra in palabras_clave_saludo):
        await message.channel.send(embed=await describirse())
    await bot.process_commands(message)

@bot.command()
async def prueba_clave(ctx, clave: str):
    if (validate_key(clave)):
        await ctx.send("Autenticación correcta")
    else:
        await ctx.send("Error al Autenticar")

@bot.command()
async def ranking(ctx, clave: str):
    if validate_key(clave):
        torneos = manager.get_torneos()  # Obtener todos los torneos
        participantes = set()
        torneos_ordenados = sorted(torneos, key=lambda x: datetime.strptime(x['fecha'], '%Y-%m-%d'))

        # Diccionario para almacenar puntajes de los jugadores por torneo
        puntajes = {}

        # Recorrer todos los torneos
        for torneo in torneos_ordenados:
            fecha_torneo = torneo['fecha']
            if fecha_torneo not in puntajes:
                puntajes[fecha_torneo] = {}

            # Recorrer las etapas y enfrentamientos
            for etapa in torneo['etapas']:
                for enfrentamiento in etapa['enfrentamientos']:
                    ganador_id = enfrentamiento['ganador']['id_discord']
                    for competidor in enfrentamiento['competidores']:
                        jugador_id = competidor['jugador']['id_discord']
                        jugador_nombre = competidor['jugador']['usuario_discord']
                        
                        # Añadir todos los jugadores a la lista de participantes
                        participantes.add(jugador_nombre)
                        
                        # Inicializar puntaje en 0 si no existe para este torneo
                        if jugador_nombre not in puntajes[fecha_torneo]:
                            puntajes[fecha_torneo][jugador_nombre] = 0

                        # Asignar puntaje basado en si es ganador o perdedor
                        if jugador_id == ganador_id:
                            puntajes[fecha_torneo][jugador_nombre] += 3
                        # Si el jugador pierde, el puntaje sigue en 0 (ya está inicializado en 0)

        # Crear un DataFrame para organizar los datos
        participantes = sorted(participantes)
        df = pd.DataFrame(participantes, columns=['Participantes'])

        # Agregar las columnas para cada torneo con los puntajes de los jugadores
        for fecha_torneo in puntajes:
            columna_puntajes = []
            for participante in participantes:
                columna_puntajes.append(puntajes[fecha_torneo].get(participante, 0))
            df[fecha_torneo] = columna_puntajes

        # Crear el archivo CSV
        archivo_csv = './ranking.csv'
        df.to_csv(archivo_csv, index=False)

        # Enviar el archivo a Discord
        await ctx.send(file=discord.File(archivo_csv))
        
        # Eliminar el archivo después de enviarlo
        if os.path.exists(archivo_csv):
            os.remove(archivo_csv)
    else:
        await ctx.send("Error al Autenticar")

@bot.command()
async def crear_torneo(ctx, pais: str, hora: str, juego: str, plataforma: str, channel: str, alcance: str, modalidad: str, costo: str, clave: str):
    if (validate_key(clave)):
        cuenta = manager.count_items('torneos')
        torneo = {
            "id_torneo": str(cuenta + 1),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "pais": pais,
            "hora": hora,
            "juego": juego,
            "alcance": alcance,
            "plataforma": plataforma,
            "costo": float(costo),
            "estado": "creado",
            "channel": channel,
            "modalidad": modalidad,
            "etapas": [],
            "observacion": False
        }
        manager.upload_items('torneos', [torneo])
        output_filename = f"torneo_{cuenta + 1}.png"
        generar_imagen_torneo(torneo["fecha"], torneo["juego"], torneo["pais"], torneo["plataforma"], torneo["modalidad"], torneo["hora"], cuenta + 1, alcance, costo, output_filename)
        general_channel = discord.utils.get(ctx.guild.channels, name=channel)
        if general_channel:
            with open(output_filename, "rb") as file:
                await general_channel.send(f"Torneo creado satisfactoriamente con id: {cuenta + 1}", file=discord.File(file))
        os.remove(output_filename)
    else:
        await ctx.send("Error al Autenticar")

async def comando_crear_torneo(pais: str, hora: str, juego: str, plataforma: str, channel: str, alcance: str, modalidad: str, costo: float, clave: str):
    if (validate_key(clave)):
        cuenta = manager.count_items('torneos')
        torneo = {
            "id_torneo": str(cuenta + 1),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "pais": pais,
            "hora": hora,
            "juego": juego,
            "plataforma": plataforma,
            "alcance": alcance,
            "costo": float(costo),
            "estado": "creado",
            "channel": channel,
            "modalidad": modalidad,
            "etapas": [],
            "observacion": False
        }
        manager.upload_items('torneos', [torneo])
        output_filename = f"torneo_{cuenta + 1}.png"
        generar_imagen_torneo(torneo["fecha"], torneo["juego"], torneo["pais"], torneo["plataforma"], torneo["modalidad"], torneo["hora"], cuenta + 1, alcance, costo, output_filename)
        guild = discord.utils.get(bot.guilds)
        general_channel = discord.utils.get(guild.channels, name=channel)
        if general_channel:
            with open(output_filename, "rb") as file:
                await general_channel.send(f"Torneo creado satisfactoriamente con id: {cuenta + 1}", file=discord.File(file))
        os.remove(output_filename)

async def watchdog():
    default_tournament_day_of_week = int(get_main_config()[0]["default_tournament_day_of_week"])
    default_tournament_hour = int(get_main_config()[0]["default_tournament_hour"])
    default_tournament_minute = int(get_main_config()[0]["default_tournament_minute"])
    default_tournament_country = get_main_config()[0]["default_tournament_country"]
    default_tournament_discord_channel = get_main_config()[0]["default_tournament_discord_channel"]
    default_tournament_game = get_main_config()[0]["default_tournament_game"]
    default_tournament_platform = get_main_config()[0]["default_tournament_platform"]
    default_tournament_target = get_main_config()[0]["default_tournament_target"]
    default_tournament_mode = get_main_config()[0]["default_tournament_mode"]
    default_tournament_price = float(get_main_config()[0]["default_tournament_price"])
    hora_minuto = f"{default_tournament_hour:02}:{default_tournament_minute:02}"
    global torneo_por_defecto_creado
    while True:
        now = datetime.now()
        current_day_of_week = now.weekday()
        current_hour = now.hour
        current_minute = now.minute
        if (current_day_of_week == default_tournament_day_of_week and
            current_hour == default_tournament_hour and
            current_minute == default_tournament_minute):
            if not torneo_por_defecto_creado:
                await comando_crear_torneo(default_tournament_country, hora_minuto, default_tournament_game, default_tournament_platform, default_tournament_discord_channel, default_tournament_target, default_tournament_mode, default_tournament_price, valor_clave_admin)
                torneo_por_defecto_creado = True
        else:
            torneo_por_defecto_creado = False
        await asyncio.sleep(5)

@bot.command()
async def registrar(ctx, torneo_id):
    author = ctx.author
    estado_torneo_response = manager.estado_torneo('torneos', torneo_id)
    estado_torneo = estado_torneo_response['response'].get('estado')
    if estado_torneo == 'creado':
        payload = {"usuario_discord": author.name, "id_discord": str(author.id), "id_torneo": torneo_id}
        token_data = generate_token(payload)
        mensaje = f"{url_inscripciones}?token={token_data}"
        await author.send("¡Claro! Para inscribirte, por favor accede a este enlace y completa tus datos.")
        await author.send(mensaje)
    else:
        await ctx.send("Lo siento, el torneo no admite inscripciones en este momento o no se encontró el torneo.")

def ya_ha_esperado(jugador, etapas):
    for etapa in etapas:
        for enfrentamiento in etapa.get('enfrentamientos', []):
            if enfrentamiento.get('codigo_enfrentamiento', '').startswith('automatico') and enfrentamiento.get('ganador'):
                if enfrentamiento['ganador'].get('usuario_discord') == jugador.get('usuario_discord'):
                    return True
    return False

@bot.command()
async def iniciar_torneo(ctx, torneo_id, fecha_enfrentamiento: str, hora_enfrentamiento: str, clave: str):
    fecha = datetime.strptime(fecha_enfrentamiento, '%Y-%m-%d')
    hora = datetime.strptime(hora_enfrentamiento, '%H:%M')
    fecha_hora_enfrentamiento = fecha.replace(hour=hora.hour, minute=hora.minute)
    fecha_hora_formateada = fecha_hora_enfrentamiento.strftime("%Y-%m-%d %H:%M:%S")
    if validate_key(clave):
        estado_torneo_response = manager.estado_torneo('torneos', torneo_id)
        estado_torneo = estado_torneo_response['response'].get('estado')
        if estado_torneo == 'creado':
            detalle_torneo_response = manager.detalle_torneo('depositos', 'torneos', torneo_id)
            torneo = detalle_torneo_response['response']['torneo']
            participantes = detalle_torneo_response['response']['participantes_torneo']
            competidor_espera = None
            intentos = 0
            max_intentos = 5
            while intentos < max_intentos:
                participantes_barajados = participantes[:]
                random.shuffle(participantes_barajados)
                if len(participantes_barajados) % 2 != 0:
                    posible_espera = participantes_barajados.pop()
                    if not ya_ha_esperado(posible_espera, torneo.get('etapas', [])):
                        competidor_espera = posible_espera
                        participantes = participantes_barajados
                        await ctx.send(f"El jugador {competidor_espera['usuario_discord']} pasa automáticamente a la siguiente ronda.")
                        break
                else:
                    participantes = participantes_barajados
                    break
                intentos += 1
            enfrentamientos = definir_enfrentamientos(participantes, fecha_hora_formateada, torneo_id, 0)
            if competidor_espera:
                enfrentamientos.append({
                    "competidores": [{'jugador':competidor_espera, 'puntaje': 1, 'puntaje_contendiente': 0}, {'jugador':competidor_espera, 'puntaje': 0, 'puntaje_contendiente': 1}],
                    "ganador": competidor_espera,
                    "fecha_enfrentamiento": fecha_hora_formateada,
                    "codigo_enfrentamiento": f"automatico_1"
                })
            etapas = [ { "index": 1, "enfrentamientos": enfrentamientos} ]
            torneo['etapas'] = etapas
            torneo['estado']='iniciado'
            torneo.pop('_id', None)
            manager.update_item('torneos', torneo['item_id'], torneo)
            await enviar_mensaje_directo_enfrentamientos(enfrentamientos, torneo['id_torneo'], torneo['juego'])
            await ctx.send(f"El torneo con ID {torneo_id} ha sido iniciado satisfactoriamente.")
            id_torneo=torneo['id_torneo']
            detalle = manager.detalle_torneo('depositos', 'torneos', id_torneo)
            datos_torneo = detalle['response']['torneo']
            if datos_torneo['etapas']:
                ultima_etapa = datos_torneo['etapas'][-1]
                enfrentamientos = ultima_etapa.get('enfrentamientos', [])
                mensaje = f"Detalles del Torneo (ID: {id_torneo}) - Etapa ({ultima_etapa['index']}):\n"
                mensaje += "```\n"
                mensaje += f"{'Encuentro':<50} {'Fecha':<20}\n"
                for enfrentamiento in enfrentamientos:
                    competidores = enfrentamiento['competidores']
                    fecha = enfrentamiento['fecha_enfrentamiento']
                    encuentro = ""
                    if enfrentamiento['codigo_enfrentamiento'] == 'automatico_1':
                        jugador = competidores[0]['jugador']['usuario_discord']
                        puntaje = competidor['puntaje'] if competidor['puntaje'] is not None else '-'
                        encuentro += f"{jugador}(EN ESPERA)"
                    else:
                        for competidor in competidores:
                            jugador = competidor['jugador']['usuario_discord']
                            puntaje = competidor['puntaje'] if competidor['puntaje'] is not None else '-'
                            if encuentro == "":
                                encuentro += f"{jugador}({puntaje})"
                            else:
                                encuentro += f" vs {jugador}({puntaje})"
                    mensaje += f"{encuentro:<50} {fecha:<20} \n"
                mensaje += "```"
                torneo_channel = discord.utils.get(ctx.guild.channels, name=datos_torneo['channel'])
                if torneo_channel:
                    await torneo_channel.send(mensaje)
                    mensaje_previo_url = "Para más información visita la siguiente dirección:"
                    await torneo_channel.send(mensaje_previo_url)
                    mensaje_url = f"{url_torneo}?id_torneo={id_torneo}"
                    await torneo_channel.send(mensaje_url)
        else:
            await ctx.send("El torneo se encuentra iniciado o ha finalizado.")
    else:
        await ctx.send("Error al autenticar.")

async def enviar_mensaje_directo_enfrentamientos(enfrentamientos, id_torneo, juego):
    for i, enfrentamiento in enumerate(enfrentamientos, start=1):
        competidores = enfrentamiento['competidores']
        jugador_1, jugador_2 = competidores[0]['jugador'], competidores[1]['jugador']
        nombre_imagen = f"imagen_torneo_partida_{i}.png"
        generar_imagen_enfrentamiento(juego, jugador_1['usuario_discord'], jugador_2['usuario_discord'], enfrentamiento['fecha_enfrentamiento'], "Código: " + enfrentamiento['codigo_enfrentamiento'], nombre_imagen)
        for competidor in competidores:
            jugador = competidor
            user = await bot.fetch_user(int(jugador['jugador']['id_discord']))
            await user.send(f'¡Tienes una partida de torneo!, Torneo con ID {id_torneo}', file=discord.File(nombre_imagen))
        os.remove(nombre_imagen)       

@bot.command()
async def torneo_next(ctx, torneo_id, fecha_enfrentamiento: str, hora_enfrentamiento: str, clave: str):
    fecha = datetime.strptime(fecha_enfrentamiento, '%Y-%m-%d')
    hora = datetime.strptime(hora_enfrentamiento, '%H:%M')
    fecha_hora_enfrentamiento = fecha.replace(hour=hora.hour, minute=hora.minute)
    fecha_hora_formateada = fecha_hora_enfrentamiento.strftime("%Y-%m-%d %H:%M:%S")
    if validate_key(clave):
        estado_torneo_response = manager.estado_torneo('torneos', torneo_id)
        estado_torneo = estado_torneo_response['response'].get('estado')
        if estado_torneo == 'iniciado':
            detalle_torneo_response = manager.detalle_torneo('depositos', 'torneos', torneo_id)
            torneo = detalle_torneo_response['response']['torneo']
            etapas = torneo.get('etapas', [])
            if etapas:
                ultima_etapa = etapas[-1]
                enfrentamientos_ultima_etapa = ultima_etapa.get('enfrentamientos', [])
                if all(enfrentamiento.get('ganador') for enfrentamiento in enfrentamientos_ultima_etapa):
                    if len(enfrentamientos_ultima_etapa) == 1:
                        ganador = enfrentamientos_ultima_etapa[0]['ganador']
                        resultado = manager.actualizar_estado_torneo('torneos', torneo_id, 'cerrado')
                        if resultado['status'] == 200:
                            torneo_channel = discord.utils.get(ctx.guild.channels, name=torneo['channel'])
                            if torneo_channel:
                                await torneo_channel.send(f"¡El torneo ha concluido! El ganador del torneo con ID {torneo_id} es: {ganador.get('usuario_discord')}")
                            return
                        else:
                            await ctx.send("Ocurrió un error al intentar cerrar el torneo.")
                            return
                    else:
                        participantes_ganadores = [enfrentamiento['ganador'] for enfrentamiento in enfrentamientos_ultima_etapa]
                        random.shuffle(participantes_ganadores)
                        nueva_etapa_index = max(etapa['index'] for etapa in etapas) + 1
                        competidor_espera = None
                        intentos = 0
                        max_intentos = 5
                        while intentos < max_intentos:
                            participantes_barajados = participantes_ganadores[:]
                            random.shuffle(participantes_barajados)
                            if len(participantes_barajados) % 2 != 0:
                                posible_espera = participantes_barajados.pop()
                                if not ya_ha_esperado(posible_espera, torneo.get('etapas', [])):
                                    competidor_espera = posible_espera
                                    participantes_ganadores = participantes_barajados
                                    await ctx.send(f"El jugador {competidor_espera['usuario_discord']} pasa automáticamente a la siguiente ronda.")
                                    break
                            else:
                                participantes_ganadores = participantes_barajados
                                break
                            intentos += 1
                        nueva_etapa_enfrentamientos = definir_enfrentamientos(participantes_ganadores, fecha_hora_formateada, torneo_id, len(etapas))
                        if competidor_espera:
                            nueva_etapa_enfrentamientos.append({
                                "competidores": [{'jugador':competidor_espera, 'puntaje': 1, 'puntaje_contendiente': 0}, {'jugador':competidor_espera, 'puntaje': 0, 'puntaje_contendiente': 1}],
                                "ganador": competidor_espera,
                                "fecha_enfrentamiento": fecha_hora_formateada,
                                "codigo_enfrentamiento": f"automatico_{nueva_etapa_index}"
                            })
                        etapas.append({"index": nueva_etapa_index, "enfrentamientos": nueva_etapa_enfrentamientos})
                        torneo['etapas'] = etapas
                        torneo.pop('_id', None)
                        manager.update_item('torneos', torneo['item_id'], torneo)
                        await enviar_mensaje_directo_enfrentamientos(nueva_etapa_enfrentamientos, torneo['id_torneo'], torneo['juego'])
                        await ctx.send(f"El torneo con ID {torneo_id} continua a su siguiente etapa satisfactoriamente.")
                        id_torneo=torneo['id_torneo']
                        detalle = manager.detalle_torneo('depositos', 'torneos', id_torneo)
                        datos_torneo = detalle['response']['torneo']
                        if datos_torneo['etapas']:
                            ultima_etapa = datos_torneo['etapas'][-1]
                            enfrentamientos = ultima_etapa.get('enfrentamientos', [])
                            mensaje = f"Detalles del Torneo (ID: {id_torneo}) - Etapa ({ultima_etapa['index']}):\n"
                            mensaje += "```\n"
                            mensaje += f"{'Encuentro':<50} {'Fecha':<20}\n"
                            for enfrentamiento in enfrentamientos:
                                competidores = enfrentamiento['competidores']
                                fecha = enfrentamiento['fecha_enfrentamiento']
                                encuentro = ""
                                if enfrentamiento['codigo_enfrentamiento'] == f'automatico_{nueva_etapa_index}':
                                    jugador = competidores[0]['jugador']['usuario_discord']
                                    puntaje = competidor['puntaje'] if competidor['puntaje'] is not None else '-'
                                    encuentro += f"{jugador}(EN ESPERA)"
                                else:
                                    for competidor in competidores:
                                        jugador = competidor['jugador']['usuario_discord']
                                        puntaje = competidor['puntaje'] if competidor['puntaje'] is not None else '-'
                                        if encuentro == "":
                                            encuentro += f"{jugador}({puntaje})"
                                        else:
                                            encuentro += f" vs {jugador}({puntaje})"
                                mensaje += f"{encuentro:<50} {fecha:<20} \n"
                            mensaje += "```"
                            torneo_channel = discord.utils.get(ctx.guild.channels, name=datos_torneo['channel'])
                            if torneo_channel:
                                await torneo_channel.send(mensaje)            
                                mensaje_previo_url = "Para más información visita la siguiente dirección:"
                                await torneo_channel.send(mensaje_previo_url)
                                mensaje_url = f"{url_torneo}?id_torneo={id_torneo}"
                                await torneo_channel.send(mensaje_url)
                        return
                else:
                    await ctx.send("No se pueden generar nuevas etapas, algunos enfrentamientos de la última etapa aún no tienen ganador.")
                    return
            else:
                await ctx.send("El torneo no tiene ninguna etapa creada.")
                return
        else:
            await ctx.send("El torneo no está en curso.")
            return    
    else:
        await ctx.send("Error al autenticar.")
        return

@bot.command()
async def partido(ctx, id_torneo, codigo_enfrentamiento, puntaje_propio, puntaje_contendiente):
    puntaje_contendiente = int(puntaje_contendiente)
    puntaje_propio = int(puntaje_propio)
    detalle_torneo_response = manager.detalle_torneo('depositos', 'torneos', id_torneo)
    observacion = False
    if 'response' in detalle_torneo_response:
        torneo = detalle_torneo_response['response']['torneo']
        for etapa in torneo['etapas']:
            for enfrentamiento in etapa['enfrentamientos']:
                if enfrentamiento['codigo_enfrentamiento'] == codigo_enfrentamiento:
                    for competidor in enfrentamiento['competidores']:
                        if (str(competidor['jugador']['id_discord']) == str(ctx.author.id)) and (str(competidor['jugador']['usuario_discord']) == str(ctx.author.name)):
                            jugador_propio = competidor
                        else:
                            jugador_otro = competidor
                    if enfrentamiento['ganador'] is not None:
                        await ctx.send("Este enfrentamiento ya se encuentra definido.")
                        return
                    jugador_propio['puntaje'] = puntaje_propio
                    jugador_propio['puntaje_contendiente'] = puntaje_contendiente
                    if jugador_otro['puntaje'] is not None and jugador_otro['puntaje_contendiente'] is not None:
                        if puntaje_propio != jugador_otro['puntaje_contendiente'] or puntaje_contendiente != jugador_otro['puntaje']:
                            torneo['observacion'] = True
                            observacion = True
                        else:
                            torneo['observacion'] = False
                            if puntaje_propio > puntaje_contendiente:
                                enfrentamiento['ganador'] = jugador_propio['jugador']
                            else:
                                enfrentamiento['ganador'] = jugador_otro['jugador']
                    else:
                        torneo['observacion'] = False
                    torneo.pop('_id', None)
                    manager.update_item('torneos', torneo['item_id'], torneo)
                    await ctx.send(f"Puntaje actualizado para {ctx.author.name} en el enfrentamiento {codigo_enfrentamiento}.")
                    if observacion:
                        for competidor in enfrentamiento['competidores']:
                            jugador = competidor
                            user = await bot.fetch_user(int(jugador['jugador']['id_discord']))
                            await user.send("Hay un desacuerdo en los valores reportados para el enfrentamiento. Por favor, envía nuevamente tus puntajes.")
                    else:
                        if jugador_otro['puntaje'] is not None and jugador_otro['puntaje_contendiente'] is not None:
                            nombre_imagen = enfrentamiento['codigo_enfrentamiento'] + '.png'
                            reportar_imagen_etapa(etapa['index'], enfrentamiento, nombre_imagen)
                            for competidor in enfrentamiento['competidores']:
                                jugador = competidor
                                user = await bot.fetch_user(int(jugador['jugador']['id_discord']))
                                await user.send(f"Resultado del enfrentamiento {enfrentamiento['codigo_enfrentamiento']}:", file=discord.File(nombre_imagen))
                            torneo_channel = discord.utils.get(ctx.guild.channels, name=torneo['channel'])
                            if torneo_channel:
                                await torneo_channel.send(f"Resultado del enfrentamiento {enfrentamiento['codigo_enfrentamiento']}:", file=discord.File(nombre_imagen))
                            os.remove(nombre_imagen)  
                    return
    await ctx.send("No se encontró el torneo o el enfrentamiento especificado.")

@bot.command()
async def partido_adm(ctx, id_torneo, codigo_enfrentamiento, usuario_discord_a, puntaje_jugador_a, puntaje_jugador_b, clave):
    if (validate_key(str(clave))):
        puntaje_jugador_a = int(puntaje_jugador_a)
        puntaje_jugador_b = int(puntaje_jugador_b)
        detalle_torneo_response = manager.detalle_torneo('depositos', 'torneos', id_torneo)
        if 'response' in detalle_torneo_response:
            torneo = detalle_torneo_response['response']['torneo']
            for etapa in torneo['etapas']:
                for enfrentamiento in etapa['enfrentamientos']:
                    if enfrentamiento['codigo_enfrentamiento'] == codigo_enfrentamiento:
                        for competidor in enfrentamiento['competidores']:
                            if (str(competidor['jugador']['usuario_discord']) == usuario_discord_a):
                                jugador_a = competidor
                            else:
                                jugador_b = competidor
                        if enfrentamiento['ganador'] is not None:
                            await ctx.send("Este enfrentamiento ya se encuentra definido.")
                            return
                        jugador_a['puntaje'] = puntaje_jugador_a
                        jugador_a['puntaje_contendiente'] = puntaje_jugador_b
                        jugador_b['puntaje'] = puntaje_jugador_b
                        jugador_b['puntaje_contendiente'] = puntaje_jugador_a
                        torneo['observacion'] = False
                        if puntaje_jugador_a > puntaje_jugador_b:
                            enfrentamiento['ganador'] = jugador_a['jugador']
                        else:
                            enfrentamiento['ganador'] = jugador_b['jugador']
                        torneo.pop('_id', None)
                        manager.update_item('torneos', torneo['item_id'], torneo)
                        await ctx.send(f"Puntaje actualizado para {ctx.author.name} en el enfrentamiento {codigo_enfrentamiento}.")
                        nombre_imagen = enfrentamiento['codigo_enfrentamiento'] + '.png'
                        reportar_imagen_etapa(etapa['index'], enfrentamiento, nombre_imagen)
                        for competidor in enfrentamiento['competidores']:
                            jugador = competidor
                            user = await bot.fetch_user(int(jugador['jugador']['id_discord']))
                            await user.send(f"Resultado del enfrentamiento {enfrentamiento['codigo_enfrentamiento']}:", file=discord.File(nombre_imagen))
                        torneo_channel = discord.utils.get(ctx.guild.channels, name=torneo['channel'])
                        if torneo_channel:
                            await torneo_channel.send(f"Resultado del enfrentamiento {enfrentamiento['codigo_enfrentamiento']}:", file=discord.File(nombre_imagen))
                        os.remove(nombre_imagen)      
                        return
        await ctx.send("No se encontró el torneo o el enfrentamiento especificado.")

@bot.command()
async def reportar_etapa(ctx, id_torneo, clave):
    if (validate_key(str(clave))):
        detalle = manager.detalle_torneo('depositos', 'torneos', id_torneo)
        datos_torneo = detalle['response']['torneo']
        if datos_torneo['etapas']:
            ultima_etapa = datos_torneo['etapas'][-1]
            enfrentamientos = ultima_etapa.get('enfrentamientos', [])
            mensaje = f"Detalles del Torneo (ID: {id_torneo}) - Etapa ({ultima_etapa['index']}):\n"
            mensaje += "```\n"
            mensaje += f"{'Encuentro':<50} {'Fecha':<20}\n"
            for enfrentamiento in enfrentamientos:
                competidores = enfrentamiento['competidores']
                fecha = enfrentamiento['fecha_enfrentamiento']
                encuentro = ""
                if enfrentamiento['codigo_enfrentamiento'] == 'automatico':
                    jugador = competidores[0]['jugador']['usuario_discord']
                    puntaje = competidor['puntaje'] if competidor['puntaje'] is not None else '-'
                    encuentro += f"{jugador}(EN ESPERA)"
                else:
                    for competidor in competidores:
                        jugador = competidor['jugador']['usuario_discord']
                        puntaje = competidor['puntaje'] if competidor['puntaje'] is not None else '-'
                        if encuentro == "":
                            encuentro += f"{jugador}({puntaje})"
                        else:
                            encuentro += f" vs {jugador}({puntaje})"
                mensaje += f"{encuentro:<50} {fecha:<20} \n"
            mensaje += "```"
            torneo_channel = discord.utils.get(ctx.guild.channels, name=datos_torneo['channel'])
            if torneo_channel:
                await torneo_channel.send(mensaje)
            
@bot.command()
async def torneo_status(ctx, id_torneo):
    detalle = manager.detalle_torneo('depositos', 'torneos', id_torneo)
    cantidad_participantes = detalle['response']['cantidad_participantes']
    datos_torneo = detalle['response']['torneo']
    costo_participacion = f"{datos_torneo['costo']:.2f}"
    mensaje = f"Detalles del Torneo (ID: {id_torneo}):\n"
    mensaje += f"```\n"
    mensaje += f"{'Estado':<30}{datos_torneo['estado'].upper():<20}\n"
    mensaje += f"{'Pais':<30}{datos_torneo['pais']:<20}\n"
    mensaje += f"{'Juego':<30}{datos_torneo['juego']:<20}\n"
    mensaje += f"{'Plataforma':<30}{datos_torneo['plataforma']:<20}\n"
    mensaje += f"{'Alcance':<30}{datos_torneo['alcance']:<20}\n"
    mensaje += f"{'Modalidad':<30}{datos_torneo['modalidad']:<20}\n"
    mensaje += f"{'Costo de Participación':<30}{costo_participacion:<20}\n"
    mensaje += f"{'No. Participantes':<30}{cantidad_participantes:<20}\n"
    if datos_torneo['etapas']:
        max_index_etapas = max(etapa['index'] for etapa in datos_torneo['etapas'])
        estado_etapa = "Activa" if any(enfrentamiento['ganador'] is None for etapa in datos_torneo['etapas'] for enfrentamiento in etapa['enfrentamientos']) else "Completa"
        mensaje += f"{'Etapa en Curso':<30}{max_index_etapas:<20}\n"
        mensaje += f"{'Estado Etapa en Curso':<30}{estado_etapa:<20}\n"
    mensaje += f"{'Observaciones':<30}{'Torneo con Observaciones' if datos_torneo.get('observacion', False) else 'Ninguna'}\n"
    if datos_torneo['estado'].upper() == 'CERRADO':
        ganador_torneo = None
        if datos_torneo['etapas']:
            ultima_etapa = datos_torneo['etapas'][-1]
            enfrentamientos_ultima_etapa = ultima_etapa.get('enfrentamientos', [])
            if all(enfrentamiento.get('ganador') for enfrentamiento in enfrentamientos_ultima_etapa):
                if len(enfrentamientos_ultima_etapa) == 1:
                    ganador_torneo = enfrentamientos_ultima_etapa[0]['ganador']['usuario_discord']
        mensaje += f"{'Ganador del Torneo':<30}{ganador_torneo if ganador_torneo else 'Aún no determinado'}\n"
    mensaje += f"```"
    await ctx.send(mensaje)
    mensaje_previo_url = "Para más información visita la siguiente dirección:"
    await ctx.send(mensaje_previo_url)
    mensaje_url = f"{url_torneo}?id_torneo={id_torneo}"
    await ctx.send(mensaje_url)

@bot.command()
async def mi_status(ctx):
    id_usuario_discord = str(ctx.author.id)
    detalle = manager.detalle_depositos_usuario('depositos', id_usuario_discord)
    saldo = "{:.2f}".format(detalle['response']['saldo'])
    ultimos_depositos = detalle['response']['depositos']
    mensaje_saludo = f"Saludos {ctx.author.name}, tu saldo es: {saldo}"
    await ctx.send(mensaje_saludo)
    tabla_depositos = "```\n"
    tabla_depositos += f"{'Fecha':<20} {'Torneo':<15} {'Valor Depósito':<20} {'Costo Evento':<20}\n"
    for deposito in ultimos_depositos[:10]:
        fecha_deposito = deposito['timestamp']
        id_torneo = deposito['id_torneo']
        cantidad_deposito = "{:.2f}".format(deposito['valor_deposito'])
        costo_evento = "{:.2f}".format(deposito['costo_evento'])
        tabla_depositos += f"{fecha_deposito:<20} {id_torneo:<15} {cantidad_deposito:<20} {costo_evento:<20}\n"
    tabla_depositos += "```"
    await ctx.send(tabla_depositos)

@bot.command()
async def mi_status_completo(ctx):
    id_usuario_discord = str(ctx.author.id)
    detalle = manager.detalle_depositos_usuario('depositos', id_usuario_discord)
    saldo = "{:.2f}".format(detalle['response']['saldo'])
    ultimos_depositos = detalle['response']['depositos']
    mensaje_saludo = f"Saludos {ctx.author.name}, tu saldo es: {saldo}"
    await ctx.send(mensaje_saludo)
    tabla_depositos = "```\n"
    tabla_depositos += f"{'Fecha':<20} {'Torneo':<15} {'Valor Depósito':<20} {'Costo Evento':<20}\n"
    for deposito in ultimos_depositos[:10]:
        fecha_deposito = deposito['timestamp']
        id_torneo = deposito['id_torneo']
        cantidad_deposito = "{:.2f}".format(deposito['valor_deposito'])
        costo_evento = "{:.2f}".format(deposito['costo_evento'])
        tabla_depositos += f"{fecha_deposito:<20} {id_torneo:<15} {cantidad_deposito:<20} {costo_evento:<20}\n"
    tabla_depositos += "```"
    await ctx.send(tabla_depositos)

@bot.command()
async def info(ctx):
    await ctx.send(embed=await describirse()) 

@bot.command()
async def tarjeta_campeon(ctx, torneo_id, clave):
    if validate_key(clave):
        estado_torneo_response = manager.estado_torneo('torneos', torneo_id)
        estado_torneo = estado_torneo_response['response'].get('estado')
        if estado_torneo == 'cerrado':
            detalle_torneo_response = manager.detalle_torneo('depositos', 'torneos', torneo_id)
            torneo = detalle_torneo_response['response']['torneo']
            etapas = torneo.get('etapas', [])
            ultima_etapa = etapas[-1]
            enfrentamientos_ultima_etapa = ultima_etapa.get('enfrentamientos', [])
            ganador = enfrentamientos_ultima_etapa[0]['ganador']
            user = await bot.fetch_user(ganador['id_discord'])
            name = user.name
            avatar_url = user.avatar.url
            avatar_base64 = get_avatar_base64(avatar_url)
            nombre_imagen_winner_card = ganador['id_discord']  + '_' + torneo_id + '.png'
            generar_imagen_campeon(avatar_base64, name, torneo, nombre_imagen_winner_card)
            torneo_channel = discord.utils.get(ctx.guild.channels, name=torneo['channel'])
            if torneo_channel:
                await torneo_channel.send(f"Felicidades a {ganador['usuario_discord']}, campeón del torneo {torneo_id}.", file=discord.File(nombre_imagen_winner_card))
            os.remove(nombre_imagen_winner_card)

async def describirse():
    embed = discord.Embed(
        title="Comandos disponibles:",
        description="Aquí están los comandos disponibles y su descripción:",
        color=discord.Color.blue()
    )

    admin_commands = [
        {
            "name": "!crear_torneo <pais> <hora_inicio hora:minuto> <juego> <plataforma> <canal> <alcance> <modalidad> <costo> <clave>",
            "value": "Crea un nuevo torneo. Alcance se utiliza para definir si el torneo será individual o por equipos."
        },
        {
            "name": "!iniciar_torneo <torneo_id> <fecha_enfrentamiento año-mes-dia> <hora_enfrentamiento hora:minutos> <clave>",
            "value": "Solo Administradores, Inicia el torneo especificado con la fecha y hora de los enfrentamientos."
        },
        {
            "name": "!torneo_next <torneo_id> <fecha_enfrentamiento año-mes-dia> <hora_enfrentamiento hora:minutos> <clave>",
            "value": "Solo Administradores, Avanza el torneo especificado a la siguiente etapa con la fecha y hora de los enfrentamientos."
        },
        {
            "name": "!partido_adm <id_torneo> <codigo_enfrentamiento> <usuario_discord_a> <puntaje_jugador_a> <puntaje_jugador_b> <clave>",
            "value": "Solo Administradores, Utiliza este comando para reportar el resultado de un enfrentamiento donde los jugadores no han llegado a un acuerdo."
        },
        {
            "name": "!reportar_etapa <id_torneo> <clave>",
            "value": "Solo Administradores, Envia los detalles de la última etapa de un torneo en el canal del torneo de discord."
        },
        {
            "name": "!tarjeta_campeon <id_torneo> <clave>",
            "value": "Solo Administradores, Envia la tarjeta de campeón en el canal del torneo de discord."
        }
    ]

    player_commands = [
        {
            "name": "!registrar <torneo_id>",
            "value": "Inscribe al usuario al torneo especificado."
        },
        {
            "name": "!partido <id_torneo> <codigo_enfrentamiento> <puntaje_propio> <puntaje_contendiente>",
            "value": "Utiliza este comando para reportar el resultado de un enfrentamiento."
        }
    ]

    general_info_commands = [
        {
            "name": "!torneo_status <id_torneo>",
            "value": "Muestra el estado y detalles de un torneo."
        },
        {
            "name": "!mi_status",
            "value": "Muestra el saldo y los últimos depósitos de un usuario."
        },
        {
            "name": "!mi_status_completo",
            "value": "Muestra el saldo y todos los depósitos de un usuario."
        }
    ]

    embed.add_field(name="------ ADMINISTRADORES ------", value="\u200b", inline=False)
    for command in admin_commands:
        embed.add_field(name=command["name"], value=command["value"], inline=False)

    embed.add_field(name="------ JUGADORES ------", value="\u200b", inline=False)
    for command in player_commands:
        embed.add_field(name=command["name"], value=command["value"], inline=False)

    embed.add_field(name="------ INFORMACIÓN GENERAL ------", value="\u200b", inline=False)
    for command in general_info_commands:
        embed.add_field(name=command["name"], value=command["value"], inline=False)

    return embed

def get_avatar_base64(avatar_url):
    response = requests.get(avatar_url)
    if response.status_code == 200:
        img_base64 = base64.b64encode(response.content).decode('utf-8')
        return img_base64
    return None

async def main():
    async with bot:
        bot.loop.create_task(watchdog())
        await bot.start(TOKEN)

asyncio.run(main())
