import os
from setuptools import setup, find_packages

# Read version from version.txt
with open("version.txt", "r") as f:
    version = f.read().strip()
    
# Get the directory where setup.py is located
this_directory = os.path.abspath(os.path.dirname(__file__))

# Read the contents of README.md
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="prometheux-mcp",
    version=version,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mcp>=1.0.0",
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "click>=8.0.0",
    ],
    entry_points={
        'console_scripts': [
            'prometheux-mcp=prometheux_mcp.__main__:main',
        ],
    },
    include_package_data=True,
    author='Prometheux Limited',
    author_email='davben@prometheux.co.uk',
    description='Model Context Protocol (MCP) server for Prometheux - enabling AI agents to interact with knowledge graphs and reasoning',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/prometheuxresearch/px-mcp-server',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    python_requires='>=3.10',
    license='BSD-3-Clause',
)
