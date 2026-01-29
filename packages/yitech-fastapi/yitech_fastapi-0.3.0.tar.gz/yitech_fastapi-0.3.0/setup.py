"""项目安装配置"""

from setuptools import setup, find_packages

setup(
    name="yifast",
    version="1.0.0",
    description="FastAPI 脚手架工具",
    author="Yitech Team",
    author_email="contact@yitech.io",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1.7",
        "fastapi>=0.128.0",
        "uv>=0.1.0",
        "pyyaml>=6.0.1",
        "jinja2>=3.1.2",
    ],
    extras_require={
        "dev": [
            "ruff>=0.6.0",
            "mypy>=1.19.1",
            "pytest>=9.0.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "yifast=cli.main:cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
)