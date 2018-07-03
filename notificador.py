from bs4 import BeautifulSoup
from tabulate import tabulate
import requests
import operator
import datetime
import urllib3
import numpy
import json
import time

urllib3.disable_warnings()

URL_NACIONAL_PDTE = "https://p2018.ine.mx/assets/JSON/PRESIDENTE/NACIONAL/Presidente_NACIONAL.json"
URL_NACIONAL_SEN  = "https://prep2018.eluniversal.com.mx/assets/JSON/SENADORES_MR/NACIONAL/Senadores_MR_NACIONAL_ESTATAL.json"
URL_NACIONAL_DIP  = "https://prep2018.eluniversal.com.mx/assets/JSON/DIPUTADOS_MR/NACIONAL/Diputados_MR_NACIONAL.json"
URL_COLIMA        = "https://www.prepcolima.mx/api/reload"
URL_JALISCO       = "http://jalisco.prep.oem.com.mx/index.php?gubernatura-entidad"

datos_nacional_pdte = ""
datos_nacional_sen  = ""
datos_nacional_dip  = ""
datos_colima        = ""
datos_jalisco       = ""

def normal_clamped(mu, sigma):
    x = numpy.random.normal(mu, sigma)
    if x < 0:
        x = 0
    return x

def getThird(item):
    return item[2]

def getSecond(item):
    return float(item[1][:-1])

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
    with open(f"{prefix}/{datetime.datetime.now()}", "w") as f:
        f.write(datos)

def handle_analisis_nacional_pdte(datos):
    print()
    print()
    print(f"Actualización PREP nacional presidente a las {time.strftime('%H:%M:%S')}")
    try:
        prep_nal = json.loads(datos)
    except Exception:
        print("Error al procesar datos del PREP Nacional Presidente")
        return
    capturadas = prep_nal["actasContabilizadas"]["total"]
    esperadas  = prep_nal["totalActas"]
    pct        = capturadas / esperadas
    print(f"    Corte al {prep_nal['horaCorte']}")
    print(f"    Casillas contabilizadas: {capturadas}/{esperadas}")
    print(f"    Porcentaje avance PREP: {prep_nal['actasContabilizadas']['porcentaje']}%")

    resultados = prep_nal["votosCandidatoPartidoCoalicion"]
    candidatos = []
    candidatos.append(["Ricardo Anaya Cortés (PAN+PRD+MC)", f"{resultados[0]['porcentaje']}%", resultados[0]['total']])
    candidatos.append(["José Antonio Meade Kuribreña (PRI+PVEM+PANAL)", f"{resultados[1]['porcentaje']}%", resultados[1]['total']])
    candidatos.append(["Andrés Manuel López Obrador (MORENA+PT+PES)", f"{resultados[2]['porcentaje']}%", resultados[2]['total']])
    candidatos.append(["Jaime Heliodoro Rodríguez Calderón", f"{resultados[4]['porcentaje']}%", resultados[4]['total']])
    candidatos.append(["Margarita Ester Zavala Gómez del Campo", f"{resultados[3]['porcentaje']}%", resultados[3]['total']])
    candidatos.append(["Candidaturas no registradas", f"{resultados[5]['porcentaje']}%", resultados[5]['total']])
    candidatos.append(["Votos nulos", f"{resultados[6]['porcentaje']}%", resultados[6]['total']])

    candidatos.sort(key=getThird, reverse=True)

    restantes = (prep_nal["totalVotos"] / pct) - prep_nal["totalVotos"]
    votos_candidatos = []

    for candidato in candidatos:
        votos_candidatos.append(candidato[2])

    proyecciones = simular_eleccion(votos_candidatos, restantes, 20000)

    for idx, proyeccion in enumerate(proyecciones):
        candidatos[idx].append(f"{proyeccion*100:.4f}%")

    print(tabulate(candidatos, headers=["Candidato a la Presidencia de la República", "Porcentaje", "Votos", "Probabilidad de ganar"]))

    save_to_file("prep_nacional_presidente", datos)

