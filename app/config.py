"""
Configuración de la aplicación.
Maneja diferentes entornos: desarrollo, pruebas y producción.
"""

from typing import List, Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración de la aplicación usando Pydantic Settings.
    Lee las variables de entorno desde el archivo .env
    """
    
    # Configuración básica de la aplicación
    app_name: str = "API de Películas"
    app_version: str = "1.0.0"
    
    # Configuración del entorno
    environment: Literal["development", "testing", "production"] = "development"
      
    # Configuración de la base de datos
    # Para SQLite: sqlite:///./peliculas.db
    # Para PostgreSQL: postgresql://user:password@localhost/dbname
    database_url: str = "sqlite:///./peliculas.db"
    
    # Configuración del servidor
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Configuración de CORS
    # En desarrollo puedes usar ["*"], en producción especifica los orígenes permitidos
    cors_origins: List[str] = ["*"]
    
    # Configuración de seguridad (para futuras mejoras)
    secret_key: str = "your-secret-key-here"  # Cambiar en producción
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Configuración de logging
    log_level: str = "INFO"
    
    # Configuración moderna en Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # class Config:
    #     """
    #     Configuración de Pydantic Settings.
    #     """
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"
    #     case_sensitive = False
        
        # Opcional - Agregar validación personalizada
    @field_validator("database_url")
    @classmethod 
    def validate_database_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("DATABASE_URL no puede estar vacío")
        return v


# Crear una instancia global de Settings
# settings = Settings()


# Opcional - Crear diferentes configuraciones para cada entorno
class DevelopmentSettings(Settings):
    """Configuración para el entorno de desarrollo."""
    debug: bool = True
    # Agregar configuraciones específicas de desarrollo
    log_level: str = "DEBUG"


class TestingSettings(Settings):
    """Configuración para el entorno de pruebas."""
    # Usar una base de datos diferente para pruebas
    debug: bool = True
    database_url: str = "sqlite:///./test_peliculas.db"
    # Agregar configuraciones específicas de pruebas
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Configuración para el entorno de producción."""
    debug: bool = False
    # Agregar configuraciones específicas de producción
    log_level: str = "INFO"
    # Cambiar a una base de datos más robusta (PostgreSQL, MySQL)
    cors_origins: List[str] = ["https://tu-dominio.com"]
    database_url: str = "postgresql://user:password@localhost/peliculas_prod"


# Función para obtener la configuración según el entorno

def get_settings() -> Settings:
    """
    Retorna la configuración apropiada según el entorno.
    """
    temp_settings = Settings()
    env = temp_settings.environment.lower()
    
    if env == "testing":
        return TestingSettings()
    elif env == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings()

settings = get_settings()

# Opcional - Agregar validación de configuración al inicio
def validate_settings():
    """Valida que todas las configuraciones necesarias estén presentes."""
    required_settings = ["database_url", "app_name"]
    for setting in required_settings:
        if not getattr(settings, setting, None):
            raise ValueError(f"Configuración requerida no encontrada: {setting}")

