from setuptools import setup, find_packages

setup(
    name="Topsis-Mehak-102303724",  
    version="1.0.0",
    author="Mehak Goyal",
    author_email="mgoyal2_be23@thapar.edu",
    description="A package for TOPSIS implementation",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'topsis=Topsis_Mehak_102303724.topsis:main', 
        ],
    },
)