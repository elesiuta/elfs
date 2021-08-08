import setuptools
import elfs

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="elfs",
    version=elfs.VERSION,
    description="Almost, but not quite, entirely unlike aliases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elesiuta/elfs",
    py_modules=["elfs"],
    entry_points={"console_scripts": ["elfs = elfs:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
)
