import requests
import operator
import datetime
import numpy
import time

URL_NACIONAL = "placeholder"
URL_COLIMA   = "placeholder"
URL_JALISCO  = "placeholder"

datos_nacional = ""
datos_colima   = ""
datos_jalisco  = ""

def normal_clamped(mu, sigma):
    x = numpy.random.normal(mu, sigma)
    if x < 0:
        x = 0
    return x

def simular_eleccion(votos_candidatos: list, restantes: float, simulations: int):
    """

    :param votos_candidatos: Una lista con la cantidad de votos por candidato, ej: [380, 420, 91]
    :param restantes: Estimado de votos restantes a computar
    :param simulations: Cantidad de simulaciones a realizar
    :return: Lista con el porcentaje de simulaciones que ganó cada candidato, ej: [0.30, 0.69, 0.01]
    """
    wins = {}
    votos_acumulados = sum(votos_candidatos)
    porcentajes_candidatos = [votos / votos_acumulados for votos in votos_candidatos]

    for _ in range(simulations):
        simulacion_candidatos = {}
        for idx, pct in enumerate(porcentajes_candidatos):
            simulacion_candidatos[idx] = votos_candidatos[idx] + (restantes * normal_clamped(pct, 0.05))
        winner = max(simulacion_candidatos.items(), key=operator.itemgetter(1))[0]
        try:
            wins[winner] += 1
        except KeyError:
            wins[winner] = 1

    resultados = []

    for i in range(len(votos_candidatos)):
        resultados.append(wins.setdefault(i, 0) / simulations)

    return resultados

def save_to_file(prefix, datos):
    with open(f"{prefix}_{datetime.datetime.now()}", "w") as f:
        f.write(datos)

def handle_analisis_nacional(datos):
    save_to_file("prep_nacional", datos)

def handle_analisis_colima(datos):
    save_to_file("prep_colima", datos)

def handle_analisis_jalisco(datos):
    save_to_file("prep_jalisco", datos)

"""
while True:
    nacional = requests.get(URL_NACIONAL).text
    colima   = requests.get(URL_COLIMA).text
    jalisco  = requests.get(URL_JALISCO).text

    if nacional != datos_nacional:
        datos_nacional = nacional
        handle_analisis_nacional(datos_nacional)

    if colima != datos_colima:
        datos_colima = jalisco
        handle_analisis_colima(datos_colima)

    if jalisco != datos_jalisco:
        datos_jalisco = jalisco
        handle_analisis_jalisco(datos_jalisco)

    time.sleep(10)

"""