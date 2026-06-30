from typing import Generic, TypeVar, Any, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Abstract Generic Repository pattern implementation wrapping async CRUD database commands.
    """
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: Any) -> ModelType | None:
        """
        Retrieve a single model record by primary key ID.
        """
        return await self.session.get(self.model, id)

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """
        List all records with pagination filters.
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all(self) -> Sequence[ModelType]:
        """
        Retrieve all records without pagination.
        """
        query = select(self.model)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: dict[str, Any] | ModelType) -> ModelType:
        """
        Create and persist a new model entity.
        """
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = obj_in
        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict[str, Any] | ModelType) -> ModelType:
        """
        Update an existing model entity.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = {
                c.name: getattr(obj_in, c.name)
                for c in db_obj.__table__.columns
                if getattr(obj_in, c.name) is not None
            }

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def delete(self, id: Any) -> ModelType | None:
        """
        Delete a model record by ID.
        """
        db_obj = await self.get_by_id(id)
        if db_obj:
            await self.session.delete(db_obj)
            await self.session.flush()
        return db_obj
