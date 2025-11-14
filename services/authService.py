"""
TribunSys - Servicio de Autenticación
Maneja la lógica de autenticación con Firebase
"""

from datetime import datetime, timezone, timedelta
from config.firebaseConfig import firebase_config
from config.settings import Settings
from utils.encryption import verify_password
from utils.logger import app_logger


class AuthService:
    """Servicio para gestionar autenticación de usuarios"""
    
    def __init__(self):
        self.db = firebase_config.get_firestore_client()
        self.auth_client = firebase_config.get_auth_client()
        self.usuarios_ref = self.db.collection(Settings.COLLECTION_USUARIOS)
        # Zona horaria de Chile (UTC-3 o UTC-4 según horario de verano)
        self.chile_tz = timezone(timedelta(hours=-3))
    
    def get_chile_time(self):
        """Retorna la fecha/hora actual en zona horaria de Chile"""
        return datetime.now(self.chile_tz)
    
    def login(self, rut: str, password: str) -> dict:
        """
        Autentica un usuario
        
        Args:
            rut (str): RUT del usuario
            password (str): Contraseña en texto plano
            
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "user": dict (si success=True)
            }
        """
        try:
            # Buscar usuario por RUT
            query = self.usuarios_ref.where("rut", "==", rut).limit(1)
            users = query.stream()
            
            user_doc = None
            for doc in users:
                user_doc = doc
                break
            
            if not user_doc:
                app_logger.warning(f"Intento de login con RUT no registrado: {rut}")
                return {
                    "success": False,
                    "message": "RUT o contraseña incorrectos"
                }
            
            # Obtener datos del usuario
            user_data = user_doc.to_dict()
            user_data["_id"] = user_doc.id
            
            # Verificar contraseña
            stored_password = user_data.get("contraseña", "")
            
            if not verify_password(password, stored_password):
                app_logger.warning(f"Contraseña incorrecta para RUT: {rut}")
                return {
                    "success": False,
                    "message": "RUT o contraseña incorrectos"
                }
            
            # Actualizar último acceso con hora de Chile
            self.usuarios_ref.document(user_doc.id).update({
                "ultimoAcceso": self.get_chile_time()
            })
            
            app_logger.info(f"Login exitoso para usuario: {rut}")
            
            # No retornar la contraseña
            user_data.pop("contraseña", None)
            
            return {
                "success": True,
                "message": "Login exitoso",
                "user": user_data
            }
        
        except Exception as e:
            app_logger.error(f"Error durante el login: {str(e)}")
            return {
                "success": False,
                "message": "Error al autenticar. Por favor intente nuevamente."
            }
    
    def register(self, user_data: dict) -> dict:
        """
        Registra un nuevo usuario
        
        Args:
            user_data (dict): Datos del usuario a registrar
            
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "user_id": str (si success=True)
            }
        """
        try:
            rut = user_data.get("rut")
            
            # Verificar si el RUT ya existe
            existing_user = self.usuarios_ref.where("rut", "==", rut).limit(1).get()
            
            if len(list(existing_user)) > 0:
                return {
                    "success": False,
                    "message": "El RUT ya está registrado en el sistema"
                }
            
            # Agregar campos de auditoría con hora de Chile
            user_data["fechaRegistro"] = self.get_chile_time()
            user_data["ultimoAcceso"] = None
            
            # Crear usuario en Firestore
            doc_ref = self.usuarios_ref.add(user_data)
            user_id = doc_ref[1].id
            
            app_logger.info(f"Usuario registrado exitosamente: {rut}")
            
            return {
                "success": True,
                "message": "Usuario registrado exitosamente",
                "user_id": user_id
            }
        
        except Exception as e:
            app_logger.error(f"Error durante el registro: {str(e)}")
            return {
                "success": False,
                "message": "Error al registrar usuario. Por favor intente nuevamente."
            }
    
    def logout(self, user_id: str):
        """
        Cierra la sesión del usuario
        
        Args:
            user_id (str): ID del usuario
        """
        try:
            # Registrar hora de cierre de sesión con hora de Chile
            self.usuarios_ref.document(user_id).update({
                "ultimaSesionCerrada": self.get_chile_time()
            })
            
            app_logger.info(f"Sesión cerrada para usuario ID: {user_id}")
        
        except Exception as e:
            app_logger.error(f"Error al cerrar sesión: {str(e)}")
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> dict:
        """
        Cambia la contraseña de un usuario
        
        Args:
            user_id (str): ID del usuario
            old_password (str): Contraseña actual
            new_password (str): Nueva contraseña
            
        Returns:
            dict: {"success": bool, "message": str}
        """
        try:
            # Obtener usuario
            user_doc = self.usuarios_ref.document(user_id).get()
            
            if not user_doc.exists:
                return {
                    "success": False,
                    "message": "Usuario no encontrado"
                }
            
            user_data = user_doc.to_dict()
            
            # Verificar contraseña actual
            if not verify_password(old_password, user_data.get("contraseña", "")):
                return {
                    "success": False,
                    "message": "La contraseña actual es incorrecta"
                }
            
            # Actualizar contraseña
            from utils.encryption import hash_password
            new_hashed_password = hash_password(new_password)
            
            self.usuarios_ref.document(user_id).update({
                "contraseña": new_hashed_password,
                "fechaCambioContraseña": self.get_chile_time()
            })
            
            app_logger.info(f"Contraseña cambiada para usuario ID: {user_id}")
            
            return {
                "success": True,
                "message": "Contraseña actualizada exitosamente"
            }
        
        except Exception as e:
            app_logger.error(f"Error al cambiar contraseña: {str(e)}")
            return {
                "success": False,
                "message": "Error al cambiar contraseña"
            }