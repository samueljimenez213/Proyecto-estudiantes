from models import Estudiante, CAMPOS_ESTUDIANTE
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido

gestor = GestorJSON("data/estudiantes.json")

# TUPLAS de configuración: fijas, nadie las modifica en tiempo de ejecución
CAMPOS_OBLIGATORIOS = ("nombre", "apellido", "email", "carnet")
CAMPOS_BUSCABLES = ("nombre", "apellido", "email", "carnet")

NOTA_MINIMA = 0
NOTA_MAXIMA = 20


# ===================== AYUDAS INTERNAS =====================

def emails_registrados(excepto_id=None):
    """CONJUNTO con los emails ya usados. Sirve para detectar duplicados al instante."""
    return {
        registro["email"].lower()
        for registro in gestor.leer()
        if registro["id"] != excepto_id
    }


def carnets_registrados(excepto_id=None):
    """CONJUNTO con los carnets ya usados (misma idea que con el email)."""
    return {
        registro["carnet"].upper()
        for registro in gestor.leer()
        if registro["id"] != excepto_id
    }


def siguiente_id():
    ids = [registro["id"] for registro in gestor.leer()]
    return max(ids) + 1 if ids else 1


def buscar_posicion(registros, id_estudiante):
    """Devuelve el índice del registro con ese id, o None si no existe."""
    for indice, registro in enumerate(registros):     # enumerate me da índice y valor
        if registro["id"] == id_estudiante:
            return indice
    return None


# ===================== C · CREATE =====================

def crear_estudiante(datos):
    """datos: diccionario con las claves de CAMPOS_ESTUDIANTE. Devuelve (exito, mensaje)."""
    try:
        # 1) Normalizo: un diccionario con todos los campos, sin espacios sobrantes
        valores = {campo: str(datos.get(campo, "")).strip() for campo in CAMPOS_ESTUDIANTE}
        valores["carnet"] = valores["carnet"].upper()

        # 2) Reviso obligatorios recorriendo la TUPLA
        faltantes = [campo for campo in CAMPOS_OBLIGATORIOS if not valores[campo]]
        if faltantes:
            return False, f"Faltan campos obligatorios: {', '.join(faltantes)}"

        # 3) Formato del email
        if not es_email_valido(valores["email"]):
            return False, f"El email '{valores['email']}' no tiene un formato válido"

        # 4) Duplicados: búsqueda instantánea dentro de un CONJUNTO
        if valores["email"].lower() in emails_registrados():
            return False, "Ese email ya está registrado"
        if valores["carnet"] in carnets_registrados():
            return False, f"El carnet {valores['carnet']} ya está registrado"

        # 5) Creo el objeto del Modelo. ** convierte el diccionario en argumentos
        estudiante = Estudiante(siguiente_id(), **valores)

        # 6) Agrego a la LISTA y guardo
        registros = gestor.leer()
        registros.append(estudiante.a_diccionario())
        if not gestor.guardar(registros):
            return False, "No se pudo escribir el archivo"

        return True, f"Estudiante {estudiante.obtener_nombre_completo()} creado con id {estudiante.id}"

    except Exception as error:
        return False, f"Error inesperado: {error}"


# ===================== R · READ =====================

def obtener_todos():
    """LISTA de objetos Estudiante."""
    return [Estudiante.desde_diccionario(registro) for registro in gestor.leer()]


def obtener_por_id(id_estudiante):
    for estudiante in obtener_todos():
        if estudiante.id == id_estudiante:
            return estudiante
    return None


# ===================== S · SEARCH =====================

def buscar_estudiantes(termino):
    """Búsqueda lineal: revisa registro por registro los campos de CAMPOS_BUSCABLES."""
    termino = termino.strip().lower()
    if not termino:
        return []

    encontrados = []
    for registro in gestor.leer():
        for campo in CAMPOS_BUSCABLES:                 # recorro la TUPLA de campos
            if termino in str(registro.get(campo, "")).lower():
                encontrados.append(Estudiante.desde_diccionario(registro))
                break                                   # ya coincidió: paso al siguiente
    return encontrados


# ===================== U · UPDATE =====================

