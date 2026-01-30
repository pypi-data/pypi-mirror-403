from setuptools import setup

setup(
    name="sawyer_cz",
    version="0.1.0",
    py_modules=["sawyer_cz"],
    license="MIT",
    long_description="My customizations to the commitizen conventional commits",
    install_requires=["commitizen"],
    entry_points={"commitizen.plugin": ["sawyer_cz = sawyer_cz:SawyerCZ"]},
)
