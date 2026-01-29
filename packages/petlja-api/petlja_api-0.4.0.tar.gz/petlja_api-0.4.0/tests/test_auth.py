import pytest

import petlja_api as petlja


def test_login_success(sess):
    assert sess is not None


def test_login_failed():
    with pytest.raises(PermissionError):
        petlja.login("wrongusername", "wrongpass")
