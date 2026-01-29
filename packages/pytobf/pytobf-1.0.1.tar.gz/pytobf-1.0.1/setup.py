from setuptools import setup, find_packages

setup(
    name="pytobf",
    version="1.0.1",
    author="MurilooPrDev",
    description="The sacred Python to Brainfuck transpiler",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'pytobf=main:main',
        ],
    },
    python_requires='>=3.6',
)
