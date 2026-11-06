"""
Router de Películas.
Endpoints para gestionar películas en la plataforma.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, or_, col
from sqlalchemy import func
from typing import List, Optional

from app.database import get_session
from app.models import Pelicula, Favorito
from app.schemas import PeliculaCreate, PeliculaRead, PeliculaUpdate

# Crear el router con prefijo y tags
router = APIRouter(
    prefix="/api/peliculas",
    tags=["Películas"]
)


# Endpoint para listar todas las películas
@router.get("/", response_model=List[PeliculaRead])
def listar_peliculas(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    """
    Lista todas las películas disponibles.
    
    - **skip**: Número de registros a omitir (para paginación)
    - **limit**: Número máximo de registros a retornar
    """
    # Consultar todas las películas con paginación
    statement = select(Pelicula).offset(skip).limit(limit)
    peliculas = session.exec(statement).all()
    return peliculas


# Endpoint para crear una nueva película
@router.post("/", response_model=PeliculaRead, status_code=status.HTTP_201_CREATED)
def crear_pelicula(
    pelicula: PeliculaCreate,
    session: Session = Depends(get_session)
):
    """
    Crea una nueva película en la plataforma.
    
    - **titulo**: Título de la película
    - **director**: Director de la película
    - **genero**: Género cinematográfico
    - **duracion**: Duración en minutos
    - **año**: Año de estreno
    - **clasificacion**: Clasificación por edad (G, PG, PG-13, R, etc.)
    - **sinopsis**: Breve descripción de la trama
    """
    # Verificar que no exista una película con el mismo título y año
    statement = select(Pelicula).where(
        (col(Pelicula.titulo) == pelicula.titulo) & (col(Pelicula.año) == pelicula.año)
    )
    
    existing_pelicula = session.exec(statement).first()
    if existing_pelicula:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una película con el título '{pelicula.titulo}' del año {pelicula.año}"
        )
    
    # Crear la nueva película
    db_pelicula = Pelicula.model_validate(pelicula)
    session.add(db_pelicula)
    session.commit()
    session.refresh(db_pelicula)
    return db_pelicula


# Endpoint para obtener una película por ID
@router.get("/{pelicula_id}", response_model=PeliculaRead)
def obtener_pelicula(
    pelicula_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtiene una película específica por su ID.
    
    - **pelicula_id**: ID de la película
    """
    # Buscar la película por ID
    pelicula = session.get(Pelicula, pelicula_id)
    if not pelicula:
        raise HTTPException(
            # Código y Detalle del Error
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Película con id {pelicula_id} no encontrada"
        )
    return pelicula


# Endpoint para actualizar una película
@router.put("/{pelicula_id}", response_model=PeliculaRead)
def actualizar_pelicula(
    pelicula_id: int,
    pelicula_update: PeliculaUpdate,
    session: Session = Depends(get_session)
):
    """
    Actualiza la información de una película existente.
    
    - **pelicula_id**: ID de la película a actualizar
    - Los campos son opcionales, solo se actualizan los proporcionados
    """
    #  Buscar la película
    db_pelicula = session.get(Pelicula, pelicula_id)
    if not db_pelicula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Película con id {pelicula_id} no encontrada"
        )

    #  Actualizar solo los campos proporcionados
    pelicula_data = pelicula_update.model_dump(exclude_unset=True)
    for key, value in pelicula_data.items():
        setattr(db_pelicula, key, value)
    session.commit()
    session.refresh(db_pelicula)
    return db_pelicula


# Endpoint para eliminar una película
@router.delete("/{pelicula_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pelicula(
    pelicula_id: int,
    session: Session = Depends(get_session)
):
    """
    Elimina una película de la plataforma.
    
    - **pelicula_id**: ID de la película a eliminar
    
    También se eliminarán todos los favoritos asociados a esta película.
    """
    # Buscar la película
    pelicula = session.get(Pelicula, pelicula_id)
    if not pelicula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Película con id {pelicula_id} no encontrada"
        )
    
    # Eliminar la película (los favoritos se eliminan por CASCADE)
    session.delete(pelicula)
    session.commit()
    return None


