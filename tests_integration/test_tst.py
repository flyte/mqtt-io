import mock
import pytest

@pytest.fixture(scope="module", autouse=True)
def fix_module():
    print("setup module")
    yield fix_module  # provide the fixture value
    print("teardown module")

@pytest.fixture(autouse=True)
def fix_fkt():
    print("setup fkt")
    yield fix_module  # provide the fixture value
    print("teardown fkt")

def test_1():
    print("test 1")

def test_2():
    print("test 2")

def test_3():
    print("test 3")
