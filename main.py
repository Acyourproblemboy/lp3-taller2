import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.config import settings
from app.database import create_db_and_tables, check_database_connection
from app.routers import usuarios, peliculas, favoritos
# Importar la configuración desde app.config

# Configuración del registrador de logs (Logger)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s"
)
logger = logging.getLogger("api_peliculas")
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación.
    Se ejecuta al iniciar y al cerrar la aplicación.
    """
    # Startup: Crear tablas en la base de datos
    create_db_and_tables()
    # Verificar conexión a la base de datos
    check_database_connection()
    yield
    
    # Shutdown: Limpiar recursos si es necesario
    print("cerrando aplicación...")


# Crear la instancia de FastAPI con metadatos apropiados
# Incluir: title, description, version, contact, license_info
app = FastAPI(
    title="API de Películas",
    description="API RESTful para gestionar usuarios, películas y favoritos",
    version="1.0.0",
    lifespan=lifespan,
    # Agregar información de contacto y licencia
    contact={
        "name": "Tu Nombre",
        "email": "tu.email@example.com",
    },
    license_info={
        "name": "MIT",
    },
)


# Configurar CORS para permitir solicitudes desde diferentes orígenes
# Esto es importante para desarrollo con frontend separado
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir los routers de usuarios, peliculas y favoritos
# Ejemplo:
app.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(peliculas.router, prefix="/api/peliculas", tags=["Películas"])
app.include_router(favoritos.router, prefix="/api/favoritos", tags=["Favoritos"])


# Crear un endpoint raíz que retorne información básica de la API
@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz de la API.
    Retorna información básica y enlaces a la documentación.
    """
    return {
        #  Agregar información
        "message": f"Bienvenido a la {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


# Crear un endpoint de health check para monitoreo
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint para verificar el estado de la API.
    Útil para sistemas de monitoreo y orquestación.
    """
    db_ok = check_database_connection()
    return {
       
        # Agregar verificación de conexión a base de datos
        
        # Agregar información sobre el sistema (uptime, memoria, etc.)
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "environment": settings.environment,
        "version": settings.app_version
    }


# Opcional - Agregar middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para medir tiempo de respuesta y registrar peticiones HTTP.
    """
    start_time = time.time()
    
    # Procesar la petición
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = f"{process_time:.2f}ms"
    
    logger.info(
        f"Path: {request.url.path} | Method: {request.method} | "
        f"Status: {response.status_code} | Duration: {formatted_process_time}"
    )
    
    response.headers["X-Process-Time"] = formatted_process_time
    return response

# Opcional - Agregar manejadores de errores personalizados
@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    """
    Captura errores de restricción SQL (por ejemplo, duplicados en unique constraints).
    """
    logger.error(f"Error de integridad en BD: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Conflicto en la base de datos: el registro o relación ya existe.",
            "path": request.url.path
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Captura errores generales del motor ORM/SQLAlchemy.
    """
    logger.error(f"Error de base de datos: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Ocurrió un error interno al procesar la transacción en la base de datos.",
            "path": request.url.path
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador global para excepciones no controladas.
    """
    logger.critical(f"Excepción no controlada: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor no controlado.",
            "path": request.url.path
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        # Configurar el servidor uvicorn con los parámetros apropiados
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

