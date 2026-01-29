from pathlib import Path
from setuptools import setup, find_packages


def read_version() -> str:
    ns = {}
    with open("syncy/__init__.py", "r", encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns.get("__version__", "0.0.0")


setup(
    name="syncy",
    version=read_version(),
    description="Database migration validation tool (SQL Server ↔ PostgreSQL)",
    author="",
    packages=find_packages(exclude=("tests", "reports")),
    include_package_data=True,
    install_requires=[
        "click>=8.1.0",
        "pyodbc>=5.0.0",
        "psycopg2-binary>=2.9.9",
        "Jinja2>=3.1.2",
        "PyYAML>=6.0.1",
        "sqlparse>=0.4.4",
        "ttkbootstrap>=1.10.1",
    ],
    entry_points={
        "console_scripts": [
            "syncy=syncy.cli:cli",
        ]
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

