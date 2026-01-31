from setuptools import setup, find_packages

setup(
    name='portier-cli',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'click>=8.0.0',
        'pyyaml>=6.0',
        'docker>=6.0.0',
        'rich>=13.0.0',
    ],
    entry_points={
        'console_scripts': [
            'portier=portier.cli:main',
        ],
    },
    author='Ton Nom',
    description='Gestionnaire de ports pour applications Docker',
    python_requires='>=3.8',
)