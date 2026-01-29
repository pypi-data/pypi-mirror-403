import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

INSTALL_REQUIRES = [
    'numpy',
    'pandas',
]

setuptools.setup(
    name="tactrandom",
    version="1.0.1",
    author="Raja CSP Raman",
    author_email="raja.csp@gmail.com",
    description="TRandom - Python package that generates fake data for you",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tactlabs/tact-random",
    packages=setuptools.find_packages(exclude=['sampleui', 'sampleui.*', 'tact-random', 'tests']),
    package_data={
        "trandom": ["py.typed", "proxy.pyi"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
    ],
    install_requires=INSTALL_REQUIRES,
    python_requires='>=3.10',
    zip_safe=False
)