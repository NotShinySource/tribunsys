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
        self.clientes_ref = self.db.collection(Settings.COLLECTION_CLIENTES)
    
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
            
            # Buscar o crear cliente
            cliente_id = self._get_or_create_cliente(datos.get("cliente_id"))
            if not cliente_id:
                return {"success": False, "message": "Error al obtener/crear cliente"}
            
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
    
    def actualizar_calificacion(self, calificacion_id: str, datos: Dict, usuario_id: str) -> Dict:
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
            
            # Verificar que es LOCAL
            if not calificacion_actual.get("esLocal", False):
                return {
                    "success": False,
                    "message": "No se puede modificar una calificación de bolsa"
                }
            
            # Verificar que es del usuario (o es admin)
            if calificacion_actual.get("propietarioRegistroId") != usuario_id:
                # TODO: Verificar si es admin
                pass
            
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
    
    def eliminar_calificacion(self, calificacion_id: str, usuario_id: str) -> Dict:
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
            
            # Verificar que es LOCAL
            if not calificacion.get("esLocal", False):
                return {
                    "success": False,
                    "message": "No se puede eliminar una calificación de bolsa"
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
    
    def listar_calificaciones(self, usuario_id: str, filtros: Optional[Dict] = None) -> List[Dict]:
        """
        Lista las calificaciones del usuario (locales + bolsa)
        
        Args:
            usuario_id (str): ID del usuario
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
                
                # Incluir si:
                # 1. Es de bolsa (esLocal=False) -> todos la ven
                # 2. Es local del usuario (propietarioRegistroId == usuario_id)
                es_local = data.get("esLocal", False)
                es_propietario = data.get("propietarioRegistroId") == usuario_id
                
                if not es_local or es_propietario:
                    calificaciones.append(data)
            
            app_logger.info(f"Listadas {len(calificaciones)} calificaciones")
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
    
    def _get_or_create_cliente(self, cliente_rut: str) -> Optional[str]:
        """Busca o crea un cliente por RUT"""
        try:
            # Buscar cliente existente
            query = self.clientes_ref.where("rut", "==", cliente_rut).limit(1)
            results = query.stream()
            
            for doc in results:
                return doc.id
            
            # Si no existe, crear cliente básico
            nuevo_cliente = {
                "rut": cliente_rut,
                "nombre": "Cliente",
                "apellido_P": "Importado",
                "apellido_M": "",
                "correo": f"{cliente_rut.replace('-', '')}@temp.com",
                "razon_social": f"Cliente {cliente_rut}",
                "sector_economico": "No especificado",
                "direccion": "",
                "pais": "Chile",
                "fecha_creacion": datetime.now()
            }
            
            doc_ref = self.clientes_ref.add(nuevo_cliente)
            cliente_id = doc_ref[1].id
            
            app_logger.info(f"Cliente creado automáticamente: {cliente_rut}")
            return cliente_id
        
        except Exception as e:
            app_logger.error(f"Error al obtener/crear cliente: {str(e)}")
            return None