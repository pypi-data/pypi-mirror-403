import pytest
from dotenv import load_dotenv
from tortoise.backends.asyncpg import AsyncpgDBClient
from x_model import init_db
# from xync_schema.models import User

from xync_schema import TORM

load_dotenv()


@pytest.fixture
async def _dbc() -> AsyncpgDBClient:
    cn: AsyncpgDBClient = await init_db(TORM, True)
    yield cn
    await cn.close()


async def test_init_db(_dbc):
    assert isinstance(_dbc, AsyncpgDBClient), "DB corrupt"


# async def test_user_keys(_dbc):
#     for user in await User.filter(prv__isnull=True, pub__isnull=True).all():
#         user.keygen()
#         await user.save()
#     assert 1, "DB corrupt"


# async def test_models(_dbc):
#     c = await Ex.first()
#     assert isinstance(c, Ex), "No exs"
