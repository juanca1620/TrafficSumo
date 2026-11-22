"""
Script utilitario de validacion de configuracion de red vial y demanda vehicular.
Cumple con los requerimientos CU2, CU3; RU001, RU002, RU017 (Formato PU-04).
"""
import os
import xml.etree.ElementTree as ET


def validar_red(net_xml_path):
    """
    Verifica que la red vial compilada (.net.xml) cumpla:
    1. Tenga 4 accesos de entrada a la intersección (N, S, E, O).
    2. Cada acceso tenga al menos 2 carriles (numLanes >= 2).
    """
    if not os.path.exists(net_xml_path):
        raise FileNotFoundError(f"Archivo de red vial no encontrado: {net_xml_path}")

    try:
        tree = ET.parse(net_xml_path)
    except ET.ParseError as e:
        raise ET.ParseError(f"Error de sintaxis en XML de red: {e}")

    root = tree.getroot()

    # Tramos de entrada esperados a la intersección central C
    inbound_expected = ["N2C", "S2C", "E2C", "W2C"]
    edges_found = {}

    for edge in root.findall("edge"):
        e_id = edge.get("id")
        if e_id and not e_id.startswith(":"):
            edges_found[e_id] = edge

    # Validar existencia de los 4 accesos
    faltantes = [acc for acc in inbound_expected if acc not in edges_found]
    if faltantes:
        return False, f"La intersección no tiene 4 accesos válidos. Faltan: {faltantes}"

    # Validar criterio de al menos 2 carriles por acceso
    for acc in inbound_expected:
        edge = edges_found[acc]
        lanes = edge.findall("lane")
        num_lanes = int(edge.get("numLanes", len(lanes)))
        if num_lanes < 2:
            return False, f"El acceso {acc} tiene {num_lanes} carril(es). Criterio mínimo: al menos 2 carriles."

    return True, "Red vial válida: 4 accesos con 2 o más carriles cada uno."


def validar_demanda(routes_xml_path):
    """
    Verifica que el archivo de rutas (routes.rou.xml) cumpla:
    1. Flujos vehiculares con valores numéricos no negativos.
    2. Demanda del eje Norte-Sur mayor que la demanda del eje Este-Oeste (CU3: mayor congestión en NS).
    """
    if not os.path.exists(routes_xml_path):
        raise FileNotFoundError(f"Archivo de demanda no encontrado: {routes_xml_path}")

    try:
        tree = ET.parse(routes_xml_path)
    except ET.ParseError as e:
        raise ET.ParseError(f"Error de sintaxis en XML de rutas: {e}")

    root = tree.getroot()
    flows = root.findall("flow")
    if not flows:
        return False, "No se encontraron elementos <flow> de demanda vehicular."

    flujos_ns = 0.0
    flujos_ew = 0.0

    for f in flows:
        flow_id = f.get("id", "desconocido")
        raw_val = f.get("vehsPerHour")
        if raw_val is None:
            raise ValueError(f"El flujo '{flow_id}' no define vehsPerHour.")

        try:
            val = float(raw_val)
        except ValueError:
            raise ValueError(f"Valor no numérico en vehsPerHour para flujo '{flow_id}': {raw_val}")

        if val < 0:
            raise ValueError(f"Flujo vehicular negativo no permitido ({val} veh/h) en '{flow_id}'.")

        route = f.get("route", "")
        # Clasificar por eje
        if "NS" in route or "SN" in route or "NS" in flow_id or "SN" in flow_id:
            flujos_ns += val
        elif "EW" in route or "WE" in route or "EW" in flow_id or "WE" in flow_id:
            flujos_ew += val

    if flujos_ns <= flujos_ew:
        return False, f"Incumplimiento del criterio CU3: La demanda NS ({flujos_ns} veh/h) debe ser mayor a EW ({flujos_ew} veh/h)."

    return True, f"Demanda válida: Congestión predominante en NS ({flujos_ns} veh/h > {flujos_ew} veh/h)."


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    net_path = os.path.join(base_dir, "network", "intersection.net.xml")
    rou_path = os.path.join(base_dir, "demand", "routes.rou.xml")
    ok_red, msg_red = validar_red(net_path)
    ok_dem, msg_dem = validar_demanda(rou_path)
    print(f"[RED VIAL]  {ok_red}: {msg_red}")
    print(f"[DEMANDA]   {ok_dem}: {msg_dem}")
