import sqlite3
from datetime import datetime


class Producto:
    def __init__(self, id, nombre, cantidad, precio):
        self.__id = id
        self.nombre = nombre
        self.cantidad = cantidad
        self.precio = precio

    def __str__(self):
        return f"ID: {self.__id} / Nombre: {self.nombre} / Cantidad: {self.cantidad} / Precio: {self.precio}"

    @property
    def id(self):
        return self.__id


class Empleado:
    def __init__(self, id, nombre, apellido, cargo, salario, password):
        self.__id = id
        self.nombre = nombre
        self.apellido = apellido
        self.cargo = cargo
        self.salario = salario
        self.__password = password

    def __str__(self):
        return (
            f"ID: {self.__id} / "
            f"{self.nombre} {self.apellido} / "
            f"Cargo: {self.cargo} / "
            f"Salario: {self.salario} / "
            f"Contraseña: {self.__password}"
        )

    @property
    def id(self):
        return self.__id


# Inventario (productos + empleados + auditoría)


class Inventario:
    def __init__(self, db_nombre="inventario.db"):
        self.db_nombre = db_nombre
        # Crear tablas al iniciar
        self._crear_tabla_productos()
        self._crear_tabla_empleados()
        self._crear_tabla_audit()

    def _conect(self):
        return sqlite3.connect(self.db_nombre)

    # — Tabla de productos —
    def _crear_tabla_productos(self):
        with self._conect() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio REAL NOT NULL
                )
            """
            )
            c.commit()

    # — Tabla de empleados —
    def _crear_tabla_empleados(self):
        with self._conect() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    cargo TEXT NOT NULL,
                    salario REAL NOT NULL,
                    password TEXT NOT NULL
                )
            """
            )
            c.commit()

    # — Tabla de auditoría —
    def _crear_tabla_audit(self):
        with self._conect() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empleado_id INTEGER NOT NULL,
                    tabla TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    registro_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(empleado_id) REFERENCES empleados(id)
                )
            """
            )
            c.commit()

    def log_action(self, empleado_id, tabla, accion, registro_id):
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._conect() as c:
            c.execute(
                """
                INSERT INTO audit_logs
                  (empleado_id, tabla, accion, registro_id, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (empleado_id, tabla, accion, registro_id, ts),
            )
            c.commit()

    # — CRUD de Productos —
    def agregar_product(self, nombre, cantidad, precio, actor_id):
        with self._conect() as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO productos (nombre, cantidad, precio) VALUES (?, ?, ?)",
                (nombre, cantidad, precio),
            )
            c.commit()
            prod_id = cur.lastrowid
        print(f"Producto '{nombre}' agregado (ID {prod_id}).")
        self.log_action(actor_id, "productos", "INSERT", prod_id)

    def obtener_productos(self):
        productos = []
        with self._conect() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM productos")
            for fila in cur.fetchall():
                productos.append(Producto(*fila))
        return productos

    def buscar_producto_por_nombre(self, nombre, actor_id):
        with self._conect() as c:
            cur = c.cursor()
            cur.execute(
                "SELECT * FROM productos WHERE nombre LIKE ?", ("%" + nombre + "%",)
            )
            fila = cur.fetchone()
        if fila:
            prod = Producto(*fila)
            self.log_action(actor_id, "productos", "SELECT", prod.id)
            return prod
        return None

    def actualizar_producto(self, producto_id, nueva_cantidad, nuevo_precio, actor_id):
        updates, params = [], []
        if nueva_cantidad is not None:
            updates.append("cantidad = ?")
            params.append(nueva_cantidad)
        if nuevo_precio is not None:
            updates.append("precio = ?")
            params.append(nuevo_precio)
        if not updates:
            print("No se especificó cantidad o precio para actualizar")
            return False

        params.append(producto_id)
        sql = f"UPDATE productos SET {', '.join(updates)} WHERE id = ?"
        with self._conect() as c:
            cur = c.cursor()
            cur.execute(sql, tuple(params))
            c.commit()
            success = cur.rowcount > 0

        if success:
            print(f"Producto ID {producto_id} actualizado correctamente.")
            self.log_action(actor_id, "productos", "UPDATE", producto_id)
        return success

    def eliminar_producto(self, producto_id, actor_id):
        with self._conect() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
            c.commit()
            success = cur.rowcount > 0

        if success:
            print(f"Producto ID {producto_id} eliminado correctamente.")
            self.log_action(actor_id, "productos", "DELETE", producto_id)
        return success

    # — CRUD de Empleados —
    def agregar_empleado(self, nombre, password, apellido, cargo, salario, actor_id):
        with self._conect() as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO empleados (nombre, apellido, cargo, salario, password) VALUES (?, ?, ?, ?, ?)",
                (nombre, apellido, cargo, salario, password),
            )
            c.commit()
            emp_id = cur.lastrowid
        print(f"Empleado '{nombre} {apellido}' agregado (ID {emp_id}).")
        self.log_action(actor_id, "empleados", "INSERT", emp_id)

    def obtener_empleados(self):
        empleados = []
        with self._conect() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM empleados")
            for fila in cur.fetchall():
                empleados.append(Empleado(*fila))
        return empleados

    def buscar_empleado_por_id(self, empleado_id):
        with self._conect() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM empleados WHERE id = ?", (empleado_id,))
            fila = cur.fetchone()
        return Empleado(*fila) if fila else None

    def buscar_empleado_por_nombre(self, nombre, actor_id):
        with self._conect() as c:
            cur = c.cursor()
            cur.execute(
                "SELECT * FROM empleados WHERE nombre LIKE ?", ("%" + nombre + "%",)
            )
            fila = cur.fetchone()
        if fila:
            emp = Empleado(*fila)
            self.log_action(actor_id, "empleados", "SELECT", emp.id)
            return emp
        return None

    def actualizar_empleado(self, empleado_id, nuevo_cargo, nuevo_salario, actor_id):
        updates, params = [], []
        if nuevo_cargo is not None:
            updates.append("cargo = ?")
            params.append(nuevo_cargo)
        if nuevo_salario is not None:
            updates.append("salario = ?")
            params.append(nuevo_salario)
        if not updates:
            print("No se especificó cargo o salario para actualizar.")
            return False

        params.append(empleado_id)
        sql = f"UPDATE empleados SET {', '.join(updates)} WHERE id = ?"
        with self._conect() as c:
            cur = c.cursor()
            cur.execute(sql, tuple(params))
            c.commit()
            success = cur.rowcount > 0

        if success:
            print(f"Empleado ID {empleado_id} actualizado correctamente.")
            self.log_action(actor_id, "empleados", "UPDATE", empleado_id)
        return success

    def eliminar_empleado(self, empleado_id, actor_id):
        with self._conect() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM empleados WHERE id = ?", (empleado_id,))
            c.commit()
            success = cur.rowcount > 0

        if success:
            print(f"Empleado ID {empleado_id} eliminado correctamente.")
            self.log_action(actor_id, "empleados", "DELETE", empleado_id)
        return success

    # — Consulta de auditoría —
    def ver_auditoria(self, actor_id):
        usr = self.buscar_empleado_por_id(actor_id)
        if not usr or usr.cargo.lower() != "gerente":
            print("Acceso denegado: sólo Gerente.")
            return []
        with self._conect() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")
            return cur.fetchall()


