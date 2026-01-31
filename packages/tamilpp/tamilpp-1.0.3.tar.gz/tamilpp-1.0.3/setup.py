from setuptools import setup, find_packages

setup(
    name="tamilpp",                      # The name on PyPI (must be unique)
    version="1.0.3",
    packages=find_packages(),
    
    # This magic line creates the command 'tamilpp' in your terminal
    entry_points={
        'console_scripts': [
            'tamilpp=tamilpp.main:main',
        ],
    },
    
    author="Shriman M",
    author_email="shrimanmec@gmail.com",
    description="A Python-based programming language in Tamil",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/shrimanm/tamilpp", # Optional
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)