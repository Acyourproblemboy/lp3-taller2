"""
Router de Favoritos.
Endpoints para gestionar las relaciones de favoritos entre usuarios y películas.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, col, or_
from sqlalchemy import func
from typing import List

from app.database import get_session
from app.models import Favorito, Usuario, Pelicula
from app.schemas import (
    FavoritoCreate,
    FavoritoRead,
    FavoritoWithDetails
)

# Crear el router con prefijo y tags
router = APIRouter(
    prefix="/api/favoritos",
    tags=["Favoritos"]
)


# Endpoint para listar todos los favoritos
@router.get("/", response_model=List[FavoritoRead])
def listar_favoritos(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    """
    Lista todos los favoritos registrados en la plataforma.
    
    - **skip**: Número de registros a omitir (para paginación)
    - **limit**: Número máximo de registros a retornar
    """
    # Consultar todos los favoritos con paginación
    statement = select(Favorito).offset(skip).limit(limit)
    favoritos = session.exec(statement).all()
    return favoritos


# Endpoint para crear un nuevo favorito
@router.post("/", response_model=FavoritoRead, status_code=status.HTTP_201_CREATED)
def crear_favorito(
    favorito: FavoritoCreate,
    session: Session = Depends(get_session)
):
    """
    Marca una película como favorita para un usuario.
    
    - **id_usuario**: ID del usuario
    - **id_pelicula**: ID de la película
    """
    # Verificar que el usuario existe
    usuario = session.get(Usuario, favorito.id_usuario)
    if not usuario:
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con id {favorito.id_usuario} no encontrado"
        )
    
    # Verificar que la película existe
    pelicula = session.get(Pelicula, favorito.id_pelicula)
    if not pelicula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Película con id {favorito.id_pelicula} no encontrada"
        )
    
    # Verificar si ya existe el favorito
    statement = select(Favorito).where(
        Favorito.id_usuario == favorito.id_usuario,
        Favorito.id_pelicula == favorito.id_pelicula
    )
    existing_favorito = session.exec(statement).first()
    if existing_favorito:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este favorito ya existe"
        )

    # Crear el nuevo favorito
    db_favorito = Favorito.model_validate(favorito)
    session.add(db_favorito)
    session.commit()
    session.refresh(db_favorito)
    return db_favorito
    


# Endpoint para obtener un favorito por ID
@router.get("/{favorito_id}", response_model=FavoritoWithDetails)
def obtener_favorito(
    favorito_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtiene un favorito específico por su ID, incluyendo información del usuario y película.
    
    - **favorito_id**: ID del favorito
    """
    # Buscar el favorito por ID
    favorito = session.get(Favorito, favorito_id)
    if not favorito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Favorito con id {favorito_id} no encontrado"
        )

    # Cargar relaciones (usuario y película)
    # Esto depende de cómo hayas configurado las relaciones en los modelos
    return favorito
    


# Endpoint para eliminar un favorito
@router.delete("/{favorito_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_favorito(
    favorito_id: int,
    session: Session = Depends(get_session)
):
    """
    Elimina un favorito de la plataforma.
    
    - **favorito_id**: ID del favorito a eliminar
    """
    # Buscar el favorito
    favorito = session.get(Favorito, favorito_id)
    if not favorito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Favorito con id {favorito_id} no encontrado"
        )
    
    # Eliminar el favorito
    session.delete(favorito)
    session.commit()
    return None
    


#  Endpoint para obtener favoritos de un usuario específico
@router.get("/usuario/{usuario_id}", response_model=List[FavoritoWithDetails])
def favoritos_por_usuario(
    usuario_id: int,
    session: Session = Depends(get_session)
):
    """
    Lista todos los favoritos de un usuario específico.
    
    - **usuario_id**: ID del usuario
    """
    #  Verificar que el usuario existe
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con id {usuario_id} no encontrado"
        )
    
    #  Obtener todos los favoritos del usuario
    statement = select(Favorito).where(Favorito.id_usuario == usuario_id)
    favoritos = session.exec(statement).all()
    return favoritos
    


# Endpoint para obtener favoritos de una película específica
@router.get("/pelicula/{pelicula_id}", response_model=List[FavoritoWithDetails])
def favoritos_por_pelicula(
    pelicula_id: int,
    session: Session = Depends(get_session)
):
    """
    Lista todos los usuarios que marcaron una película como favorita.
    
    - **pelicula_id**: ID de la película
    """
    # Verificar que la película existe
    pelicula = session.get(Pelicula, pelicula_id)
    if not pelicula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Película con id {pelicula_id} no encontrada"
        )
    
    # Obtener todos los favoritos de la película
    statement = select(Favorito).where(Favorito.id_pelicula == pelicula_id)
    favoritos = session.exec(statement).all()
    return favoritos
    


