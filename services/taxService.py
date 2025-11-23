from datetime import datetime
from typing import Dict, List, Optional
from config.firebaseConfig import firebase_config
from config.settings import Settings
from utils.logger import app_logger, log_audit
from utils.validators import validate_factor_sum
from services.firebaseWrapper import requires_connection, FirebaseServiceBase


class CalificacionTributariaService(FirebaseServiceBase):
    """Servicio para gestionar calificaciones tributarias (CRUD)"""
    
    def __init__(self):
        self.db = firebase_config.get_firestore_client()
        self.datos_ref = self.db.collection(Settings.COLLECTION_DATOS_TRIBUTARIOS)
        self.clientes_ref = self.db.collection(Settings.COLLECTION_USUARIOS)

    @requires_connection
    def crear_calificacion(self, datos: Dict, usuario_id: str) -> Dict:
        """
        Crea una nueva calificación tributaria LOCAL
        
        Args:
            datos (Dict): Datos de la calificación
            usuario_id (str): ID del usuario que crea
            
        Returns:
            Dict: {"success": bool, "message": str, "calificacion_id": str}
        """
        try:
            # Validar datos
            es_valido, mensaje = self._validar_datos(datos)
            if not es_valido:
                return {"success": False, "message": mensaje}
            
            cliente_id, error = self._validate_cliente(datos.get("cliente_id"))

            if not cliente_id:
                return {
                    "success": False,
                    "message": f"No se puede crear la calificación: {error}",
                    "cliente_no_registrado": True
                }
            
            fecha_str = datos["fecha_declaracion"].strftime("%Y-%m-%d")
            conflicto = self.buscar_conflicto_oficial(
                cliente_id,
                fecha_str,
                datos["tipo_impuesto"]
            )
            
            if conflicto:
                return {
                    "success": False,
                    "message": "Ya existe una calificación oficial de bolsa con estos datos",
                    "conflicto": True,
                    "dato_oficial": {
                        "id": conflicto["_id"],
                        "monto": conflicto.get("montoDeclarado", 0),
                        "fecha": conflicto.get("fechaDeclaracion", "")
                    }
                }
            
            # Preparar documento
            calificacion = {
                "clienteId": cliente_id,
                "usuarioCargaId": usuario_id,
                "propietarioRegistroId": usuario_id,
                "fechaDeclaracion": datos["fecha_declaracion"].strftime("%Y-%m-%d"),
                "tipoImpuesto": datos["tipo_impuesto"],
                "pais": datos["pais"],
                "montoDeclarado": float(datos["monto_declarado"]),
                "factores": self._preparar_factores(datos["factores"]),
                "subsidiosAplicados": datos.get("subsidios_aplicados", []),
                "esLocal": True,  # ← CRÍTICO: Marca como local
                "fechaCreacion": datetime.now(),
                "fechaModificacion": datetime.now(),
                "activo": True
            }
            
            # Guardar en Firestore
            doc_ref = self.datos_ref.add(calificacion)
            calificacion_id = doc_ref[1].id
            
            # Auditoría
            log_audit(
                action="CALIFICACION_CREADA",
                user_id=usuario_id,
                details={"calificacion_id": calificacion_id, "cliente_id": cliente_id}
            )
            
            app_logger.info(f"Calificación creada: {calificacion_id}")
            
            return {
                "success": True,
                "message": "Calificación creada exitosamente",
                "calificacion_id": calificacion_id
            }
        
        except Exception as e:
            app_logger.error(f"Error al crear calificación: {str(e)}")
            return {"success": False, "message": f"Error al crear: {str(e)}"}
    
    def actualizar_calificacion(self, calificacion_id: str, datos: Dict, usuario_id: str, rol: str = None) -> Dict:
        """
        Actualiza una calificación LOCAL existente
        
        Args:
            calificacion_id (str): ID de la calificación
            datos (Dict): Nuevos datos
            usuario_id (str): ID del usuario que actualiza
            
        Returns:
            Dict: {"success": bool, "message": str}
        """
        try:
            # Verificar que existe
            doc = self.datos_ref.document(calificacion_id).get()
            if not doc.exists:
                return {"success": False, "message": "Calificación no encontrada"}
            
            calificacion_actual = doc.to_dict()
            
            if rol == "administrador":
                # Admin puede editar TODO (incluso datos de bolsa si es necesario)
                pass  # Continuar sin restricciones
            else:
                # Usuario normal: solo puede editar sus datos locales
                if not calificacion_actual.get("esLocal", False):
                    return {
                        "success": False,
                        "message": "No se puede modificar una calificación de bolsa"
                    }
                
                if calificacion_actual.get("propietarioRegistroId") != usuario_id:
                    return {
                        "success": False,
                        "message": "No tiene permisos para editar esta calificación"
                    }
            
            # Validar datos
            es_valido, mensaje = self._validar_datos(datos)
            if not es_valido:
                return {"success": False, "message": mensaje}
            
            # Preparar actualización
            actualizacion = {
                "fechaDeclaracion": datos["fecha_declaracion"].strftime("%Y-%m-%d"),
                "tipoImpuesto": datos["tipo_impuesto"],
                "pais": datos["pais"],
                "montoDeclarado": float(datos["monto_declarado"]),
                "factores": self._preparar_factores(datos["factores"]),
                "subsidiosAplicados": datos.get("subsidios_aplicados", []),
                "fechaModificacion": datetime.now()
            }
            
            # Actualizar en Firestore
            self.datos_ref.document(calificacion_id).update(actualizacion)
            
            # Auditoría
            log_audit(
                action="CALIFICACION_ACTUALIZADA",
                user_id=usuario_id,
                details={"calificacion_id": calificacion_id}
            )
            
            app_logger.info(f"Calificación actualizada: {calificacion_id}")
            
            return {
                "success": True,
                "message": "Calificación actualizada exitosamente"
            }
        
        except Exception as e:
            app_logger.error(f"Error al actualizar calificación: {str(e)}")
            return {"success": False, "message": f"Error al actualizar: {str(e)}"}
    
    def eliminar_calificacion(self, calificacion_id: str, usuario_id: str, rol: str = None) -> Dict:
        """
        Elimina (desactiva) una calificación LOCAL
        
        Args:
            calificacion_id (str): ID de la calificación
            usuario_id (str): ID del usuario que elimina
            
        Returns:
            Dict: {"success": bool, "message": str}
        """
        try:
            # Verificar que existe
            doc = self.datos_ref.document(calificacion_id).get()
            if not doc.exists:
                return {"success": False, "message": "Calificación no encontrada"}
            
            calificacion = doc.to_dict()
            
            if rol == "administrador":
                # Admin puede eliminar TODO
                pass  # Continuar sin restricciones
            else:
                # Usuario normal: solo puede eliminar sus datos locales
                if not calificacion.get("esLocal", False):
                    return {
                        "success": False,
                        "message": "No se puede eliminar una calificación de bolsa"
                    }
                
                if calificacion.get("propietarioRegistroId") != usuario_id:
                    return {
                        "success": False,
                        "message": "No tiene permisos para eliminar esta calificación"
                    }
            
            # Soft delete (marcar como inactivo)
            self.datos_ref.document(calificacion_id).update({
                "activo": False,
                "fechaEliminacion": datetime.now()
            })
            
            # Auditoría
            log_audit(
                action="CALIFICACION_ELIMINADA",
                user_id=usuario_id,
                details={"calificacion_id": calificacion_id}
            )
            
            app_logger.info(f"Calificación eliminada: {calificacion_id}")
            
            return {
                "success": True,
                "message": "Calificación eliminada exitosamente"
            }
        
        except Exception as e:
            app_logger.error(f"Error al eliminar calificación: {str(e)}")
            return {"success": False, "message": f"Error al eliminar: {str(e)}"}
    
    def obtener_calificacion(self, calificacion_id: str) -> Optional[Dict]:
        """
        Obtiene una calificación por ID
        
        Args:
            calificacion_id (str): ID de la calificación
            
        Returns:
            Dict: Datos de la calificación o None
        """
        try:
            doc = self.datos_ref.document(calificacion_id).get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            data["_id"] = doc.id
            
            return data
        
        except Exception as e:
            app_logger.error(f"Error al obtener calificación: {str(e)}")
            return None
    
    def buscar_conflicto_oficial(self, cliente_id: str, fecha: str, tipo_impuesto: str) -> Optional[Dict]:
        """
        Busca si existe un dato oficial (bolsa) para los mismos parámetros
        
        Args:
            cliente_id (str): ID del cliente
            fecha (str): Fecha de declaración (formato YYYY-MM-DD)
            tipo_impuesto (str): Tipo de impuesto
            
        Returns:
            Dict: Datos del documento oficial si existe, None si no
        """
        try:
            # Convertir fecha a string si es necesario
            if hasattr(fecha, 'strftime'):
                fecha_str = fecha.strftime("%Y-%m-%d")
            else:
                fecha_str = str(fecha)
            
            query = self.datos_ref.where("clienteId", "==", cliente_id)\
                                .where("fechaDeclaracion", "==", fecha_str)\
                                .where("tipoImpuesto", "==", tipo_impuesto)\
                                .where("esLocal", "==", False)\
                                .where("activo", "==", True)\
                                .limit(1)
            
            results = query.stream()
            
            for doc in results:
                data = doc.to_dict()
                data["_id"] = doc.id
                return data
            
            return None
            
        except Exception as e:
            app_logger.error(f"Error al buscar conflicto oficial: {str(e)}")
            return None

    
    def listar_calificaciones(self, usuario_id: str, rol: str = None, filtros: Optional[Dict] = None) -> List[Dict]:
        """
        Lista las calificaciones del usuario (locales + bolsa)
        
        Args:
            usuario_id (str): ID del usuario
            rol (str): Rol del usuario (administrador, analista_mercado, etc.)
            filtros (Dict): Filtros opcionales
            
        Returns:
            List[Dict]: Lista de calificaciones
        """
        try:
            # Query base: solo activas
            query = self.datos_ref.where("activo", "==", True)
            
            # Filtro por usuario (solo sus calificaciones locales)
            # Las de bolsa (esLocal=False) se muestran a todos
            
            # Aplicar filtros opcionales
            if filtros:
                if "fecha_desde" in filtros:
                    fecha_str = filtros["fecha_desde"].strftime("%Y-%m-%d")
                    query = query.where("fechaDeclaracion", ">=", fecha_str)
                
                if "fecha_hasta" in filtros:
                    fecha_str = filtros["fecha_hasta"].strftime("%Y-%m-%d")
                    query = query.where("fechaDeclaracion", "<=", fecha_str)
                
                if "tipo_impuesto" in filtros:
                    query = query.where("tipoImpuesto", "==", filtros["tipo_impuesto"])
                
                if "pais" in filtros:
                    query = query.where("pais", "==", filtros["pais"])
            
            # Ejecutar query
            docs = query.stream()
            
            calificaciones = []
            for doc in docs:
                data = doc.to_dict()
                data["_id"] = doc.id
                
                es_local = data.get("esLocal", False)
                es_propietario = data.get("propietarioRegistroId") == usuario_id
                
                if rol == "administrador":
                    # Admin ve TODAS las calificaciones
                    calificaciones.append(data)
                elif not es_local:
                    # Datos de bolsa: TODOS los ven
                    calificaciones.append(data)
                elif es_propietario:
                    # Datos locales: solo el propietario
                    calificaciones.append(data)
            
            app_logger.info(f"Listadas {len(calificaciones)} calificaciones para rol {rol}")
            return calificaciones
        
        except Exception as e:
            app_logger.error(f"Error al listar calificaciones: {str(e)}")
            return []
    
    def _validar_datos(self, datos: Dict) -> tuple:
        """Valida los datos de una calificación"""
        # Validar campos requeridos
        requeridos = ["fecha_declaracion", "tipo_impuesto", "pais", "monto_declarado", "factores"]
        for campo in requeridos:
            if campo not in datos or not datos[campo]:
                return False, f"El campo '{campo}' es requerido"
        
        # Validar monto positivo
        if datos["monto_declarado"] <= 0:
            return False, "El monto declarado debe ser positivo"
        
        # Validar que haya 19 factores
        if len(datos["factores"]) != 19:
            return False, "Se requieren exactamente 19 factores"
        
        # Validar rangos de factores
        for i, valor in enumerate(datos["factores"], 1):
            if not (0 <= valor <= 1):
                return False, f"El factor {i} debe estar entre 0 y 1"
        
        # Validar suma de factores 8-19 (REQUERIMIENTO A-01)
        factores_dict = {f"factor_{i}": datos["factores"][i-1] for i in range(1, 20)}
        es_valido, mensaje = validate_factor_sum(factores_dict, start=8, end=19)
        
        if not es_valido:
            return False, mensaje
        
        return True, "Validación exitosa"
    
    def _preparar_factores(self, factores: List[float]) -> Dict:
        """Convierte lista de factores a diccionario"""
        return {f"factor_{i}": float(factores[i-1]) for i in range(1, 20)}
    
    def _validate_cliente(self, rut: str) -> tuple:
        """
        Valida que un cliente exista en la base de datos
        NO CREA clientes nuevos
        
        Args:
            rut (str): RUT del cliente
            
        Returns:
            tuple: (cliente_id, error_message)
                Si existe: (cliente_id, None)
                Si no existe: (None, "mensaje de error")
        """
        try:
            # Buscar cliente existente
            query = self.clientes_ref.where("rut", "==", rut).limit(1)
            results = query.stream()
            
            for doc in results:
                app_logger.debug(f"Cliente encontrado: {rut}")
                return doc.id, None
            
            # Cliente NO existe
            error_msg = f"Cliente con RUT {rut} no está registrado en el sistema"
            app_logger.warning(error_msg)
            return None, error_msg
            
        except Exception as e:
            error_msg = f"Error al buscar cliente {rut}: {str(e)}"
            app_logger.error(error_msg)
            return None, error_msg