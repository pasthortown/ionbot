from PIL import Image, ImageDraw, ImageFont, ImageOps
import datetime
import base64
from io import BytesIO

def escalar_texto_para_ajustar_ancho(texto, max_ancho, fuente):
    fuente_tamano = fuente.getsize(texto)
    if fuente_tamano[0] <= max_ancho:
        return fuente
    else:
        nuevo_tamano = int(max_ancho / fuente_tamano[0] * fuente.size)
        return ImageFont.truetype(fuente.path, nuevo_tamano)

def generar_imagen_enfrentamiento(juego, jugador_a, jugador_b, fecha_texto, codigo_enfrentamiento, output_filename):
    max_ancho_texto_jugador = 300
    fondo = Image.open(f"imagenes/{juego.lower()}_enfrentamiento_fondo.png")
    vs_imagen = Image.open("imagenes/vs.png")
    vs_imagen = vs_imagen.resize((300, 300))
    draw = ImageDraw.Draw(fondo)    
    posicion_vs = ((fondo.width - vs_imagen.width) // 2, (fondo.height - vs_imagen.height) // 2)
    fuente_50 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=30)
    fuente_30 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=20)
    fuente_50_jugador_a = escalar_texto_para_ajustar_ancho(jugador_a, max_ancho_texto_jugador, fuente_50)
    fuente_50_jugador_b = escalar_texto_para_ajustar_ancho(jugador_b, max_ancho_texto_jugador, fuente_50)
    ancho_jugador_a, alto_jugador_a = draw.textsize(jugador_a, font=fuente_50_jugador_a)
    ancho_jugador_b, alto_jugador_b = draw.textsize(jugador_b, font=fuente_50_jugador_b)
    ancho_fecha, alto_fecha = draw.textsize(fecha_texto, font=fuente_30)
    ancho_codigo, alto_codigo = draw.textsize(codigo_enfrentamiento, font=fuente_30)
    posicion_jugador_a = (50, 75)
    posicion_jugador_b = (fondo.width - ancho_jugador_b - 50, 275)
    posicion_fecha = ((fondo.width - ancho_fecha) // 2, fondo.height - 50)
    posicion_codigo = (fondo.width - ancho_codigo - 25, 25)
    fondo.paste(vs_imagen, posicion_vs, vs_imagen)
    draw.text(posicion_jugador_a, jugador_a, fill="white", font=fuente_50_jugador_a)
    draw.text(posicion_jugador_b, jugador_b, fill="white", font=fuente_50_jugador_b)
    draw.text(posicion_codigo, codigo_enfrentamiento, fill="white", font=fuente_30)
    draw.text(posicion_fecha, fecha_texto, fill="white", font=fuente_30)
    fondo.save(output_filename)
    fondo.close()
    vs_imagen.close()

def generar_imagen_campeon(player_avatar_base64, player_name, torneo, nombre_imagen_winner_card):
    juego = torneo['juego']
    pais = torneo['pais']
    fecha = torneo['fecha']
    plataforma = torneo['plataforma']
    alcance = torneo['alcance']
    id_torneo = torneo['id_torneo']

    fondo = Image.open("imagenes/tournament.jpg")
    draw = ImageDraw.Draw(fondo)

    fuente_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=150)
    fuente_secondary = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=60)
    fuente_info = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=30)

    texto_juego_plataforma = f"{juego} - {plataforma}"
    ancho_texto, _ = draw.textsize(texto_juego_plataforma, font=fuente_main)
    posicion_juego_plataforma = ((fondo.width - ancho_texto) // 2, 50)
    draw.text(posicion_juego_plataforma, texto_juego_plataforma, fill="white", font=fuente_main)

    # Decodificar y procesar imagen del jugador
    player_avatar_bytes = base64.b64decode(player_avatar_base64)
    player_avatar = Image.open(BytesIO(player_avatar_bytes))
    player_avatar = player_avatar.resize((600, 600))

    # Redondear imagen del jugador
    mask = Image.new('L', player_avatar.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0) + player_avatar.size, fill=255)
    player_avatar = ImageOps.fit(player_avatar, mask.size, centering=(0.5, 0.5))
    player_avatar.putalpha(mask)

    posicion_imagen_jugador = ((fondo.width - player_avatar.width) // 2, posicion_juego_plataforma[1] + 200)
    fondo.paste(player_avatar, posicion_imagen_jugador, player_avatar)

    borde_dibujo = ImageDraw.Draw(fondo)
    borde_dibujo.ellipse([posicion_imagen_jugador[0] - 2, posicion_imagen_jugador[1] - 2, 
                          posicion_imagen_jugador[0] + 602, posicion_imagen_jugador[1] + 602], 
                         outline='white', width=10)

    espacio_entre = 50
    texto_nombre_jugador = player_name
    ancho_texto_jugador, _ = draw.textsize(texto_nombre_jugador, font=fuente_secondary)
    posicion_nombre_jugador = ((fondo.width - ancho_texto_jugador) // 2, posicion_imagen_jugador[1] + player_avatar.height + espacio_entre)
    draw.text(posicion_nombre_jugador, texto_nombre_jugador, fill="white", font=fuente_secondary)

    espacio_entre_campeon = 100
    texto_campeon = "CAMPEÓN"
    ancho_texto_campeon, _ = draw.textsize(texto_campeon, font=fuente_main)
    posicion_campeon = ((fondo.width - ancho_texto_campeon) // 2, posicion_nombre_jugador[1] + espacio_entre_campeon)
    draw.text(posicion_campeon, texto_campeon, fill="white", font=fuente_main)

    texto_torneo = f"TORNEO - {id_torneo}"
    ancho_texto_torneo, _ = draw.textsize(texto_torneo, font=fuente_secondary)
    posicion_torneo = ((fondo.width - ancho_texto_torneo) // 2, posicion_campeon[1] + 150)
    draw.text(posicion_torneo, texto_torneo, fill="white", font=fuente_secondary)

    margen_inferior_izquierdo = 25
    ancho_texto_pais, _ = draw.textsize(pais, font=fuente_secondary)
    posicion_pais = (margen_inferior_izquierdo, fondo.height - margen_inferior_izquierdo - 60)
    draw.text(posicion_pais, pais, fill="white", font=fuente_secondary)

    espacio_entre_pais_alcance = 5
    texto_alcance = f"Alcance: {alcance}"
    ancho_texto_alcance, _ = draw.textsize(texto_alcance, font=fuente_info)
    posicion_alcance = (margen_inferior_izquierdo, posicion_pais[1] - 40 - espacio_entre_pais_alcance)
    draw.text(posicion_alcance, texto_alcance, fill="white", font=fuente_info)

    margen_inferior_derecho = 25
    ancho_texto_fecha, _ = draw.textsize(fecha, font=fuente_info)
    posicion_fecha = (fondo.width - ancho_texto_fecha - margen_inferior_derecho, fondo.height - margen_inferior_derecho - 30)
    draw.text(posicion_fecha, fecha, fill="white", font=fuente_info)

    fondo.save(nombre_imagen_winner_card)
    fondo.close()

def generar_imagen_torneo(fecha, juego, pais, plataforma, modalidad, hora, id_torneo, alcance, costo, output_filename):
    fondo = Image.open("imagenes/tournament.jpg")
    draw = ImageDraw.Draw(fondo)
    fuente_info = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=60)
    fuente_adicional = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=150)
    fuente_guia_inscripcion = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=50)
    texto_fecha = "Fecha: " + fecha
    posicion_fecha = (25, 25)
    draw.text(posicion_fecha, texto_fecha, fill="white", font=fuente_info)
    texto_pais_juego_plataforma = f"{pais} - {juego} - {plataforma}"
    texto_alcance = f"{alcance}"
    ancho_texto_alcance, alto_texto_alcance = draw.textsize(texto_alcance, font=fuente_guia_inscripcion)
    ancho_texto, alto_texto = draw.textsize(texto_pais_juego_plataforma, font=fuente_info)
    posicion_pais_juego_plataforma = ((fondo.width - ancho_texto) // 2, 500)
    draw.text(posicion_pais_juego_plataforma, texto_pais_juego_plataforma, fill="white", font=fuente_info)

    texto_hora = f"Hora del Torneo: {hora}"
    ancho_texto_hora, alto_texto_hora = draw.textsize(texto_hora, font=fuente_info)
    padding_x = 30
    padding_y = 20
    rect_x1 = (fondo.width - ancho_texto_hora) // 2 - padding_x
    rect_y1 = 500 + alto_texto + 50
    rect_x2 = rect_x1 + ancho_texto_hora + padding_x * 2
    rect_y2 = rect_y1 + alto_texto_hora + padding_y * 2

    radius = 10
    draw.rounded_rectangle([rect_x1, rect_y1, rect_x2, rect_y2], radius=radius, fill="white")
    posicion_hora_texto = ((fondo.width - ancho_texto_hora) // 2, rect_y1 + ((rect_y2 - rect_y1 - alto_texto_hora) // 2)
)
    draw.text(posicion_hora_texto, texto_hora, fill="black", font=fuente_info)

    texto_modalidad = modalidad
    ancho_texto_modalidad, alto_texto_modalidad = draw.textsize(texto_modalidad, font=fuente_info)
    rect_mod_x1 = (fondo.width - ancho_texto_modalidad) // 2 - padding_x
    rect_mod_y1 = rect_y2 + 25
    rect_mod_x2 = rect_mod_x1 + ancho_texto_modalidad + padding_x * 2
    rect_mod_y2 = rect_mod_y1 + alto_texto_modalidad + padding_y * 2

    draw.rounded_rectangle([rect_mod_x1, rect_mod_y1, rect_mod_x2, rect_mod_y2], radius=radius, fill="white")
    posicion_modalidad_texto = ((fondo.width - ancho_texto_modalidad) // 2, rect_mod_y1 + ((rect_mod_y2 - rect_mod_y1 - alto_texto_modalidad) // 2))
    draw.text(posicion_modalidad_texto, texto_modalidad, fill="black", font=fuente_info)

    texto_adicional = "TORNEO"
    ancho_texto_adicional, alto_texto_adicional = draw.textsize(texto_adicional, font=fuente_adicional)
    posicion_texto_adicional = ((fondo.width - ancho_texto_adicional) // 2, 300)
    draw.text(posicion_texto_adicional, texto_adicional, fill="white", font=fuente_adicional)
    texto_id = f"ID del Torneo: {id_torneo}"
    posicion_id = (25, fondo.height - 175)
    draw.text(posicion_id, texto_id, fill="white", font=fuente_info)
    texto_guia_inscripcion = f"Para inscribirte envía: !registrar {id_torneo}"
    posicion_texto_guia_inscripcion = (25, fondo.height - 75)
    draw.text(posicion_texto_guia_inscripcion, texto_guia_inscripcion, fill="white", font=fuente_guia_inscripcion)
    texto_costo = f"Costo: {costo}"
    ancho_texto_costo, alto_texto_costo = draw.textsize(texto_costo, font=fuente_info)
    posicion_costo = (fondo.width - ancho_texto_costo - 25, 25)
    posicion_alcance = (fondo.width - ancho_texto_alcance - 25, 100)
    draw.text(posicion_costo, texto_costo, fill="white", font=fuente_info)
    draw.text(posicion_alcance, texto_alcance, fill="white", font=fuente_guia_inscripcion)
    fondo.save(output_filename)
    fondo.close()

def reportar_imagen_etapa(etapa, enfrentamiento, output_filename):
    imagen = Image.new("RGB", (200, 90), "white")
    draw = ImageDraw.Draw(imagen)
    color_rojo_oscuro = "#8B0000"
    color_blanco = "white"       
    color_negro = "black"        
    color_gris_oscuro = "#404040"
    draw.rectangle([(0, 0), (199, 22)], fill=color_rojo_oscuro, outline="black", width=1 )
    draw.rectangle([(0, 21), (199, 43)], fill=color_blanco, outline="black", width=1)
    draw.rectangle([(0, 21), (49, 43)], fill=color_gris_oscuro, outline="black", width=1)
    draw.rectangle([(0, 42), (199, 64)], fill=color_blanco, outline="black", width=1)
    draw.rectangle([(0, 42), (49, 64)], fill=color_gris_oscuro, outline="black", width=1)
    texto_etapa = f"Etapa {etapa}"
    fuente_etapa = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=10)
    fuente_jugador = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=8)
    fuente_puntaje = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=8)
    fuente_info = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=6)
    ancho_texto_etapa, _ = draw.textsize(texto_etapa, font=fuente_etapa)
    posicion_texto_etapa = ((imagen.width - ancho_texto_etapa) // 2, (22 - fuente_etapa.getsize(texto_etapa)[1]) // 2)
    draw.text(posicion_texto_etapa, texto_etapa, fill=color_blanco, font=fuente_etapa)
    jugador_1_nombre = enfrentamiento['competidores'][0]['jugador']['usuario_discord']
    jugador_2_nombre = enfrentamiento['competidores'][1]['jugador']['usuario_discord']
    margen_izquierdo = 55
    altura_jugador_1 = 21 + (22 - fuente_jugador.getsize(jugador_1_nombre)[1]) // 2
    altura_jugador_2 = 42 + (22 - fuente_jugador.getsize(jugador_2_nombre)[1]) // 2
    draw.text((margen_izquierdo, altura_jugador_1), jugador_1_nombre, fill=color_negro, font=fuente_jugador)
    draw.text((margen_izquierdo, altura_jugador_2), jugador_2_nombre, fill=color_negro, font=fuente_jugador)
    puntaje_jugador_1 = enfrentamiento['competidores'][0]['puntaje']
    puntaje_jugador_2 = enfrentamiento['competidores'][1]['puntaje']
    ancho_puntaje_1, _ = draw.textsize(str(puntaje_jugador_1), font=fuente_puntaje)
    ancho_puntaje_2, _ = draw.textsize(str(puntaje_jugador_2), font=fuente_puntaje)
    altura_puntaje = 21 + (22 - fuente_puntaje.getsize(str(puntaje_jugador_1))[1]) // 2
    draw.text(((49 - ancho_puntaje_1) // 2, altura_puntaje), str(puntaje_jugador_1), fill=color_blanco, font=fuente_puntaje)
    draw.text(((49 - ancho_puntaje_2) // 2, altura_puntaje + 21), str(puntaje_jugador_2), fill=color_blanco, font=fuente_puntaje)
    fecha_enfrentamiento = enfrentamiento['fecha_enfrentamiento']
    codigo_enfrentamiento = enfrentamiento['codigo_enfrentamiento']
    draw.text((5, imagen.height - 25), f"Fecha: {fecha_enfrentamiento}", fill=color_negro, font=fuente_info)
    draw.text((5, imagen.height - 15), f"Código: {codigo_enfrentamiento}", fill=color_negro, font=fuente_info)
    imagen.save(output_filename)
    imagen.close()
