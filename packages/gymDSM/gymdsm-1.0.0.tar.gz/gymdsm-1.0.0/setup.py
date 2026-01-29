import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    # PyPI distribution name (pip install gymDSM)
    name="gymDSM",
    version="1.0.0",
    author="Daniel Saromo",
    author_email="danielsaromo@gmail.com",
    description=(
        "gymDSM (Didactically Supercharged Mod): a small library that provides "
        "didactically enhanced OpenAI Gym environments (e.g., a MountainCar variant "
        "whose render color shows the last action)."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DanielSaromo/gymDSM",
    packages=setuptools.find_packages(),
    install_requires=[
        "gym==0.22",
        "numpy",
    ],
    extras_require={
        "render": ["pygame"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.7",
)
