"""
Tests para la API de Películas.
Pruebas unitarias y de integración usando pytest.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from app.database import get_session
from app.models import Usuario, Pelicula, Favorito


# =============================================================================
# CONFIGURACIÓN DE FIXTURES
# =============================================================================

# Fixture para crear una base de datos en memoria para testing
@pytest.fixture(name="session")
def session_fixture():
    """
    Crea una sesión de base de datos en memoria para cada test.
    Se limpia automáticamente después de cada test.
    """
    # Crear engine en memoria (SQLite)
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Crear todas las tablas
    SQLModel.metadata.create_all(engine)
    
    # Crear sesión
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)  # Limpiar tablas después de cada test


# Fixture para cliente de pruebas
@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Crea un cliente de pruebas de FastAPI con la sesión de test.
    """
    # Override de la dependencia get_session
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
    


# Fixture para crear usuarios de prueba
@pytest.fixture(name="usuario_test")
def usuario_test_fixture(session: Session):
    """
    Crea un usuario de prueba en la base de datos.
    """
    usuario = Usuario(
        nombre="Usuario Test",
        correo="test@example.com"
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario
    


# Fixture para crear películas de prueba
@pytest.fixture(name="pelicula_test")
def pelicula_test_fixture(session: Session):
    """
    Crea una película de prueba en la base de datos.
    """
    pelicula = Pelicula(
        titulo="Película Test",
        director="Director Test",
        genero="Drama",
        duracion=120,
        año=2020,
        clasificacion="PG-13",
        sinopsis="Una película de prueba"
    )
    session.add(pelicula)
    session.commit()
    session.refresh(pelicula)
    return pelicula
    


# =============================================================================
# TESTS DE USUARIOS
# =============================================================================

class TestUsuarios:
    """Tests para los endpoints de usuarios."""
    
    # Test para listar usuarios
    def test_listar_usuarios(self, client: TestClient):
        """Test para GET /api/usuarios"""
        response = client.get("/api/usuarios/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
    
    # Test para crear usuario
    def test_crear_usuario(self, client: TestClient):
        """Test para POST /api/usuarios"""
        usuario_data = {
            "nombre": "Nuevo Usuario",
            "correo": "nuevo@example.com"
        }
        response = client.post("/api/usuarios/", json=usuario_data)
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == usuario_data["nombre"]
        assert data["correo"] == usuario_data["correo"]
        assert "id" in data
        
    
    # Test para crear usuario con correo duplicado
    def test_crear_usuario_correo_duplicado(self, client: TestClient, usuario_test: Usuario):
        """Test para verificar que no se permiten correos duplicados"""
        usuario_data = {
            "nombre": "Otro Usuario",
            "correo": usuario_test.correo
        }
        response = client.post("/api/usuarios/", json=usuario_data)
        assert response.status_code == 400
        assert "correo" in response.json()["detail"].lower()
        
    
    # Test para obtener usuario por ID
    def test_obtener_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para GET /api/usuarios/{id}"""
        response = client.get(f"/api/usuarios/{usuario_test.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == usuario_test.id
        assert data["nombre"] == usuario_test.nombre
        
    
    # Test para obtener usuario inexistente
    def test_obtener_usuario_no_existe(self, client: TestClient):
        """Test para verificar error 404 con usuario inexistente"""
        response = client.get("/api/usuarios/9999")
        assert response.status_code == 404
        
    
    # Test para actualizar usuario
    def test_actualizar_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para PUT /api/usuarios/{id}"""
        update_data = {"nombre": "Nombre Actualizado"}
        response = client.put(f"/api/usuarios/{usuario_test.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == update_data["nombre"]
        
    
    # Test para eliminar usuario
    def test_eliminar_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para DELETE /api/usuarios/{id}"""
        response = client.delete(f"/api/usuarios/{usuario_test.id}")
        assert response.status_code == 204
        
        # Verificar que el usuario ya no existe
        response = client.get(f"/api/usuarios/{usuario_test.id}")
        assert response.status_code == 404
        


# =============================================================================
# TESTS DE PELÍCULAS
# =============================================================================

class TestPeliculas:
    """Tests para los endpoints de películas."""
    
    # Test para listar películas
    def test_listar_peliculas(self, client: TestClient):
        """Test para GET /api/peliculas"""
        response = client.get("/api/peliculas/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
    
    #  Test para crear película
    def test_crear_pelicula(self, client: TestClient):
        """Test para POST /api/peliculas"""
        pelicula_data = {
            "titulo": "Nueva Película",
            "director": "Director Nuevo",
            "genero": "Acción",
            "duracion": 150,
            "año": 2023,
            "clasificacion": "PG-13",
            "sinopsis": "Una nueva película de prueba"
        }
        response = client.post("/api/peliculas/", json=pelicula_data)
        assert response.status_code == 201
        data = response.json()
        assert data["titulo"] == pelicula_data["titulo"]
        assert "id" in data
            
    #  Test para obtener película por ID
    def test_obtener_pelicula(self, client: TestClient, pelicula_test: Pelicula):
        """Test para GET /api/peliculas/{id}"""
        response = client.get(f"/api/peliculas/{pelicula_test.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pelicula_test.id
        assert data["titulo"] == pelicula_test.titulo
        
    
    # Test para actualizar película
    def test_actualizar_pelicula(self, client: TestClient, pelicula_test: Pelicula):
        """Test para PUT /api/peliculas/{id}"""
        update_data = {"titulo": "Título Actualizado"}
        response = client.put(f"/api/peliculas/{pelicula_test.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["titulo"] == update_data["titulo"]
        
    
    #  Test para eliminar película
    def test_eliminar_pelicula(self, client: TestClient, pelicula_test: Pelicula):
        """Test para DELETE /api/peliculas/{id}"""
        response = client.delete(f"/api/peliculas/{pelicula_test.id}")
        assert response.status_code == 204
        
    
    #  Test para buscar películas
    def test_buscar_peliculas(self, client: TestClient, pelicula_test: Pelicula):
        """Test para GET /api/peliculas/buscar"""
        response = client.get(f"/api/peliculas/buscar/?titulo={pelicula_test.titulo}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["titulo"] == pelicula_test.titulo
        
    
    #  Test para buscar películas con múltiples filtros
    def test_buscar_peliculas_multiples_filtros(self, client: TestClient):
        """Test para búsqueda con múltiples parámetros"""
        response = client.get("/api/peliculas/buscar/?genero=Drama&año_min=2020")
        assert response.status_code == 200
        


# =============================================================================
# TESTS DE FAVORITOS
# =============================================================================

class TestFavoritos:
    """Tests para los endpoints de favoritos."""
    
    #  Test para listar favoritos
    def test_listar_favoritos(self, client: TestClient):
        """Test para GET /api/favoritos"""
        response = client.get("/api/favoritos/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
    
    #  Test para crear favorito
    def test_crear_favorito(
        self, 
        client: TestClient, 
        usuario_test: Usuario, 
        pelicula_test: Pelicula
    ):
        """Test para POST /api/favoritos"""
        favorito_data = {
            "id_usuario": usuario_test.id,
            "id_pelicula": pelicula_test.id
        }
        response = client.post("/api/favoritos/", json=favorito_data)
        assert response.status_code == 201
        data = response.json()
        assert data["id_usuario"] == usuario_test.id
        assert data["id_pelicula"] == pelicula_test.id
        
    
    #  Test para crear favorito duplicado
    def test_crear_favorito_duplicado(
        self, 
        client: TestClient, 
        usuario_test: Usuario, 
        pelicula_test: Pelicula
    ):
        """Test para verificar que no se permiten favoritos duplicados"""
        favorito_data = {
            "id_usuario": usuario_test.id,
            "id_pelicula": pelicula_test.id
        }
        # Crear el primer favorito
        client.post("/api/favoritos/", json=favorito_data)
        
        # Intentar crear el mismo favorito nuevamente
        response = client.post("/api/favoritos/", json=favorito_data)
        assert response.status_code == 400
        
    
    #  Test para eliminar favorito
    def test_eliminar_favorito(
        self, 
        client: TestClient, 
        session: Session,
        usuario_test: Usuario, 
        pelicula_test: Pelicula
    ):
        """Test para DELETE /api/favoritos/{id}"""
        # # Crear favorito
        favorito = Favorito(id_usuario=usuario_test.id, id_pelicula=pelicula_test.id)
        session.add(favorito)
        session.commit()
        session.refresh(favorito)
        
        # Eliminar favorito
        response = client.delete(f"/api/favoritos/{favorito.id}")
        assert response.status_code == 204
        
    
    # Test para marcar favorito desde usuario
    def test_marcar_favorito_usuario(
        self, 
        client: TestClient, 
        usuario_test: Usuario, 
        pelicula_test: Pelicula
    ):
        """Test para POST /api/usuarios/{id}/favoritos/{id_pelicula}"""
        response = client.post(
            f"/api/usuarios/{usuario_test.id}/favoritos/{pelicula_test.id}"
        )
        assert response.status_code == 201
        
    
    #  Test para listar favoritos de usuario
    def test_listar_favoritos_usuario(
        self, 
        client: TestClient, 
        session: Session,
        usuario_test: Usuario, 
        pelicula_test: Pelicula
    ):
        """Test para GET /api/usuarios/{id}/favoritos"""
        # # Crear favorito
        favorito = Favorito(id_usuario=usuario_test.id, id_pelicula=pelicula_test.id)
        session.add(favorito)
        session.commit()
        
        # Listar favoritos del usuario
        response = client.get(f"/api/usuarios/{usuario_test.id}/favoritos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        


# =============================================================================
# TESTS DE INTEGRACIÓN
# =============================================================================

class TestIntegracion:
    """Tests de integración que prueban flujos completos."""
    
    # Test de flujo completo: crear usuario, película y marcar favorito
    def test_flujo_completo(self, client: TestClient):
        """Test que verifica el flujo completo de la aplicación"""
        # # 1. Crear usuario
        usuario_data = {
            "nombre": "Usuario Integración",
            "correo": "integracion@example.com"
        }
        response_usuario = client.post("/api/usuarios/", json=usuario_data)
        assert response_usuario.status_code == 201
        usuario_id = response_usuario.json()["id"]
        
        # # 2. Crear película
        pelicula_data = {
            "titulo": "Película Integración",
            "director": "Director Test",
            "genero": "Drama",
            "duracion": 120,
            "año": 2023,
            "clasificacion": "PG-13"
        }
        response_pelicula = client.post("/api/peliculas/", json=pelicula_data)
        assert response_pelicula.status_code == 201
        pelicula_id = response_pelicula.json()["id"]
        
        # # 3. Marcar como favorito
        response_favorito = client.post(
            f"/api/usuarios/{usuario_id}/favoritos/{pelicula_id}"
        )
        assert response_favorito.status_code == 201
        
        # 4. Verificar que aparece en favoritos del usuario
        response_lista = client.get(f"/api/usuarios/{usuario_id}/favoritos")
        assert response_lista.status_code == 200
        favoritos = response_lista.json()
        assert len(favoritos) == 1
        assert favoritos[0]["id"] == pelicula_id
        pass


# =============================================================================
# TESTS DE VALIDACIÓN
# =============================================================================

class TestValidacion:
    """Tests para validaciones de datos."""
    
    # Test para validar email inválido
    def test_email_invalido(self, client: TestClient):
        """Test para verificar validación de email"""
        usuario_data = {
            "nombre": "Usuario Test",
            "correo": "email-invalido"
        }
        response = client.post("/api/usuarios/", json=usuario_data)
        assert response.status_code == 422  # Unprocessable Entity
        
    
    # Test para validar año de película
    def test_año_pelicula_invalido(self, client: TestClient):
        """Test para verificar validación de año"""
        pelicula_data = {
            "titulo": "Película Test",
            "director": "Director Test",
            "genero": "Drama",
            "duracion": 120,
            "año": 1800,  # Año inválido (cine comenzó en 1888)
            "clasificacion": "PG-13"
        }
        response = client.post("/api/peliculas/", json=pelicula_data)
        assert response.status_code == 422
        
    
    #  Test para validar campos requeridos
    def test_campos_requeridos(self, client: TestClient):
        """Test para verificar que los campos requeridos son obligatorios"""
        usuario_data = {"nombre": "Usuario Sin Email"}
        response = client.post("/api/usuarios/", json=usuario_data)
        assert response.status_code == 422
        


