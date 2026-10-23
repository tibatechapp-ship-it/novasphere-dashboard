import os
import tempfile
db_path = os.path.join(tempfile.gettempdir(), "novasphere_test.db")
try:
    os.remove(db_path)
except FileNotFoundError:
    pass
os.environ["DATABASE_URL"] = "sqlite:///" + db_path
os.environ["SECRET_KEY"] = "test-secret"

import pytest
from database import Base, engine
import models  # noqa: F401
import models  # noqa: F401  register tables


@pytest.fixture(autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