# Endpoint para buscar películas
@router.get("/buscar/", response_model=List[PeliculaRead])
def buscar_peliculas(
    titulo: Optional[str] = Query(None, description="Buscar por título"),
    director: Optional[str] = Query(None, description="Buscar por director"),
    genero: Optional[str] = Query(None, description="Buscar por género"),
    año: Optional[int] = Query(None, description="Buscar por año exacto"),
    año_min: Optional[int] = Query(None, description="Año mínimo"),
    año_max: Optional[int] = Query(None, description="Año máximo"),
    session: Session = Depends(get_session)
):
    """
    Busca películas según diferentes criterios.
    Todos los parámetros son opcionales y se pueden combinar.
    
    - **titulo**: Busca películas que contengan este texto en el título
    - **director**: Busca películas que contengan este texto en el director
    - **genero**: Busca películas que contengan este género
    - **año**: Busca películas de un año específico
    - **año_min**: Busca películas desde este año en adelante
    - **año_max**: Busca películas hasta este año
    """
    # Construir la consulta base
    statement = select(Pelicula)
    
    # Agregar filtros según los parámetros proporcionados
    if titulo:
        statement = statement.where(col(Pelicula.titulo).contains(titulo))
    
    if director:
        statement = statement.where(col(Pelicula.director).contains(director))
    
    if genero:
        statement = statement.where(col(Pelicula.genero).contains(genero))
    
    if año:
        statement = statement.where(Pelicula.año == año)
    
    if año_min:
        statement = statement.where(Pelicula.año >= año_min)
    
    if año_max:
        statement = statement.where(Pelicula.año <= año_max)
    
    # TODO: Ejecutar la consulta y retornar resultados
    # peliculas = session.exec(statement).all()
    # return peliculas
    pass


# Opcional - Endpoint para obtener películas más populares
@router.get("/populares/top", response_model=List[PeliculaRead])
def peliculas_populares(
    limit: int = Query(10, ge=1, le=50, description="Número de películas a retornar"),
    session: Session = Depends(get_session)
):
    """
    Obtiene las películas más populares basado en la cantidad de favoritos.
    
    - **limit**: Número de películas a retornar (máximo 50)
    """
    # Consultar películas ordenadas por número de favoritos
   
    statement = (select(Pelicula, func.count(Favorito.id).label("favoritos_count"))
                 .join(Favorito, Favorito.pelicula_id == Pelicula.id)
                 .group_by(Pelicula.id)
                 .order_by(func.count(Favorito.id).desc())
                 .limit(limit))

    results = session.exec(statement).all()
    peliculas = [ result[0] for result in results ]
    return peliculas


# Opcional - Endpoint para obtener películas por clasificación
@router.get("/clasificacion/{clasificacion}", response_model=List[PeliculaRead])
def peliculas_por_clasificacion(
    clasificacion: str,
    session: Session = Depends(get_session),
    limit: int = 100
):
    """
    Obtiene películas filtradas por clasificación de edad.
    
    - **clasificacion**: G, PG, PG-13, R, NC-17
    """
    # Validar clasificación
    clasificaciones_validas = ["G", "PG", "PG-13", "R", "NC-17"]
    if clasificacion.upper() not in clasificaciones_validas:
        raise HTTPException(
            status_code=400,
            detail="Clasificación de edad no válida"
        )
    
    #  Buscar películas por clasificación
    statement = select(Pelicula).where(
        Pelicula.clasificacion == clasificacion.upper()
    ).limit(limit)
    peliculas = session.exec(statement).all()
    return peliculas


# Opcional - Endpoint para obtener películas recientes
@router.get("/recientes/nuevas", response_model=List[PeliculaRead])
def peliculas_recientes(
    limit: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session)
):
    """
    Obtiene las películas más recientes basado en fecha de creación.
    
    - **limit**: Número de películas a retornar
    """
    # Consultar películas ordenadas por fecha de creación
    statement = select(Pelicula).order_by(Pelicula.fecha_creacion.desc()).limit(limit)
    peliculas = session.exec(statement).all()
    return peliculas
    

