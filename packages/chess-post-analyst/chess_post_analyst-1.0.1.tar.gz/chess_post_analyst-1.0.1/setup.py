"""
Chess Post-Game Analyst - Production-ready chess game analysis tool
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Core dependencies
requirements = [
    "python-chess>=1.999",
    "stockfish>=3.28.0",
    "click>=8.1.7",
    "colorama>=0.4.6",
    "tqdm>=4.66.1",
    "flask>=3.0.0",
    "flask-cors>=4.0.0",
    "python-dotenv>=1.0.0",
    "markdown>=3.5.1",
]

setup(
    name="chess-post-analyst",
    version="1.0.1",
    author="Lekhan",
    author_email="",
    description="A professional chess post-game analysis tool with CLI and web interfaces",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lekhanpro/chess-post-game-analyst",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment :: Board Games",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "chess-analyst=chess_analyst.cli:main",
        ],
    },
    include_package_data=True,
    keywords="chess analysis stockfish pgn game-analysis chess-engine",
    project_urls={
        "Bug Reports": "https://github.com/lekhanpro/chess-post-game-analyst/issues",
        "Source": "https://github.com/lekhanpro/chess-post-game-analyst",
    },
)
