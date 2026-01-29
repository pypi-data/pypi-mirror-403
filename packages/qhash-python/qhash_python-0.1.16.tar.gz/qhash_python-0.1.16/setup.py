from setuptools import setup

setup(
    name="qhash-python",
    package_data={"qhash": ["py.typed"], "qhash.clients.protos": ["*.py"]},
)
