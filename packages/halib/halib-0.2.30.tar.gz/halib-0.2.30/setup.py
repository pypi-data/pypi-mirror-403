import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    required = f.read().splitlines()

setuptools.setup(
    name="halib",
    version="0.2.30",
    author="Hoang Van Ha",
    author_email="hoangvanhauit@gmail.com",
    description="Small library for common tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    include_package_data=True,  # This reads your MANIFEST.in
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=required,
)
