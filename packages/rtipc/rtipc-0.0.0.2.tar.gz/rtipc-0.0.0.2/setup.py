from setuptools import setup

versionContext = {}
with open('rtipc/version.py') as f:
    exec(f.read(), versionContext)

setup(
    version=versionContext['__version__'],
)
