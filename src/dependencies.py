from punq import Container
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import DBConfig, GigachatConfig
from repositories import DBRepository, GigachatClient
from usecases import (
    DishRecognitionUseCase,
    RecommendationUseCase,
    StatisticsUseCase,
    UsersUseCase,
)
from usecases.interfaces import AIClientInterface, DBRepositoryInterface

container = Container()
db_config = DBConfig()
gigachat_config = GigachatConfig()


engine = create_async_engine(
    db_config.db_url,
    echo=False,
    pool_size=7,
    max_overflow=20,
    pool_pre_ping=True,
)

session_factory = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

container.register(AIClientInterface, factory=GigachatClient, config=gigachat_config)
container.register(DBRepositoryInterface, factory=DBRepository, session_factory=session_factory)
container.register(DBRepository, factory=DBRepository, session_factory=session_factory)
container.register(UsersUseCase, factory=UsersUseCase)
container.register(DishRecognitionUseCase, factory=DishRecognitionUseCase)
container.register(StatisticsUseCase, factory=StatisticsUseCase)
container.register(RecommendationUseCase, factory=RecommendationUseCase)
