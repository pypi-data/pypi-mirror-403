from setuptools import setup, find_packages
import os

def readme():
    with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:
        return f.read()

setup(
    name="humanbytes",
    version="1.0.0",
    description="Convert bytes to human-readable sizes (KB, MB, KiB, MiB, etc.)",
    long_description=readme(),
    long_description_content_type="text/markdown",
    author="Zsombroo",
    url="https://github.com/Zsombroo/humanbytes",
    packages=find_packages(),
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    license="MIT",
    include_package_data=True,
    zip_safe=False,
)
