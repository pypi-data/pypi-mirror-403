from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='portier-cli',
    version='0.1.4',
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

    # Informations affichées sur PyPI
    author='Franck AÏGBA',
    author_email='franckaigba4@gmail.com',
    description='Gestionnaire de ports pour vos applications Docker',
    long_description=long_description,
    long_description_content_type='text/markdown',

    # Lien vers GitHub
    url='https://github.com/Landers9/portier',
    project_urls={
        'Bug Tracker': 'https://github.com/Landers9/portier/issues',
        'Documentation': 'https://github.com/Landers9/portier#readme',
        'Source': 'https://github.com/Landers9/portier',
    },

    # Métadonnées
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    keywords='docker, ports, cli, devops, containers',
    python_requires='>=3.8',
)