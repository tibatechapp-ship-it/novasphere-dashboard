import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + __import__("os").path.join(__import__("tempfile").gettempdir(),"novasphere_test.db")
os.environ["SECRET_KEY"] = "test-secret"

import auth
import models  # noqa: F401


def test_create_and_authenticate():
    ok, tok = auth.create_user("alice", "secret123")
    assert ok
    assert auth.verify_token(tok) == "alice"
    t2 = auth.authenticate("alice", "secret123")
    assert t2 is not None
    assert auth.authenticate("alice", "wrong") is None


def test_duplicate_user():
    auth.create_user("bob", "pass1234")
    ok, msg = auth.create_user("bob", "pass1234")
    assert not ok
