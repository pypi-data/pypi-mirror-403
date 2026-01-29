from setuptools import setup, find_packages

setup(
    name="pytobf-muriloopr",
    version="1.0.0",
    author="MurilooPrDev",
    description="A sacred transpiler from Python to Brainfuck",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'pytobf=main:main',
        ],
    },
    python_requires='>=3.6',
)
