from setuptools import setup, find_packages

setup(
    name='pyshielder',
    version='1.0.2',
    packages=find_packages(),
    author='PythonToday',
    author_email='pythontodayz@gmail.com',
    description='A robust tool for Python code obfuscation and encryption using Cython.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/PythonTodayz/pyshielder',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Security',
        'Topic :: Software Development :: Build Tools',
    ],
    install_requires=[
        'Cython',
    ],
    entry_points={
        'console_scripts': [
            'pyshielder=pyshielder.core:main',
        ],
    },
    python_requires='>=3.6',
)