# MENÚ


# Vista completa del inventario para el gerente
def mostrar_menu_gerente():
    print(
        """
    --- Menú de Inventario & Empleados ---
    1. Agregar Producto
    2. Ver Todos los Productos
    3. Buscar Producto por Nombre
    4. Actualizar Producto por ID
    5. Eliminar Producto por ID
    6. Agregar Empleado
    7. Ver Todos los Empleados
    8. Buscar Empleado por Nombre
    9. Actualizar Empleado por ID
    10. Eliminar Empleado por ID
    11. Ver Auditoría (Gerente)
    12. Salir
    -------------------------------------
    """
    )


# Vista limitada para un empleado preservando la info-sec.
def mostrar_menu_empleado():
    print(
        """
    ---------- Menú de Empleado ---------
    1. Ver Productos
    2. Buscar Producto por Nombre
    3. Ver Empleados    
    4. Buscar Empleado por Nombre
    5. Salir
    -------------------------------------
    """
    )


def obtener_entrada(mensaje, tipo=str, obligatorio=True):
    while True:
        val = input(mensaje).strip()
        if not val and obligatorio:
            print("Entrada no puede estar vacía.")
            continue
        if tipo is int:
            try:
                return int(val)
            except ValueError:
                print("Debes ingresar un número válido.")
        elif tipo is float:
            try:
                return float(val)
            except ValueError:
                print("Debes ingresar un valor numérico.")
        else:
            return val


