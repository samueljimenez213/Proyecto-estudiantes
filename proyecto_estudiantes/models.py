import json

# TUPLA de campos: el orden y los nombres son fijos, por eso no es una lista.
# La usan el Controlador y la Vista para no repetir textos sueltos.
CAMPOS_CLIENTE = ("nombre", "apellido", "email", "telefono", "ciudad", "direccion")

# TUPLA de campos de texto que se piden al crear un estudiante (las notas y
# materias se llenan aparte, con agregar_nota).
CAMPOS_ESTUDIANTE = ("nombre", "apellido", "email", "carnet")


class Cliente:
    """MODELO: representa a un cliente."""

    def __init__(self, id_cliente, nombre, apellido, email, telefono, ciudad, direccion):
        self.id = id_cliente          # no usamos 'id' como parámetro: es una función de Python
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.telefono = telefono
        self.ciudad = ciudad
        self.direccion = direccion

    def obtener_nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def a_diccionario(self):
        # Objeto -> diccionario (listo para JSON)
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "telefono": self.telefono,
            "ciudad": self.ciudad,
            "direccion": self.direccion,
        }

    @classmethod
    def desde_diccionario(cls, datos):
        # Diccionario -> objeto. Es un método de la CLASE, no de un objeto:
        # se usa así -> Cliente.desde_diccionario({...})
        return cls(
            datos["id"],
            datos["nombre"],
            datos["apellido"],
            datos["email"],
            datos["telefono"],
            datos.get("ciudad", ""),      # .get por si el archivo es de una versión vieja
            datos.get("direccion", ""),
        )

    def a_json(self):
        return json.dumps(self.a_diccionario(), ensure_ascii=False)

    def __str__(self):
        return f"[{self.id}] {self.obtener_nombre_completo()} - {self.email}"


class Estudiante:
    """MODELO: representa a un estudiante. Usa las cuatro colecciones."""

    def __init__(self, id_estudiante, nombre, apellido, email, carnet, notas=None, materias=None):
        self.id = id_estudiante
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.carnet = carnet                      # ej: EST2026001
        # DICCIONARIO DE LISTAS: {"Matemática": [18, 19], "Inglés": [17]}
        self.notas = notas if notas else {}
        # CONJUNTO: materias en las que está inscrito, sin repetidos
        self.materias = set(materias) if materias else set()

    def obtener_nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def inscribir_materia(self, materia):
        # add() no duplica: si ya estaba inscrito, no pasa nada
        self.materias.add(materia)

    def agregar_nota(self, materia, nota):
        self.inscribir_materia(materia)
        # setdefault crea la lista vacía la primera vez que aparece la materia
        self.notas.setdefault(materia, []).append(nota)

    def obtener_promedio(self):
        todas = []
        for lista_notas in self.notas.values():
            todas.extend(lista_notas)
        if not todas:
            return 0
        return round(sum(todas) / len(todas), 2)

    def materias_en_comun(self, otro_estudiante):
        # INTERSECCIÓN de conjuntos: qué materias comparten dos estudiantes
        return self.materias & otro_estudiante.materias

    def a_diccionario(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "carnet": self.carnet,
            "notas": self.notas,
            # JSON no sabe guardar un set: lo convertimos a lista ordenada
            "materias": sorted(self.materias),
        }

    @classmethod
    def desde_diccionario(cls, datos):
        return cls(
            datos["id"], datos["nombre"], datos["apellido"], datos["email"],
            datos["carnet"],
            notas=datos.get("notas", {}),
            # y al leer lo volvemos a convertir en set
            materias=set(datos.get("materias", [])),
        )

    def __str__(self):
        return f"[{self.carnet}] {self.obtener_nombre_completo()} - Promedio: {self.obtener_promedio()}"
