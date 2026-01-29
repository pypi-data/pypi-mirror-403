"""Setup script for easy-sgr package."""

from setuptools import setup, find_packages

# Читаем длинное описание из README
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = ""

# Читаем версию из __init__.py
def get_version():
    """Extract version from package __init__.py."""
    import re
    import os
    
    init_path = os.path.join(os.path.dirname(__file__), "easy_sgr", "__init__.py")
    if os.path.exists(init_path):
        with open(init_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    return "0.1.0"

setup(
    # Основная информация о пакете
    name="easy-sgr",
    version=get_version(),
    author="Maksim",
    author_email="maks6863@gmail.com",
    description="A simplified interface for SGR (Schema-Guided Reasoning) agents in LangChain style",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",  # URL репозитория (можно добавить позже)
    
    # Лицензия
    license="MIT",
    
    # Классификаторы для PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    
    # Ключевые слова
    keywords=[
        "sgr",
        "schema-guided-reasoning",
        "langchain",
        "ai",
        "llm",
        "agent",
        "openai",
        "tool-calling",
    ],
    
    # Зависимости
    python_requires=">=3.10",
    install_requires=[
        "fastmcp",
        "jambo",
        "openai",
        "pydantic>=2.0",
        "pydantic-settings",
        "fastapi",
        "uvicorn",
        "pyyaml",
        "httpx",
        "tavily-python",
        "python-dotenv",
    ],
    
    # Опциональные зависимости
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
        ],
    },
    
    # Пакеты для включения (автоматический поиск)
    packages=find_packages(include=["easy_sgr*"]),
    
    # Данные пакета (файлы, которые не являются Python кодом)
    package_data={
        "easy_sgr": ["sgr_agent_core/prompts/*.txt"],
    },
    
    # Включить данные пакета
    include_package_data=True,
    
    # Zip safe - можно ли устанавливать пакет как zip-архив
    zip_safe=False,
)
