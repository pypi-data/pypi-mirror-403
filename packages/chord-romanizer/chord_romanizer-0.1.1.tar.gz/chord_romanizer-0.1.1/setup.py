from setuptools import setup, find_packages

setup(
    name="chord_romanizer",
    version="0.1.1",
    description="A library to analyze chord progressions and convert them to Roman numeral analysis.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="anime-song",
    url="https://github.com/anime-song/chord-romanizer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