def handle_analisis_nacional_sen(datos):
    print()
    print()
    print(f"Actualización PREP nacional senadores a las {time.strftime('%H:%M:%S')}")
    try:
        prep_nal = json.loads(datos)
    except Exception:
        print("Error al procesar datos del PREP Nacional Senadores")
        return
    resultados = prep_nal["entidadesGanadaPartidoCoalicion"]
    votos      = prep_nal["votosCandidatoPartidoCoalicion"]
    resultados_primera = prep_nal["entidadesGanadasPrimeraMinoria"]
    partidos = []
    partidos.append(["Coalición Por México al Frente (PAN+PRD+MC)", resultados[9]['total']*2 + resultados_primera[9]['total'], votos[9]['porcentaje']])
    partidos.append(["Coalición Todos por México (PRI+PVEM+PANAL)", resultados[10]['total']*2 + resultados_primera[10]['total'], votos[10]['porcentaje']])
    partidos.append(["Coalición Juntos Haremos Historia (MORENA+PT+PES)", resultados[11]['total']*2 + resultados_primera[11]['total'], votos[11]['porcentaje']])

    total_mr = 0
    total_rp = 0

    for idx, partido in enumerate(partidos):
        partidos[idx][2] = partidos[idx][1] + int(32 * (0.01 *partidos[idx][2]))
        total_mr += partido[1]
        total_rp += partidos[idx][2]

    partidos.append(("Total", total_mr, total_rp))

    print(tabulate(partidos, ["Coalición", "Senadores MR", "Senadores MR + RP (estimado)"]))
    save_to_file("prep_nacional_senadores", datos)

def handle_analisis_nacional_dip(datos):
    print()
    print()
    print(f"Actualización PREP nacional diputados a las {time.strftime('%H:%M:%S')}")
    try:
        prep_nal = json.loads(datos)
    except Exception:
        print("Error al procesar datos del PREP Nacional Diputados")
        return
    resultados = prep_nal["entidadesGanadaPartidoCoalicion"]
    votos = prep_nal["votosCandidatoPartidoCoalicion"]
    partidos = []
    partidos.append(["Coalición Por México al Frente (PAN+PRD+MC)", resultados[9]['total'], votos[9]['porcentaje']])
    partidos.append(["Coalición Todos por México (PRI+PVEM+PANAL)", resultados[10]['total'], votos[9]['porcentaje']])
    partidos.append(["Coalición Juntos Haremos Historia (MORENA+PT+PES)", resultados[11]['total'], votos[9]['porcentaje']])

    total_mr = 0
    total_rp = 0

    for idx, partido in enumerate(partidos):
        partidos[idx][2] = partidos[idx][1] + int(200 * (0.01 * partidos[idx][2]))
        total_mr += partido[1]
        total_rp += partidos[idx][2]

    partidos.append(("Total", total_mr, total_rp))

    print(tabulate(partidos, ["Coalición", "Diputados MR", "Diputados MR + RP (estimado)"]))
    save_to_file("prep_nacional_diputados", datos)

def handle_analisis_colima(datos):
    print()
    print()
    print(f"Actualización PREP estatal Colima a las {time.strftime('%H:%M:%S')}")
    try:
        colima_json = json.loads(datos)
    except Exception:
        print("Error al procesar datos del PREP Colima")
        return
    casillas   = colima_json['boxesstatus']
    capturadas = casillas['capturadas']
    esperadas  = casillas['total']
    pct        = (capturadas / esperadas) * 100
    print(f"    Casillas contabilizadas: {capturadas}/{esperadas}")
    print(f"    Porcentaje avance PREP: {pct:.4}%")

    ayuntamientos = colima_json['votes_towns']

    for ayto in ayuntamientos:
        if ayto["town_id"] == 2:
            resultados_ayto_col = []
            walter = int(ayto["pri"]) + int(ayto["pvem"]) + int(ayto["pri_pvem"])
            insua  = int(ayto["pan"]) + int(ayto["prd"]) + int(ayto["pan_prd"])
            rafael = int(ayto["mor"]) + int(ayto["pt"]) + int(ayto["pes"]) + int(ayto["mor_pt"]) + int(ayto["mor_pes"]) + int(ayto["pt_pes"]) + int(ayto["mor_pt_pes"])
            locho  = int(ayto["mc"])
            chapula = int(ayto["nva"])
            nulos   = int(ayto["nulo"])
            totales = ayto["total"]

            resultados_ayto_col.append(["Héctor Insúa García (PAN+PRD)", f"{(insua/totales)*100:.4}%", insua])
            resultados_ayto_col.append(["Walter Alejandro Oldenbourg Ochoa (PRI+PVEM)", f"{(walter/totales)*100:.4}%", walter])
            resultados_ayto_col.append(["Rafael Briceño Alcaraz (MORENA+PT+PES)", f"{(rafael/totales)*100:.4}%", rafael])
            resultados_ayto_col.append(["Leoncio Alfonso Morán Sánchez (MC)", f"{(locho/totales)*100:.4}%", locho])
            resultados_ayto_col.append(["Roberto Chapula de la Mora (PANAL)", f"{(chapula/totales)*100:.4}%", chapula])
            resultados_ayto_col.append(["Votos nulos", f"{(nulos/totales)*100:.4}%", nulos])

            resultados_ayto_col.sort(key=getThird, reverse=True)

            resultados_ayto_col.append(["Votos totales", f"{(totales/totales)*100:.4}%", totales])

            restantes = ((100 * totales) / pct) - totales
            votos_candidatos = []

            for candidato in resultados_ayto_col:
                if candidato[0] != "Votos totales":
                    votos_candidatos.append(candidato[2])

            proyecciones = simular_eleccion(votos_candidatos, restantes, 20000)

            for idx, proyeccion in enumerate(proyecciones):
                resultados_ayto_col[idx].append(f"{proyeccion*100:.4f}%")

            print(tabulate(resultados_ayto_col, headers=["Candidato a la presidencia municipal de Colima", "Porcentaje", "Votos", "Probabilidad de ganar"]))

    save_to_file("prep_colima", datos)

