from setuptools import setup, find_packages

setup(
    name='biatoolkit',
    version='1.2.2',
    packages=find_packages(),
    install_requires=[],
    author='Bia Platform Team',  
    author_email='data.platform@sankhya.com.br',
    description='Biblioteca para desenvolvedores que utilizam o BiaAgentBuilder',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    long_description=open('README_PUBLIC.md').read(),
    long_description_content_type='text/markdown',

)