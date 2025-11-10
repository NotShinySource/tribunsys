import os
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
import warnings

_firebase_app = None
_db = None
warnings.filterwarnings("ignore", message="Detected filter using positional arguments.*")

def init_firebase():
    global _firebase_app, _db
    if _firebase_app is not None:
        return _db

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.join(current_dir, "assets", "db", "AccountKey.json")

        cred = credentials.Certificate(cred_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        _db = firestore.client()
        print("Conexión a Firebase exitosa.")
        return _db

    except Exception as e:
        print(f"Error al conectar con Firebase: {e}")
        return None


def get_user_by_rut(rut):
    db = init_firebase()
    if db is None:
        print("No hay conexión con Firebase.")
        return None

    try:
        # Primero buscamos en usuarios
        users_ref = db.collection("usuarios").where("rut", "==", rut)
        docs = users_ref.get()
        if docs:
            user_doc = docs[0]
            user_data = user_doc.to_dict()
            user_data["doc_id"] = user_doc.id
            print(f"Usuario encontrado en 'usuarios': {user_data}")
            return user_data

        # Si no se encuentra, buscamos en cliente
        clients_ref = db.collection("cliente").where("rut", "==", rut)
        docs = clients_ref.get()
        if docs:
            client_doc = docs[0]
            client_data = client_doc.to_dict()
            client_data["doc_id"] = client_doc.id
            # simulamos rol 'client' para consistencia interna
            client_data["rol"] = "client"
            print(f"Usuario encontrado en 'cliente': {client_data}")
            return client_data

        print(f"No se encontró usuario con RUT {rut}")
        return None

    except Exception as e:
        print(f"Error al buscar usuario: {e}")
        return None



def authenticate_user(rut, password):
    try:
        db = init_firebase()
        if db is None:
            print("No hay conexión con Firebase.")
            return None

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Primero intentamos en usuarios
        users_ref = db.collection("usuarios").where("rut", "==", rut)
        docs = users_ref.get()
        for doc in docs:
            user_data = doc.to_dict()
            if user_data.get("password") == password_hash:
                user_data["doc_id"] = doc.id
                return user_data

        # Si no se encuentra en usuarios, intentamos en cliente
        clients_ref = db.collection("cliente").where("rut", "==", rut)
        docs = clients_ref.get()
        for doc in docs:
            client_data = doc.to_dict()
            if client_data.get("password") == password_hash:
                client_data["doc_id"] = doc.id
                client_data["rol"] = "client"  # rol interno simulado
                return client_data

        print("Credenciales incorrectas.")
        return None

    except Exception as e:
        print(f"Error al validar credenciales: {e}")
        return None

    

def create_user(user_data: dict):
    """
    Crea un usuario en la colección 'usuarios'.
    user_data: dict con los campos necesarios según tipo de usuario.
    """
    db = init_firebase()
    if db is None:
        print("No hay conexión con Firebase.")
        return False

    try:
        db.collection("usuarios").add(user_data)
        print(f"Usuario agregado correctamente: {user_data.get('rut')}")
        return True
    except Exception as e:
        print(f"Error al agregar usuario: {e}")
        return False


def create_client(data):
    """Crea un cliente en la colección 'cliente'."""
    try:
        db = init_firebase()
        if db is None:
            print("No hay conexión con Firebase.")
            return False

        db.collection("cliente").add(data)
        print(f"Cliente agregado correctamente: {data}")
        return True
    except Exception as e:
        print(f"Error al agregar cliente: {e}")
        return False

#init_firebase()
#authenticate_user("12345678-9","12345")


#a= "12345"
#passw = hashlib.sha256(a.encode()).hexdigest()
#print(passw)