def handle_analisis_jalisco(datos):
    print()
    print()
    print(f"Actualización PREP estatal Jalisco a las {time.strftime('%H:%M:%S')}")
    try:
        soup = BeautifulSoup(datos, "html.parser")
    except Exception:
        print("Error al procesar datos del PREP Jalisco")
        return
    try:
        capturadas = int(soup.find_all(id='lblActasCapturadasTopH')[0].text)
        esperadas  = int(soup.find_all(id='lblActasEsperadasTop')[0].text)
    except Exception:
        print("Error al procesar datos del PREP Jalisco")
        return
    pct = (capturadas/esperadas) * 100
    print(f"    Casillas contabilizadas: {capturadas}/{esperadas}")
    print(f"    Porcentaje avance PREP: {pct:.4}%")
    candidatos = []
    for candidato in soup.find_all(class_="gobernatura"):
        nombre = candidato.find_all("p")[0].text
        pct    = candidato.find_all(class_="color-oficial")[0].text
        candidatos.append((nombre, pct))
    candidatos.sort(key=getSecond, reverse=True)
    print(tabulate(candidatos, headers=["Candidato a la gubernatura de Jalisco", "Porcentaje"]))
    save_to_file("prep_jalisco", datos)


while True:
    try:
        nacional_pdte = requests.get(URL_NACIONAL_PDTE).text
    except Exception:
        nacional_pdte = datos_nacional_pdte
        print("Error al obtener datos del PREP Nacional Presidente")

    try:
        nacional_sen = requests.get(URL_NACIONAL_SEN).text
    except Exception:
        nacional_sen = datos_nacional_sen
        print("Error al obtener datos del PREP Nacional Senadores")

    try:
        nacional_dip = requests.get(URL_NACIONAL_DIP).text
    except Exception:
        nacional_dip = datos_nacional_dip
        print("Error al obtener datos del PREP Nacional Diputados")

    try:
        colima = requests.get(URL_COLIMA).text
    except Exception:
        colima = datos_colima
        print("Error al obtener datos del PREP Colima")

    try:
        jalisco = requests.get(URL_JALISCO).text
    except Exception:
        jalisco = datos_jalisco
        print("Error al obtener datos del PREP Jalisco")

    if nacional_pdte != datos_nacional_pdte:
        datos_nacional_pdte = nacional_pdte
        handle_analisis_nacional_pdte(datos_nacional_pdte)

    if nacional_sen != datos_nacional_sen:
        datos_nacional_sen = nacional_sen
        handle_analisis_nacional_sen(datos_nacional_sen)

    if nacional_dip != datos_nacional_dip:
        datos_nacional_dip = nacional_dip
        handle_analisis_nacional_dip(datos_nacional_dip)

    if colima != datos_colima:
        datos_colima = colima
        handle_analisis_colima(datos_colima)

    if jalisco != datos_jalisco:
        datos_jalisco = jalisco
        handle_analisis_jalisco(datos_jalisco)

    time.sleep(61)
    print("Actualización de datos... ")

