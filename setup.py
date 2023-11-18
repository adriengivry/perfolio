from setuptools import setup, find_packages
import perfolio

# Read the requirements from the generated requirements.txt file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()
    
setup(
    name="perfolio",
    version=perfolio.__version__,
    author="Adrien Givry",
    description="Portfolio Performance Analysis",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "mcsgui = mcsgui.__main__:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
)
