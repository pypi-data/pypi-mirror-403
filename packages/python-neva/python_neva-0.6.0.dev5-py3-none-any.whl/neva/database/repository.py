"""Repository module."""

from pydantic import BaseModel
from tortoise import Model
from tortoise.queryset import QuerySet, QuerySetSingle


class BaseRepository[T: Model, CreateSchema: BaseModel, UpdateSchema: BaseModel]:
    """Base repository class."""

    def __init__(self, model: type[T]) -> None:
        """Initialize the repository."""
        self.model = model

    def all(self) -> QuerySet[T]:
        """Returns all objects."""
        return self.model.all()

    def get(self, obj_id: int) -> QuerySetSingle[T | None]:
        """Returns an object by ID."""
        return self.model.filter(id=obj_id).first()

    async def create(self, data: CreateSchema) -> T:
        """Create a new object.

        Returns:
            The created object.
        """
        return await self.model.create(**data.model_dump())

    async def update(self, obj_id: int, data: UpdateSchema) -> None:
        """Update an object by ID."""
        obj = await self.get(obj_id)
        if obj is not None:
            for key, value in data.model_dump(exclude_unset=True):
                setattr(obj, key, value)
            await obj.save()

    async def delete(self, obj_id: int) -> bool:
        """Delete an object by ID.

        Returns:
            True if the object was deleted, False otherwise.
        """
        obj = await self.get(obj_id)
        if obj is not None:
            await obj.delete()
            return True
        return False
