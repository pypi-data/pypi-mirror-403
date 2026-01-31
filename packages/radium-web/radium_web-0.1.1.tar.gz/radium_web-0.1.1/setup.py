from setuptools import setup, find_packages

setup(
    name="radium-web",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "radium=Radium.cli:main"
        ]
    },
)
