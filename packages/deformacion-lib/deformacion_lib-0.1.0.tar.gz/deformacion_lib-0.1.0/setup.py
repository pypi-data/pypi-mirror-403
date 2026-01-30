from setuptools import setup, find_packages

setup(
    name="deformacion_lib",
    version="0.1.0",
    description="Library for deformation analysis in tensile tests and 3D structures",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Martin Esteban, Oier Labeaga, Malen Ubiria, Eneko Urrutia",
    author_email="martin.esteban@alumni.mondragon.edu, oier.labeaga@alumni.mondragon.edu, malen.ubiria@alumni.mondragon.edu, eneko.urrutia@alumni.mondragon.edu",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "opencv-python>=4.5.0",
        "numpy>=1.19.0",
        "matplotlib>=3.3.0",
        "pandas>=1.1.0",
        "Pillow>=8.0.0",
        "imageio>=2.9.0",
    ],
)