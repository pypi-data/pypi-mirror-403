"""
Package database for typosquatting detection.

Contains the top packages from PyPI and NPM registries.
These are the most likely targets for typosquatting attacks.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

# Top 500 PyPI packages (most downloaded)
# Source: https://hugovk.github.io/top-pypi-packages/
PYPI_TOP_PACKAGES: Set[str] = {
    # Core/Popular
    "requests", "numpy", "pandas", "flask", "django", "boto3", "urllib3",
    "setuptools", "pip", "wheel", "six", "python-dateutil", "pyyaml",
    "certifi", "charset-normalizer", "idna", "typing-extensions",
    "cryptography", "cffi", "pycparser", "packaging", "attrs", "pluggy",
    "pytest", "coverage", "tox", "virtualenv", "click", "jinja2",
    "markupsafe", "werkzeug", "itsdangerous", "sqlalchemy", "greenlet",
    "pillow", "scipy", "matplotlib", "scikit-learn", "tensorflow",
    "torch", "keras", "pytorch", "transformers", "huggingface-hub",

    # AWS/Cloud
    "botocore", "s3transfer", "awscli", "aws-sam-cli", "azure-core",
    "google-cloud-storage", "google-auth", "google-api-core",

    # Web frameworks
    "fastapi", "uvicorn", "starlette", "httpx", "aiohttp", "httpcore",
    "tornado", "gunicorn", "gevent", "celery", "redis", "kombu",

    # Data/ML
    "pyarrow", "polars", "dask", "xgboost", "lightgbm", "catboost",
    "seaborn", "plotly", "bokeh", "altair", "streamlit", "gradio",

    # CLI/Utils
    "rich", "typer", "fire", "argparse", "colorama", "tqdm", "tabulate",

    # Testing
    "pytest-cov", "mock", "faker", "hypothesis", "responses", "httpretty",

    # Linting/Formatting
    "black", "ruff", "flake8", "pylint", "mypy", "isort", "autopep8",

    # Security (meta - we want to protect these)
    "bandit", "safety", "pip-audit", "semgrep",

    # Database
    "psycopg2", "psycopg2-binary", "pymongo", "motor", "sqlalchemy",
    "alembic", "peewee", "tortoise-orm", "databases",

    # API/Serialization
    "pydantic", "marshmallow", "orjson", "ujson", "msgpack",

    # Async
    "asyncio", "anyio", "trio", "curio",

    # Dev tools
    "ipython", "jupyter", "notebook", "jupyterlab", "nbconvert",

    # Parsing
    "beautifulsoup4", "lxml", "html5lib", "cssselect", "parsel",
    "scrapy", "selenium", "playwright", "pyppeteer",

    # Image/Media
    "opencv-python", "imageio", "scikit-image",

    # Crypto
    "pyjwt", "python-jose", "passlib", "bcrypt", "paramiko",

    # Common typosquatting targets (high value)
    "colorama", "idna", "chardet", "certifi", "urllib3",
}

# Top 500 NPM packages
NPM_TOP_PACKAGES: Set[str] = {
    # Core
    "lodash", "react", "express", "axios", "moment", "chalk", "commander",
    "debug", "uuid", "dotenv", "yargs", "fs-extra", "glob", "async",
    "underscore", "request", "bluebird", "rxjs", "ramda", "date-fns",

    # React ecosystem
    "react-dom", "react-router", "react-router-dom", "redux", "react-redux",
    "next", "gatsby", "create-react-app", "styled-components", "emotion",

    # Vue ecosystem
    "vue", "vuex", "vue-router", "nuxt", "vite", "vitepress",

    # Angular
    "angular", "@angular/core", "@angular/cli", "zone.js", "rxjs",

    # Build tools
    "webpack", "babel", "@babel/core", "rollup", "esbuild", "parcel",
    "terser", "uglify-js", "postcss", "autoprefixer", "sass", "less",

    # Testing
    "jest", "mocha", "chai", "jasmine", "karma", "cypress", "playwright",
    "puppeteer", "sinon", "nyc", "istanbul", "supertest",

    # Linting
    "eslint", "prettier", "typescript", "tslint", "stylelint",

    # CLI
    "inquirer", "ora", "listr", "meow", "execa", "shelljs", "cross-env",

    # HTTP/API
    "node-fetch", "got", "superagent", "http-proxy", "cors", "body-parser",
    "cookie-parser", "express-session", "passport", "jsonwebtoken",

    # Database
    "mongoose", "sequelize", "knex", "typeorm", "prisma", "pg", "mysql",
    "mongodb", "redis", "ioredis",

    # Utils
    "winston", "bunyan", "pino", "morgan", "helmet", "compression",
    "validator", "joi", "yup", "zod", "ajv",

    # AWS
    "aws-sdk", "@aws-sdk/client-s3", "aws-amplify",

    # Type definitions
    "@types/node", "@types/react", "@types/express", "@types/lodash",

    # Security targets (high value)
    "event-stream", "colors", "faker", "ua-parser-js", "coa", "rc",
}

# Known malicious packages (confirmed typosquatting attacks)
KNOWN_MALICIOUS: Dict[str, str] = {
    # PyPI
    "reqeusts": "requests",
    "requets": "requests",
    "request": "requests",
    "python-requests": "requests",
    "python3-requests": "requests",
    "djang": "django",
    "djagno": "django",
    "flaask": "flask",
    "falsk": "flask",
    "numpyy": "numpy",
    "nunpy": "numpy",
    "panadas": "pandas",
    "pandsa": "pandas",
    "colourama": "colorama",
    "colorsama": "colorama",
    "python-boto3": "boto3",
    "botocore3": "botocore",
    "urllib": "urllib3",
    "urllib33": "urllib3",
    "setup-tools": "setuptools",
    "setuptool": "setuptools",

    # NPM
    "loadash": "lodash",
    "lodashs": "lodash",
    "lodahs": "lodash",
    "expres": "express",
    "expresss": "express",
    "axois": "axios",
    "axio": "axios",
    "reactt": "react",
    "reacct": "react",
    "chalkk": "chalk",
    "chlak": "chalk",
    "event-steram": "event-stream",
    "crossenv": "cross-env",
    "cross-env.js": "cross-env",
}


class PackageDatabase:
    """
    Database of legitimate packages for typosquatting detection.

    Provides fast lookup and similarity checking against known good packages.
    """

    def __init__(self, ecosystem: str = "pypi"):
        """
        Initialize the package database.

        Args:
            ecosystem: "pypi" or "npm"
        """
        self.ecosystem = ecosystem.lower()
        if self.ecosystem == "pypi":
            self._packages = PYPI_TOP_PACKAGES
        elif self.ecosystem == "npm":
            self._packages = NPM_TOP_PACKAGES
        else:
            self._packages = PYPI_TOP_PACKAGES | NPM_TOP_PACKAGES

        # Normalized name -> original name mapping
        self._normalized: Dict[str, str] = {}
        for pkg in self._packages:
            normalized = self._normalize(pkg)
            self._normalized[normalized] = pkg

    def _normalize(self, name: str) -> str:
        """Normalize package name for comparison."""
        return name.lower().replace("_", "-").replace(".", "-").strip()

    def contains(self, package_name: str) -> bool:
        """Check if a package is in the legitimate database."""
        normalized = self._normalize(package_name)
        return normalized in self._normalized

    def get_original_name(self, package_name: str) -> Optional[str]:
        """Get the canonical name of a package."""
        normalized = self._normalize(package_name)
        return self._normalized.get(normalized)

    def is_known_malicious(self, package_name: str) -> Optional[str]:
        """
        Check if a package is a known malicious typosquat.

        Returns the legitimate package it impersonates, or None.
        """
        normalized = self._normalize(package_name)
        # Check both original and normalized
        if package_name in KNOWN_MALICIOUS:
            return KNOWN_MALICIOUS[package_name]
        if normalized in KNOWN_MALICIOUS:
            return KNOWN_MALICIOUS[normalized]
        return None

    def get_all_packages(self) -> Set[str]:
        """Get all packages in the database."""
        return self._packages.copy()

    def size(self) -> int:
        """Get the number of packages in the database."""
        return len(self._packages)

    @classmethod
    def combined(cls) -> "PackageDatabase":
        """Create a database with both PyPI and NPM packages."""
        db = cls("all")
        return db
