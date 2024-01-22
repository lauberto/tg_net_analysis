from setuptools import setup, find_packages

setup(
    name="tg_net_analysis",
    version="1.0.0",
    author="Andrea Grillandi",
    packages=find_packages(),
    python_requires=">=3.10.0",
    install_requires=[
        "pytest>=7.4.4",
        "pytest-asyncio>=0.23.3",
        "python-dotenv>=1.0.0",
        "telethon>=1.33.1",
    ]
)