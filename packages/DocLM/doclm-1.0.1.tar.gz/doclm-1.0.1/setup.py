from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="DocLM",
    version="1.0.1",
    author="Louati Mahdi",
    author_email="louatimahdi390@gmail.com",
    description="An intelligent document analysis library for Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/DocLM",  # Replace with your GitHub repo URL
    packages=find_packages(),
    install_requires=[
        "PyMuPDF",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
