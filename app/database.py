"""
Configuración de la base de datos y gestión de sesiones.
Utiliza SQLModel para ORM y gestión de conexiones.
"""

from sqlmodel import SQLModel, create_engine, Session, text
from typing import Generator

from app.config import settings


# Crear el engine de la base de datos
is_sqlite = settings.database_url.startswith("sqlite")
# El engine es la conexión principal a la base de datos
# connect_args es específico para SQLite, remover para otras bases de datos
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Muestra las consultas SQL en consola si debug=True
    connect_args=connect_args  # Necesario para SQLite
)


# Función para crear todas las tablas
def create_db_and_tables():
    """
    Crea todas las tablas en la base de datos.
    Se llama al iniciar la aplicación.
    """
    # Importar todos los modelos antes de crear las tablas
    from app import models  # Asegurarse de que todos los modelos estén registrados
    
    SQLModel.metadata.create_all(engine)
    print("Tablas de la base de datos creadas correctamente")


# Función para eliminar todas las tablas (útil para testing)
def drop_db_and_tables():
    """
    Elimina todas las tablas de la base de datos.
    Usar con precaución - elimina todos los datos.
    """
    SQLModel.metadata.drop_all(engine)
    print("Tablas de la base de datos eliminadas")


# Obtener una sesión de base de datos
def get_session() -> Generator[Session, None, None]:
    """
    Generador de sesiones de base de datos.
    Se usa como dependencia en los endpoints de FastAPI.
    
    # Uso en endpoints:
    #     @app.get("/items")
    #     def read_items(session: Session = Depends(get_session)):
    #         items = session.exec(select(Item)).all()
    #         return items
    """
    with Session(engine) as session:
        yield session


# Opcional - Función para verificar la conexión a la base de datos
def check_database_connection() -> bool:
    """
    Verifica que la conexión a la base de datos funcione correctamente.
    Retorna True si la conexión es exitosa, False en caso contrario.
    """
    try:
        with Session(engine) as session:
            # Ejecutar una consulta simple para verificar la conexión
            session.exec(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return False


# Opcional - Context manager para transacciones
class DatabaseSession:
    """
    Context manager para manejar sesiones de base de datos.
    Útil para operaciones fuera de endpoints FastAPI.
    
    Uso:
        with DatabaseSession() as session:
            user = session.get(Usuario, user_id)
    """
    def __enter__(self) -> Session:
        self.session = Session(engine)
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        self.session.close()


#  Opcional - Función para inicializar datos de prueba
def init_sample_data():
    """
    Inicializa la base de datos con datos de prueba.
    Útil para desarrollo y testing.
    """
    # : Crear usuarios, películas y favoritos de ejemplo
    with Session(engine) as session:
        # Crear usuarios de ejemplo
        if not session.exec(select(Usuario)).first():
            usuarios = [...]
            for usuario in usuarios:
                session.add(usuario)
            session.commit()
    

