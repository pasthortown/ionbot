import random
from datetime import datetime

def definir_enfrentamientos(participantes, fecha_enfrentamiento_str, torneo_id, etapa):
    enfrentamientos = []
    random.shuffle(participantes)
    for i in range(0, len(participantes), 2):
        pareja = [{"jugador": participantes[i], "puntaje": None, "puntaje_contendiente": None}, {"jugador": participantes[i + 1], "puntaje": None, "puntaje_contendiente": None}]
        enfrentamiento = {
            "competidores": pareja,
            "fecha_enfrentamiento": fecha_enfrentamiento_str,
            "codigo_enfrentamiento": str(torneo_id) + str(etapa) + str(i),
            "ganador": None
        }
        enfrentamientos.append(enfrentamiento)
    return enfrentamientos