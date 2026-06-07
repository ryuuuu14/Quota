import py_compile
import glob
import os

def test_syntax():
    for f in glob.glob("src/**/*.py", recursive=True):
        print(f"Checking {f}")
        py_compile.compile(f, doraise=True)
    assert True
