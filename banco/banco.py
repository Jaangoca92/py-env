"""
===============================================================================
           SISTEMA CORE BANCARIO ENTERPRISE - EDITION 2026
===============================================================================
Diseñado para entornos de hardware limitado (32-bit / 2GB RAM / Windows 7)
Compatibilidad: Python 3.8.9 + VS Code 1.70.2
Librerías: Estándar (Zero-Dependency para máximo rendimiento)
===============================================================================
"""

# =============================================================================
# SECCIÓN 1: IMPORTACIONES ESTÁNDAR
# =============================================================================
import os
import sys
import json
import uuid
import re
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime, timezone

# =============================================================================
# SECCIÓN 2: AUDITORÍA Y LOGS
# =============================================================================
logging.basicConfig(
    filename="banco_audit.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)

# =============================================================================
# SECCIÓN 3: EXCEPCIONES DE DOMINIO BANCARIO
# =============================================================================
class ErrorBancario(Exception):
    """Excepción base para el dominio financiero."""

    pass


class SaldoInsuficienteError(ErrorBancario):
    """Lanzada cuando la cuenta no cuenta con liquidez suficiente."""

    pass


class CuentaNoEncontradaError(ErrorBancario):
    """Lanzada cuando la cuenta solicitada no existe."""

    pass


class CuentaBloqueadaError(ErrorBancario):
    """Lanzada cuando la cuenta ha superado el límite de intentos de PIN."""

    pass


class ErrorValidacionDatos(ErrorBancario):
    """Lanzada cuando un dato ingresado no cumple con las reglas de tipo/formato."""

    pass


class ErrorAutenticacion(ErrorBancario):
    """Lanzada ante fallos en la validación del PIN."""

    pass


# =============================================================================
# SECCIÓN 4: MOTOR DE VALIDACIÓN Y SANITIZACIÓN DE ENTRADAS
# =============================================================================
class ValidadorEntradas:
    """Clase estricta encargada de validar el tipo y contenido de cada dato."""

    # Expresión regular para nombres válidos (solo letras en español y espacios)
    PATRON_TEXTO_PURO = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$")

    # Expresión regular para alfanumérico estricto (letras y números sin símbolos)
    PATRON_ALFANUMERICO = re.compile(r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$")

    @classmethod
    def validar_texto_puro(
        cls, valor: str, nombre_campo: str, min_len: int = 2, max_len: int = 50
    ) -> str:
        """Valida que una cadena sea SOLO LETRAS y espacios (sin números ni símbolos)."""
        valor_limpio = valor.strip()
        if not valor_limpio:
            raise ErrorValidacionDatos(
                f"El campo '{nombre_campo}' no puede estar vacío."
            )
        if len(valor_limpio) < min_len or len(valor_limpio) > max_len:
            raise ErrorValidacionDatos(
                f"El campo '{nombre_campo}' debe tener entre {min_len} y {max_len} caracteres."
            )
        if not cls.PATRON_TEXTO_PURO.match(valor_limpio):
            raise ErrorValidacionDatos(
                f"El campo '{nombre_campo}' debe contener ÚNICAMENTE letras (sin números ni símbolos)."
            )

        # Normalizar espacios dobles y formato Nombre Propio
        return " ".join(valor_limpio.split()).title()

    @classmethod
    def validar_entero_puro(
        cls, valor: str, nombre_campo: str, longitud_exacta: Optional[int] = None
    ) -> int:
        """Valida que una entrada sea SOLO NÚMEROS ENTEROS (sin letras, decimales ni símbolos)."""
        valor_limpio = valor.strip()
        if not valor_limpio:
            raise ErrorValidacionDatos(f"El campo '{nombre_campo}' es obligatorio.")
        if not valor_limpio.isdigit():
            raise ErrorValidacionDatos(
                f"El campo '{nombre_campo}' debe contener ÚNICAMENTE números enteros."
            )
        if longitud_exacta and len(valor_limpio) != longitud_exacta:
            raise ErrorValidacionDatos(
                f"El campo '{nombre_campo}' debe tener exactamente {longitud_exacta} dígitos."
            )
        return int(valor_limpio)

    @classmethod
    def validar_monto_decimal(cls, valor: str, nombre_campo: str = "Monto") -> Decimal:
        """Valida que la entrada sea un DATO NUMÉRICO (Decimal/Float) positivo válido."""
        valor_limpio = valor.strip()
        if not valor_limpio:
            raise ErrorValidacionDatos(
                f"El campo '{nombre_campo}' no puede estar vacío."
            )

        # Verificar que solo contenga dígitos y opcionalmente un punto
        if not re.match(r"^\d+(\.\d+)?$", valor_limpio):
            raise ErrorValidacionDatos(
                f"El campo '{nombre_campo}' debe ser un número válido (ej. 100 o 150.50)."
            )

        try:
            monto = Decimal(valor_limpio)
            if monto <= Decimal("0.00"):
                raise ErrorValidacionDatos(
                    f"El {nombre_campo.lower()} debe ser estrictamente mayor a 0.00."
                )
            if monto.as_tuple().exponent < -2:
                raise ErrorValidacionDatos(
                    f"El {nombre_campo.lower()} no puede tener más de 2 decimales (centavos)."
                )
            return monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except InvalidOperation:
            raise ErrorValidacionDatos(
                f"El valor ingresado en '{nombre_campo}' no es un número válido."
            )

    @classmethod
    def validar_alfanumerico(
        cls, valor: str, nombre_campo: str, min_len: int = 1, max_len: int = 100
    ) -> str:
        """Valida que la entrada sea COMBINADA (Letras y Números permitidos)."""
        valor_limpio = valor.strip()
        if not valor_limpio:
            raise ErrorValidacionDatos(
                f"El campo '{nombre_campo}' no puede estar vacío."
            )
        if len(valor_limpio) < min_len or len(valor_limpio) > max_len:
            raise ErrorValidacionDatos(
                f"El campo '{nombre_campo}' debe tener entre {min_len} y {max_len} caracteres."
            )
        if not cls.PATRON_ALFANUMERICO.match(valor_limpio):
            raise ErrorValidacionDatos(
                f"El campo '{nombre_campo}' solo permite letras y números (sin caracteres especiales)."
            )
        return " ".join(valor_limpio.split())


# =============================================================================
# SECCIÓN 5: CRIPTOGRAFÍA Y SEGURIDAD
# =============================================================================
class CriptografiaUtils:
    """Implementa el cifrado de PINs usando PBKDF2-HMAC-SHA256 con Salt aleatorio."""

    @staticmethod
    def cifrar_pin(pin: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        if salt is None:
            salt = os.urandom(16)

        pin_cifrado = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 100_000)
        return pin_cifrado.hex(), salt.hex()

    @staticmethod
    def verificar_pin(
        pin_ingresado: str, hash_guardado: str, salt_guardado: str
    ) -> bool:
        salt_bytes = bytes.fromhex(salt_guardado)
        hash_calculado, _ = CriptografiaUtils.cifrar_pin(pin_ingresado, salt_bytes)
        return hash_calculado == hash_guardado


# =============================================================================
# SECCIÓN 6: MODELOS DE DATOS OPTIMIZADOS EN MEMORIA
# =============================================================================
class Transaccion:
    """Modelo de datos optimizado con __slots__ para minimizar uso de memoria RAM."""

    __slots__ = ("id_tx", "num_cuenta", "tipo", "monto", "fecha", "descripcion")

    def __init__(
        self,
        num_cuenta: str,
        tipo: str,
        monto: Decimal,
        descripcion: str,
        id_tx: str = None,
        fecha: str = None,
    ):
        self.id_tx = id_tx or str(uuid.uuid4())
        self.num_cuenta = num_cuenta
        self.tipo = tipo
        self.monto = monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.fecha = fecha or datetime.now(timezone.utc).isoformat()
        self.descripcion = descripcion

    def a_diccionario(self) -> dict:
        return {
            "id_tx": self.id_tx,
            "num_cuenta": self.num_cuenta,
            "tipo": self.tipo,
            "monto": str(self.monto),
            "fecha": self.fecha,
            "descripcion": self.descripcion,
        }


class CuentaBancaria:
    """Entidad de Cuenta con control de bloqueo e intentos fallidos."""

    __slots__ = (
        "num_cuenta",
        "titular",
        "saldo",
        "pin_hash",
        "pin_salt",
        "fecha_creacion",
        "activa",
        "intentos_fallidos",
        "bloqueada",
    )

    def __init__(
        self,
        num_cuenta: str,
        titular: str,
        pin: str,
        saldo: Decimal = Decimal("0.00"),
        pin_hash: str = None,
        pin_salt: str = None,
        fecha_creacion: str = None,
        activa: bool = True,
        intentos_fallidos: int = 0,
        bloqueada: bool = False,
    ):
        self.num_cuenta = num_cuenta
        self.titular = titular
        self.saldo = saldo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.activa = activa
        self.intentos_fallidos = intentos_fallidos
        self.bloqueada = bloqueada
        self.fecha_creacion = fecha_creacion or datetime.now(timezone.utc).isoformat()

        if pin_hash and pin_salt:
            self.pin_hash = pin_hash
            self.pin_salt = pin_salt
        else:
            self.pin_hash, self.pin_salt = CriptografiaUtils.cifrar_pin(pin)

    def validar_pin(self, pin_probar: str) -> bool:
        if self.bloqueada:
            raise CuentaBloqueadaError(
                "La cuenta se encuentra BLOQUEADA por seguridad debido a múltiples intentos fallidos."
            )

        es_valido = CriptografiaUtils.verificar_pin(
            pin_probar, self.pin_hash, self.pin_salt
        )

        if es_valido:
            self.intentos_fallidos = 0  # Reiniciar contador si acierta
        else:
            self.intentos_fallidos += 1
            if self.intentos_fallidos >= 3:
                self.bloqueada = True
                logging.warning(
                    f"CUENTA BLOQUEADA por 3 intentos fallidos de PIN: {self.num_cuenta}"
                )
                raise CuentaBloqueadaError(
                    "Ha ingresado un PIN incorrecto 3 veces. Su cuenta ha sido BLOQUEADA."
                )

        return es_valido

    def a_diccionario(self) -> dict:
        return {
            "num_cuenta": self.num_cuenta,
            "titular": self.titular,
            "saldo": str(self.saldo),
            "pin_hash": self.pin_hash,
            "pin_salt": self.pin_salt,
            "fecha_creacion": self.fecha_creacion,
            "activa": self.activa,
            "intentos_fallidos": self.intentos_fallidos,
            "bloqueada": self.bloqueada,
        }


# =============================================================================
# SECCIÓN 7: PERSISTENCIA ATÓMICA DE DATOS
# =============================================================================
class GestorBaseDatos:
    """Maneja la lectura y escritura atómica en archivo JSON."""

    __slots__ = ("ruta_archivo",)

    def __init__(self, ruta_archivo: str = "banco_datos.json"):
        self.ruta_archivo = ruta_archivo
        if not os.path.exists(self.ruta_archivo):
            self._guardado_atomico({"cuentas": {}, "transacciones": []})

    def _guardado_atomico(self, datos: dict) -> None:
        """Escritura atómica usando archivo temporal para prevenir corrupción."""
        ruta_temporal = f"{self.ruta_archivo}.tmp"
        try:
            with open(ruta_temporal, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            os.replace(ruta_temporal, self.ruta_archivo)
        except Exception as error:
            if os.path.exists(ruta_temporal):
                os.remove(ruta_temporal)
            logging.error(f"Fallo en guardado atómico: {str(error)}")
            raise ErrorBancario("Error al escribir los datos en disco.")

    def cargar_datos(self) -> Tuple[Dict[str, CuentaBancaria], List[Transaccion]]:
        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                datos_crudos = json.load(f)

            cuentas: Dict[str, CuentaBancaria] = {}
            for acc_num, c in datos_crudos.get("cuentas", {}).items():
                cuentas[acc_num] = CuentaBancaria(
                    num_cuenta=c["num_cuenta"],
                    titular=c["titular"],
                    pin="",
                    saldo=Decimal(c["saldo"]),
                    pin_hash=c["pin_hash"],
                    pin_salt=c["pin_salt"],
                    fecha_creacion=c["fecha_creacion"],
                    activa=c["activa"],
                    intentos_fallidos=c.get("intentos_fallidos", 0),
                    bloqueada=c.get("bloqueada", False),
                )

            transacciones: List[Transaccion] = []
            for t in datos_crudos.get("transacciones", []):
                transacciones.append(
                    Transaccion(
                        id_tx=t["id_tx"],
                        num_cuenta=t["num_cuenta"],
                        tipo=t["tipo"],
                        monto=Decimal(t["monto"]),
                        fecha=t["fecha"],
                        descripcion=t["descripcion"],
                    )
                )

            return cuentas, transacciones
        except (json.JSONDecodeError, KeyError) as e:
            logging.critical(f"Base de datos corrupta: {str(e)}")
            raise ErrorBancario("Base de datos local corrupta o no legible.")

    def guardar_todo(
        self, cuentas: Dict[str, CuentaBancaria], transacciones: List[Transaccion]
    ) -> None:
        estructura = {
            "cuentas": {
                acc_num: acc.a_diccionario() for acc_num, acc in cuentas.items()
            },
            "transacciones": [tx.a_diccionario() for tx in transacciones],
        }
        self._guardado_atomico(estructura)


# =============================================================================
# SECCIÓN 8: SERVICIO BANCARIO Y LÓGICA DE NEGOCIO
# =============================================================================
class ServicioBancario:
    """Implementa las reglas financieras del banco."""

    __slots__ = ("bd", "cuentas", "transacciones")

    def __init__(self, bd: GestorBaseDatos):
        self.bd = bd
        self.cuentas, self.transacciones = self.bd.cargar_datos()

    def crear_cuenta(
        self, nombre_raw: str, pin_raw: str, deposito_raw: str = "0.00"
    ) -> CuentaBancaria:
        # Validaciones de tipo estrictas
        titular = ValidadorEntradas.validar_texto_puro(
            nombre_raw, "Nombre del Titular", min_len=3, max_len=60
        )
        _ = ValidadorEntradas.validar_entero_puro(
            pin_raw, "PIN de Seguridad", longitud_exacta=4
        )
        monto_inicial = (
            ValidadorEntradas.validar_monto_decimal(deposito_raw, "Monto Inicial")
            if deposito_raw != "0.00"
            else Decimal("0.00")
        )

        # Generar número de cuenta numérico de 10 dígitos único
        numero_cuenta = str(uuid.uuid4().int)[:10]
        while numero_cuenta in self.cuentas:
            numero_cuenta = str(uuid.uuid4().int)[:10]

        nueva_cuenta = CuentaBancaria(
            num_cuenta=numero_cuenta,
            titular=titular,
            pin=pin_raw.strip(),
            saldo=monto_inicial,
        )
        self.cuentas[numero_cuenta] = nueva_cuenta

        if monto_inicial > Decimal("0.00"):
            tx = Transaccion(
                numero_cuenta,
                "DEPOSITO",
                monto_inicial,
                "Apertura de Cuenta - Depósito Inicial",
            )
            self.transacciones.append(tx)

        self.bd.guardar_todo(self.cuentas, self.transacciones)
        logging.info(f"Cuenta Aperturada: {numero_cuenta} - Titular: {titular}")
        return nueva_cuenta

    def obtener_cuenta(self, num_cuenta_raw: str) -> CuentaBancaria:
        _ = ValidadorEntradas.validar_entero_puro(
            num_cuenta_raw, "Número de Cuenta", longitud_exacta=10
        )
        cuenta = self.cuentas.get(num_cuenta_raw.strip())
        if not cuenta or not cuenta.activa:
            raise CuentaNoEncontradaError(
                "La cuenta especificada no existe o se encuentra inactiva."
            )
        return cuenta

    def autenticar_cliente(self, num_cuenta_raw: str, pin_raw: str) -> CuentaBancaria:
        cuenta = self.obtener_cuenta(num_cuenta_raw)
        _ = ValidadorEntradas.validar_entero_puro(
            pin_raw, "PIN de Seguridad", longitud_exacta=4
        )

        if not cuenta.validar_pin(pin_raw.strip()):
            self.bd.guardar_todo(
                self.cuentas, self.transacciones
            )  # Guardar el intento fallido
            intentos_restantes = 3 - cuenta.intentos_fallidos
            logging.warning(
                f"Intento de PIN fallido en cuenta {cuenta.num_cuenta}. Quedan {intentos_restantes} intentos."
            )
            raise ErrorAutenticacion(
                f"PIN incorrecto. Le quedan {intentos_restantes} intento(s) antes de bloquear la cuenta."
            )

        self.bd.guardar_todo(
            self.cuentas, self.transacciones
        )  # Guardar reinicio de intentos
        return cuenta

    def depositar(self, num_cuenta_raw: str, monto_raw: str) -> Decimal:
        cuenta = self.obtener_cuenta(num_cuenta_raw)
        monto = ValidadorEntradas.validar_monto_decimal(monto_raw, "Monto a depositar")

        cuenta.saldo += monto
        tx = Transaccion(
            cuenta.num_cuenta, "DEPOSITO", monto, "Depósito de fondos en efectivo"
        )
        self.transacciones.append(tx)

        self.bd.guardar_todo(self.cuentas, self.transacciones)
        logging.info(f"Depósito: ${monto} en cuenta {cuenta.num_cuenta}")
        return cuenta.saldo

    def retirar(self, num_cuenta_raw: str, pin_raw: str, monto_raw: str) -> Decimal:
        cuenta = self.autenticar_cliente(num_cuenta_raw, pin_raw)
        monto = ValidadorEntradas.validar_monto_decimal(monto_raw, "Monto a retirar")

        if cuenta.saldo < monto:
            raise SaldoInsuficienteError(
                f"Fondos insuficientes. Su saldo disponible es de ${cuenta.saldo}"
            )

        cuenta.saldo -= monto
        tx = Transaccion(cuenta.num_cuenta, "RETIRO", monto, "Retiro de efectivo")
        self.transacciones.append(tx)

        self.bd.guardar_todo(self.cuentas, self.transacciones)
        logging.info(f"Retiro: ${monto} de cuenta {cuenta.num_cuenta}")
        return cuenta.saldo

    def transferir(
        self,
        origen_raw: str,
        pin_raw: str,
        destino_raw: str,
        monto_raw: str,
        concepto_raw: str = "",
    ) -> Decimal:
        _ = ValidadorEntradas.validar_entero_puro(
            origen_raw, "Cuenta de Origen", longitud_exacta=10
        )
        _ = ValidadorEntradas.validar_entero_puro(
            destino_raw, "Cuenta de Destino", longitud_exacta=10
        )

        if origen_raw.strip() == destino_raw.strip():
            raise ErrorValidacionDatos(
                "No es posible transferir dinero a la misma cuenta de origen."
            )

        cuenta_origen = self.autenticar_cliente(origen_raw, pin_raw)
        cuenta_destino = self.obtener_cuenta(destino_raw)
        monto = ValidadorEntradas.validar_monto_decimal(monto_raw, "Monto a transferir")

        # Concepto es un campo alfanumérico opcional (combinado)
        concepto = (
            ValidadorEntradas.validar_alfanumerico(concepto_raw, "Concepto", 1, 50)
            if concepto_raw.strip()
            else "Transferencia de fondos"
        )

        if cuenta_origen.saldo < monto:
            raise SaldoInsuficienteError(
                f"Saldo insuficiente. Saldo disponible actual: ${cuenta_origen.saldo}"
            )

        # Transacción Atómica
        cuenta_origen.saldo -= monto
        cuenta_destino.saldo += monto

        tx_salida = Transaccion(
            cuenta_origen.num_cuenta,
            "TRANSFERENCIA_ENVIADA",
            monto,
            f"A CTA: {cuenta_destino.num_cuenta} - {concepto}",
        )
        tx_entrada = Transaccion(
            cuenta_destino.num_cuenta,
            "TRANSFERENCIA_RECIBIDA",
            monto,
            f"DE CTA: {cuenta_origen.num_cuenta} - {concepto}",
        )

        self.transacciones.extend([tx_salida, tx_entrada])

        try:
            self.bd.guardar_todo(self.cuentas, self.transacciones)
        except Exception:
            # Rollback
            cuenta_origen.saldo += monto
            cuenta_destino.saldo -= monto
            self.transacciones.pop()
            self.transacciones.pop()
            raise ErrorBancario(
                "Fallo de almacenamiento. La transferencia se ha revertido."
            )

        logging.info(
            f"Transferencia de ${monto} realizada de {cuenta_origen.num_cuenta} a {cuenta_destino.num_cuenta}"
        )
        return cuenta_origen.saldo

    def obtener_historial_movimientos(
        self, num_cuenta_raw: str, pin_raw: str
    ) -> List[Transaccion]:
        cuenta = self.autenticar_cliente(num_cuenta_raw, pin_raw)
        return [tx for tx in self.transacciones if tx.num_cuenta == cuenta.num_cuenta]


# =============================================================================
# SECCIÓN 9: INTERFAZ DE USUARIO CONSOLA (CLI)
# =============================================================================
def mostrar_menu_principal():
    print("\n" + "=" * 55)
    print("      SISTEMA BANCARIO CORE ENTERPRISE (32-bit)")
    print("=" * 55)
    print(" 1. 📋 Abrir una Nueva Cuenta Bancaria")
    print(" 2. 💵 Realizar un Depósito (Abonar)")
    print(" 3. 🏧 Realizar un Retiro")
    print(" 4. 🔄 Realizar una Transferencia")
    print(" 5. 📑 Consultar Saldo y Estado de Cuenta")
    print(" 6. 🚪 Salir del Sistema")
    print("=" * 55)


def ejecutor_sistema():
    bd = GestorBaseDatos()
    banco = ServicioBancario(bd)

    while True:
        mostrar_menu_principal()
        opcion = input("Seleccione una opción (1-6): ").strip()

        try:
            if opcion == "1":
                print("\n--- NUEVA APERTURA DE CUENTA ---")
                nombre = input("Nombre y Apellido del Titular (SOLO LETRAS): ")
                pin = input("PIN de Seguridad (EXACTAMENTE 4 NÚMEROS): ")
                deposito = (
                    input(
                        "Monto inicial de apertura (Opcional, [ENTER] para $0.00): "
                    ).strip()
                    or "0.00"
                )

                cuenta = banco.crear_cuenta(nombre, pin, deposito)
                print("\n✅ ¡CUENTA CREADA EXITOSAMENTE!")
                print(f" 📌 Número de Cuenta:        {cuenta.num_cuenta}")
                print(f" 👤 Titular Registrado:      {cuenta.titular}")
                print(f" 💰 Saldo Inicial Disponible: ${cuenta.saldo}")

            elif opcion == "2":
                print("\n--- MÓDULO DE DEPÓSITOS ---")
                num_cuenta = input("Número de Cuenta Destino (10 DÍGITOS): ")
                monto = input("Monto a depositar (NUMÉRICO): ")

                nuevo_saldo = banco.depositar(num_cuenta, monto)
                print(f"\n✅ Depósito completado. Nuevo saldo: ${nuevo_saldo}")

            elif opcion == "3":
                print("\n--- MÓDULO DE RETIROS ---")
                num_cuenta = input("Número de Cuenta (10 DÍGITOS): ")
                pin = input("PIN de Seguridad (4 DÍGITOS): ")
                monto = input("Monto a retirar (NUMÉRICO): ")

                nuevo_saldo = banco.retirar(num_cuenta, pin, monto)
                print(f"\n✅ Retiro completado. Nuevo saldo: ${nuevo_saldo}")

            elif opcion == "4":
                print("\n--- MÓDULO DE TRANSFERENCIAS ---")
                origen = input("Su Número de Cuenta (10 DÍGITOS): ")
                pin = input("Su PIN de Seguridad (4 DÍGITOS): ")
                destino = input("Número de Cuenta Destino (10 DÍGITOS): ")
                monto = input("Monto a transferir (NUMÉRICO): ")
                concepto = input("Concepto/Motivo (ALFANUMÉRICO, Opcional): ")

                nuevo_saldo = banco.transferir(origen, pin, destino, monto, concepto)
                print(f"\n✅ Transferencia completada con éxito.")
                print(f" 💰 Su saldo disponible restante es: ${nuevo_saldo}")

            elif opcion == "5":
                print("\n--- ESTADO DE CUENTA Y MOVIMIENTOS ---")
                num_cuenta = input("Número de Cuenta (10 DÍGITOS): ")
                pin = input("PIN de Seguridad (4 DÍGITOS): ")

                movimientos = banco.obtener_historial_movimientos(num_cuenta, pin)
                cuenta = banco.obtener_cuenta(num_cuenta)

                print("\n" + "-" * 65)
                print(f" DETALLE DE LA CUENTA: {cuenta.num_cuenta}")
                print(f" Titular: {cuenta.titular}")
                print(
                    f" Estado:  {'🟢 ACTIVA' if not cuenta.bloqueada else '🔴 BLOQUEADA'}"
                )
                print(f" Saldo Disponible: ${cuenta.saldo}")
                print("-" * 65)
                print(" MOVIMIENTOS REGISTRADOS:")

                if not movimientos:
                    print("  (No existen movimientos registrados para esta cuenta)")
                else:
                    for tx in movimientos:
                        fecha_f = tx.fecha[:19].replace("T", " ")
                        print(
                            f"  [{fecha_f}] {tx.tipo:<22} | ${tx.monto:>10} | {tx.descripcion}"
                        )
                print("-" * 65)

            elif opcion == "6":
                print("\n🔒 Finalizando sesión y guardando datos de forma segura...")
                sys.exit(0)

            else:
                print(
                    "\n❌ Opción no válida. Por favor, seleccione un número entre 1 y 6."
                )

        except ErrorBancario as err:
            print(f"\n⚠️  [RECHAZADO]: {str(err)}")
        except Exception as err:
            logging.error(f"Error no previsto: {str(err)}")
            print(
                f"\n❌ [ERROR GRAVE]: Ha ocurrido un error inesperado. Consulte el archivo de log."
            )

        input("\nPresione [ENTER] para continuar...")


if __name__ == "__main__":
    ejecutor_sistema()