def actualizar_estudiante(id_estudiante, cambios):
    """cambios: diccionario solo con los campos que se quieren modificar."""
    try:
        # DIFERENCIA DE CONJUNTOS: ¿mandaron algún campo que no existe?
        desconocidos = set(cambios) - set(CAMPOS_ESTUDIANTE)
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"

        if not cambios:
            return False, "No se indicó ningún cambio"

        cambios = {campo: str(valor).strip() for campo, valor in cambios.items()}

        if "email" in cambios:
            if not es_email_valido(cambios["email"]):
                return False, "El email no tiene un formato válido"
            if cambios["email"].lower() in emails_registrados(excepto_id=id_estudiante):
                return False, "Ese email ya lo usa otro estudiante"

        if "carnet" in cambios:
            cambios["carnet"] = cambios["carnet"].upper()
            if not cambios["carnet"]:
                return False, "El carnet no puede quedar vacío"
            if cambios["carnet"] in carnets_registrados(excepto_id=id_estudiante):
                return False, "Ese carnet ya lo usa otro estudiante"

        registros = gestor.leer()
        posicion = buscar_posicion(registros, id_estudiante)
        if posicion is None:
            return False, f"No existe un estudiante con id {id_estudiante}"

        registros[posicion].update(cambios)             # actualizo el diccionario en su lugar
        if not gestor.guardar(registros):
            return False, "No se pudo escribir el archivo"
        return True, f"Estudiante {id_estudiante} actualizado ({len(cambios)} campo/s)"

    except Exception as error:
        return False, f"Error inesperado: {error}"


# ===================== D · DELETE =====================

def eliminar_estudiante(id_estudiante):
    registros = gestor.leer()
    # Construyo una LISTA NUEVA sin ese registro: nunca borro mientras recorro
    quedan = [registro for registro in registros if registro["id"] != id_estudiante]

    if len(quedan) == len(registros):
        return False, f"No existe un estudiante con id {id_estudiante}"

    if not gestor.guardar(quedan):
        return False, "No se pudo escribir el archivo"
    return True, f"Estudiante {id_estudiante} eliminado"


# ===================== NOTAS Y MATERIAS (colecciones) =====================

def agregar_nota(id_estudiante, materia, nota):
    """Agrega una nota (0 a 20) a una materia. Devuelve (exito, mensaje)."""
    try:
        materia = str(materia).strip().title()      # evita "matemática" y "Matemática" por separado
        if not materia:
            return False, "La materia no puede estar vacía"

        # La nota puede llegar como texto desde la Vista: la convierto aquí,
        # porque validar es trabajo del Controlador.
        try:
            valor = float(str(nota).strip().replace(",", "."))
        except ValueError:
            return False, f"La nota '{nota}' no es un número"

        if not (NOTA_MINIMA <= valor <= NOTA_MAXIMA):   # también rechaza nan e inf
            return False, f"La nota debe estar entre {NOTA_MINIMA} y {NOTA_MAXIMA}"

        if valor.is_integer():
            valor = int(valor)                          # guardo 18 y no 18.0

        registros = gestor.leer()
        posicion = buscar_posicion(registros, id_estudiante)
        if posicion is None:
            return False, f"No existe un estudiante con id {id_estudiante}"

        # El Modelo hace el trabajo: agrega la nota a la LISTA de esa materia
        # (dentro del DICCIONARIO) y añade la materia al CONJUNTO.
        estudiante = Estudiante.desde_diccionario(registros[posicion])
        estudiante.agregar_nota(materia, valor)
        registros[posicion] = estudiante.a_diccionario()

        if not gestor.guardar(registros):
            return False, "No se pudo escribir el archivo"
        return True, f"Nota {valor} agregada en {materia} a {estudiante.obtener_nombre_completo()}"

    except Exception as error:
        return False, f"Error inesperado: {error}"


def promedio_estudiante(id_estudiante):
    """Devuelve (True, DICCIONARIO de promedios) o (False, mensaje)."""
    estudiante = obtener_por_id(id_estudiante)
    if estudiante is None:
        return False, f"No existe un estudiante con id {id_estudiante}"

    por_materia = {
        materia: round(sum(lista) / len(lista), 2)
        for materia, lista in estudiante.notas.items()
        if lista
    }
    return True, {
        "nombre": estudiante.obtener_nombre_completo(),
        "general": estudiante.obtener_promedio(),
        "por_materia": por_materia,
    }


def materias_ofertadas():
    """CONJUNTO con todas las materias inscritas por todos los estudiantes, sin repetir."""
    todas = set()
    for estudiante in obtener_todos():
        todas |= estudiante.materias        # UNIÓN de conjuntos
    return todas


def estudiantes_en_comun(id_a, id_b):
    """Devuelve (True, set de materias compartidas) o (False, mensaje)."""
    if id_a == id_b:
        return False, "Elija dos estudiantes distintos"

    estudiante_a = obtener_por_id(id_a)
    estudiante_b = obtener_por_id(id_b)
    if estudiante_a is None:
        return False, f"No existe un estudiante con id {id_a}"
    if estudiante_b is None:
        return False, f"No existe un estudiante con id {id_b}"

    # INTERSECCIÓN de conjuntos (operador &), resuelta dentro del Modelo
    return True, estudiante_a.materias_en_comun(estudiante_b)
