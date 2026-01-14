from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from auth.models.command import Command

class CommandCruds:
    async def get_all_commands(self, db: AsyncSession):
        result = await db.execute(select(Command))
        return result.scalars().all()

command_service = CommandCruds()