from setuptools import setup, find_packages

with open("README.md","r") as f:
    description = f.read()

setup(
    name='commlab',
    version='0.2.0',
    description='Communication Lab utilities for signal processing and noise addition',
    author='Padmapriya C J',
    author_email='padmapriyacj06@gmail.com',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.20.0',
    ],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
long_description=open("README.md").read(),
long_description_content_type="text/markdown",