# Opcional - Endpoint para verificar si una película es favorita de un usuario
@router.get("/verificar/{usuario_id}/{pelicula_id}")
def verificar_favorito(
    usuario_id: int,
    pelicula_id: int,
    session: Session = Depends(get_session)
):
    """
    Verifica si una película es favorita de un usuario.
    
    - **usuario_id**: ID del usuario
    - **pelicula_id**: ID de la película
    
    Retorna un objeto con el estado y el ID del favorito si existe.
    """
    #  Buscar el favorito
    statement = select(Favorito).where(
        Favorito.id_usuario == usuario_id,
        Favorito.id_pelicula == pelicula_id
    )
    favorito = session.exec(statement).first()
    
    if favorito:
        return {
            "es_favorito": True,
            "favorito_id": favorito.id,
            "fecha_marcado": favorito.fecha_marcado
        }
    else:
        return {"es_favorito": False}
    


# Opcional - Endpoint para estadísticas de favoritos
@router.get("/estadisticas/generales")
def estadisticas_favoritos(
    session: Session = Depends(get_session)
):
    """
    Obtiene estadísticas generales sobre los favoritos en la plataforma.
    
    Retorna:
    - Total de favoritos
    - Usuario con más favoritos
    - Película más favorita
    - Género más popular en favoritos
    """
    # Calcular total de favoritos
    from sqlalchemy import func
    total_favoritos = session.exec(select(func.count(Favorito.id))).one()
    
    # Usuario con más favoritos
    statement_usuario = (
        select(Usuario, func.count(Favorito.id).label("count"))
        .join(Favorito)
        .group_by(Usuario.id)
        .order_by(func.count(Favorito.id).desc())
        .limit(1)
    )
    top_usuario = session.exec(statement_usuario).first()
    
    #  Película más favorita
    statement_pelicula = (
        select(Pelicula, func.count(Favorito.id).label("count"))
        .join(Favorito)
        .group_by(Pelicula.id)
        .order_by(func.count(Favorito.id).desc())
        .limit(1)
    )
    top_pelicula = session.exec(statement_pelicula).first()
    
    return {
        "total_favoritos": total_favoritos,
        "usuario_top": {
            "nombre": top_usuario[0].nombre if top_usuario else None,
            "cantidad_favoritos": top_usuario[1] if top_usuario else 0
        },
        "pelicula_top": {
            "titulo": top_pelicula[0].titulo if top_pelicula else None,
            "cantidad_favoritos": top_pelicula[1] if top_pelicula else 0
        }
    }
    


# Opcional - Endpoint para eliminar todos los favoritos de un usuario
@router.delete("/usuario/{usuario_id}/todos", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_todos_favoritos_usuario(
    usuario_id: int,
    session: Session = Depends(get_session)
):
    """
    Elimina TODOS los favoritos de un usuario.
    
    - **usuario_id**: ID del usuario
    
    ⚠️ Esta acción es irreversible.
    """
    # Verificar que el usuario existe
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con id {usuario_id} no encontrado"
        )
    
    # Eliminar todos los favoritos del usuario
    statement = select(Favorito).where(Favorito.id_usuario == usuario_id)
    favoritos = session.exec(statement).all()
    
    for favorito in favoritos:
        session.delete(favorito)
    
    session.commit()
    return None
    


# Opcional - Endpoint para obtener recomendaciones basadas en favoritos
@router.get("/recomendaciones/{usuario_id}", response_model=List)
def obtener_recomendaciones(
    usuario_id: int,
    limit: int = 5,
    session: Session = Depends(get_session)
):
    """
    Obtiene recomendaciones de películas para un usuario basadas en sus favoritos.
    
    La lógica básica busca películas del mismo género o director que las favoritas del usuario.
    
    - **usuario_id**: ID del usuario
    - **limit**: Número máximo de recomendaciones
    """
    # Verificar que el usuario existe
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con id {usuario_id} no encontrado"
        )
    
    #  Obtener géneros y directores de películas favoritas del usuario
    statement = (
        select(Pelicula.genero, Pelicula.director)
        .join(Favorito)
        .where(Favorito.id_usuario == usuario_id)
    )
    favoritos_info = session.exec(statement).all()
    
    if not favoritos_info:
        return []
    
    #  Buscar películas similares que el usuario NO haya marcado como favoritas
    generos = [info[0] for info in favoritos_info]
    directores = [info[1] for info in favoritos_info]
    
    # # Obtener IDs de películas ya favoritas
    statement_ids = select(Favorito.id_pelicula).where(Favorito.id_usuario == usuario_id)
    ids_favoritos = session.exec(statement_ids).all()
    
    # # Buscar películas recomendadas
    statement_recomendaciones = (
        select(Pelicula)
        .where(
            or_(
                col(Pelicula.genero).in_(generos),
                col(Pelicula.director).in_(directores)
            ),
            Pelicula.id.notin_(ids_favoritos)
        )
        .limit(limit)
    )
    recomendaciones = session.exec(statement_recomendaciones).all()
    return recomendaciones
    

