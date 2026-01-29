from setuptools import setup, find_packages

setup(
    name="ekansnake-cli-game",  # MUST be unique on PyPI
    version="1.0.2",
    author="Abhishek Jha",
    description="A CLI Snake Game with obstacles and high scores",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AbhishekJha3511/cli-snake-game",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "windows-curses; platform_system=='Windows'",
    ],
    entry_points={
        "console_scripts": [
            "ekansnake=ekansnake_game:main_menu",
        ],
    },
)