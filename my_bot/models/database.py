import datetime
from typing import AsyncGenerator, Dict, List
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy import func
from sqlalchemy import select, insert, ForeignKey

from config_reader import settings
from utils.logger import get_logger

logger = get_logger("models.database")

engine = create_async_engine(settings.DB_URI, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    create_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())


class ChatCity(Base):
    """Не используется на данном этапе"""
    __tablename__ = 'chat_cities'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(nullable=False)
    city_id: Mapped[int] = mapped_column(ForeignKey('cities.id'))

    city = relationship("City")


async def init_db() -> None:
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        logger.info("База создана")

    await engine.dispose()


async def get_db() -> AsyncGenerator:
    """
    Генерирует сессию.

    :yield: AsyncGenerator
    """
    async with async_session() as session:
        logger.debug("ASYNC Pool: {pool}".format(pool=engine.pool.status()))
        yield session


class CRUDService:

    async def insert_db(self, name):
        stmt = (
            insert(City).
            values(name=name)
        )
        async with async_session.begin() as con:
            await con.execute(stmt)
            logger.info(f"Город {name} добавлен в базу.")

    async def select_object(self, name: str) -> City | None:
        stmt = select(City).where(City.name == name.capitalize())
        async with async_session() as con:
            result = await con.execute(stmt)
            city = result.fetchone()
            if city is not None:
                logger.info(f"Город {name} имеется в базе.")
                return city[0]
            else:
                logger.info(f"Город {name} отсутствует в базе.")
                raise None

    async def select_object_by_prefix(self, prefix: str) -> City | None:
        stmt = select(City).where(City.name.like(f"{prefix.capitalize()}%"))
        async with async_session() as con:
            result = await con.execute(stmt)
            city = result.first()[0]
            print(777, city)
            if city:
                logger.info(f"Найден город, начинающийся с '{prefix}': {city.name}")
                return city
            else:
                logger.info(f"Город, начинающийся с '{prefix}', не найден.")
                return None

    async def get_cities(self) -> Dict[str, List[str]]:
        """
        Асинхронная функция для извлечения всех городов из базы данных.
        """
        cities_by_first_letter: Dict[str, List[str]] = {}

        async with async_session.begin() as con:
            cities = (await con.execute(select(City))).all()
            for city in cities:
                first_letter = city[0].name[0].lower()
                cities_by_first_letter.setdefault(first_letter, []).append(city[0].name)

        return cities_by_first_letter

    async def add_city_to_chat(self, chat_id, city_name) -> bool:
        """
        Добавляем города для чата
        """
        async with async_session.begin() as con:
            city = (await con.execute(select(City).filter(City.name == city_name))).first()[0]
            chat_city = (await con.execute(select(ChatCity).filter(
                ChatCity.city_id == city.id, ChatCity.chat_id == chat_id))).first()[0]
            if city and not chat_city:
                new_chat_city = ChatCity(chat_id=chat_id, city_id=city.id)
                con.add(new_chat_city)
                await con.commit()
                return True
            else:
                return False



    async def remove_cities_from_chat(self, chat_id):
        """
        Удаляет все записи чата.
        """
        async with async_session.begin() as con:
            # Находим все записи для данного чата
            chat_cities = await con.execute(select(ChatCity).filter(ChatCity.chat_id == chat_id))

            # Удаляем все найденные записи
            for chat_city in chat_cities:
                await con.delete(chat_city)

            # Коммитим изменения
            await con.commit()

    async def create_cities_dict(self):

        cities_dict = {}
        for city in cities:
            last_letter = city[-1].lower()
            if last_letter not in cities_dict:
                cities_dict[last_letter] = []
            cities_dict[last_letter].append(city)


service = CRUDService()
