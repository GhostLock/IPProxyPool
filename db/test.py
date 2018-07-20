import asyncio
import datetime
from aiomysql.sa import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Numeric, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DB_CONFIG, DEFAULT_SCORE
from db.ISqlHelper import ISqlHelper


# engine = create_engine("mysql+aiomysql://root:123456@localhost/test",echo=False)
"""
放弃采用异步数据库引擎，对原代码改动太多，不支持ORM。
采用多线程进行数据库操作。
"""

async def go():
    engine = await create_engine(
        user=DB_CONFIG["user"],
        db=DB_CONFIG["db"],
        host=DB_CONFIG["host"],
        password=DB_CONFIG["password"],
    )
    print(engine)


BaseModel = declarative_base()


class Proxy(BaseModel):
    __tablename__ = 'proxys'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(VARCHAR(16), nullable=False)
    port = Column(Integer, nullable=False)
    types = Column(Integer, nullable=False)
    protocol = Column(Integer, nullable=False, default=0)
    country = Column(VARCHAR(100), nullable=False)
    area = Column(VARCHAR(100), nullable=False)
    updatetime = Column(DateTime(), default=datetime.datetime.utcnow)
    speed = Column(Numeric(5, 2), nullable=False)
    score = Column(Integer, nullable=False, default=DEFAULT_SCORE)


async def create_sqlhelper(*args, **kwargs):
    helper = SqlHelper()
    await helper._init()
    return helper


class SqlHelper(ISqlHelper):
    params = {'ip': Proxy.ip, 'port': Proxy.port, 'types': Proxy.types, 'protocol': Proxy.protocol,
              'country': Proxy.country, 'area': Proxy.area, 'score': Proxy.score}

    async def _init(self):
        self.engine = await create_engine(
            user=DB_CONFIG["user"],
            db=DB_CONFIG["db"],
            host=DB_CONFIG["host"],
            password=DB_CONFIG["password"],
        )
        DB_Session = sessionmaker(bind=self.engine)
        self.session = DB_Session()

    def init_db(self):
        BaseModel.metadata.create_all(self.engine)


async def main():
    helper = await create_sqlhelper()
    print(helper.engine,helper.session)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