if __name__ == "__main__":
    inv = Inventario()

    # — Inicio de sesión de empleado CON CONTRASEÑA —
    current = None
    while not current:
        print("\n--- Iniciar Sesión ---")
        eid = obtener_entrada("Tu ID de Empleado: ", int)
        user = inv.buscar_empleado_por_id(eid)
        if not user:
            print("ID inválido. Intenta de nuevo.")
            continue

        # Contraseña = <ID> + '420'
        expected_pwd = f"{eid}420"
        pwd = input("Contraseña: ").strip()
        if pwd == expected_pwd:
            current = user
        else:
            print("Contraseña incorrecta. Vuelve a intentarlo.")

    print(f"\nBienvenido, {current.nombre} {current.apellido} ({current.cargo})\n")

    # — Bucle principal —
    while True:
        # Si el cargo de quien inició sesión es distinto
        # a gerente entonces mostrar menú de empleado
        if current.cargo.lower() != "gerente":
            mostrar_menu_empleado()
            opcion = input("Seleccione una opción: ").strip()
            if opcion == "1":
                for pr in inv.obtener_productos():
                    print(pr)

            elif opcion == "2":
                n = obtener_entrada("Nombre a buscar: ")
                pr = inv.buscar_producto_por_nombre(n, actor_id=current.id)
                print(pr if pr else "No encontrado.")

            elif opcion == "3":
                for emp in inv.obtener_empleados():
                    print(emp)

            elif opcion == "4":
                n = obtener_entrada("Nombre a buscar: ")
                emp = inv.buscar_empleado_por_nombre(n, actor_id=current.id)
                print(emp if emp else "No encontrado.")

            elif opcion == "5":
                print("¡Hasta luego!")
                break
            else:
                print("Opción inválida. Selecciona del 1 al 5.")
        else:
            # Gerente
            # Si es gerente, mostrar su respectivo menú
            mostrar_menu_gerente()
            opcion = input("Seleccione una opción: ").strip()
            if opcion == "1":
                n = obtener_entrada("Nombre producto: ")
                c = obtener_entrada("Cantidad: ", int)
                p = obtener_entrada("Precio: ", float)
                inv.agregar_product(n, c, p, actor_id=current.id)

            elif opcion == "2":
                for pr in inv.obtener_productos():
                    print(pr)

            elif opcion == "3":
                n = obtener_entrada("Nombre a buscar: ")
                pr = inv.buscar_producto_por_nombre(n, actor_id=current.id)
                print(pr if pr else "No encontrado.")

            elif opcion == "4":
                pid = obtener_entrada("ID producto: ", int)
                nc = input("Nueva cantidad (dejar vacío): ").strip()
                np = input("Nuevo precio (dejar vacío): ").strip()
                nc = int(nc) if nc else None
                np = float(np) if np else None
                inv.actualizar_producto(pid, nc, np, actor_id=current.id)

            elif opcion == "5":
                pid = obtener_entrada("ID producto a eliminar: ", int)
                inv.eliminar_producto(pid, actor_id=current.id)

            # Empleados
            elif opcion == "6":
                n = obtener_entrada("Nombre: ")
                ap = obtener_entrada("Apellido: ")
                ca = obtener_entrada("Cargo: ")
                sa = obtener_entrada("Salario: ", float)
                pw = obtener_entrada("Contraseña: ", str)

                inv.agregar_empleado(n, pw, ap, ca, sa, actor_id=current.id)

            elif opcion == "7":
                for emp in inv.obtener_empleados():
                    print(emp)

            elif opcion == "8":
                n = obtener_entrada("Nombre a buscar: ")
                emp = inv.buscar_empleado_por_nombre(n, actor_id=current.id)
                print(emp if emp else "No encontrado.")

            elif opcion == "9":
                eid = obtener_entrada("ID empleado: ", int)
                nc = input("Nuevo cargo (dejar vacío): ").strip() or None
                ns = input("Nuevo salario (dejar vacío): ").strip()
                ns = float(ns) if ns else None
                inv.actualizar_empleado(eid, nc, ns, actor_id=current.id)

            elif opcion == "10":
                eid = obtener_entrada("ID empleado a eliminar: ", int)
                inv.eliminar_empleado(eid, actor_id=current.id)

            # Auditoría
            elif opcion == "11":
                logs = inv.ver_auditoria(actor_id=current.id)
                if logs:
                    for _id, emp_id, tabla, acc, rid, ts in logs:
                        print(f"[{ts}] Emp {emp_id} • {acc} • {tabla}#{rid}")
                else:
                    print("Sin registros o acceso denegado.")

            elif opcion == "12":
                print("¡Hasta luego!")
                break

            else:
                print("Opción inválida. Selecciona del 1 al 12.")

            # Productos
