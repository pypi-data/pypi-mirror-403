from setuptools import setup

setup(
    name="dockposegen",
    version="1.0.0",  
    author="fred",
    description="A Tool for Ligands pose extraction and Complex Building Workflow",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/alpha-horizon/dockposegen.git",
    py_modules=["dockposegen"], 
    install_requires=[
        'numpy',
        'pandas',
    ],
    entry_points={
        'console_scripts': [
            'dockposegen=dockposegen:main', 
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
