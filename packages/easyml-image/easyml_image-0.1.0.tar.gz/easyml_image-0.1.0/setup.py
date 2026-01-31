from setuptools import setup, find_packages

setup(
    name="easyml-image",          # MUST be unique on PyPI
    version="0.1.0",
    author="B. Tharun Bala",
    author_email="your_email@gmail.com",
    description="PyTorch CNN library for image classification using folder-based datasets",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/potato_cnn_lib",
    packages=find_packages(),
    install_requires=[
        "torch",
        "torchvision",
        "numpy",
        "scikit-learn",
        "matplotlib",
        "seaborn"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
