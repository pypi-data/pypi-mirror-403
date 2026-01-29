
from setuptools import setup, find_packages

setup(
    name="deepdrift",
    version="0.4.0",
    author="Alexey Evtushenko",
    author_email="alexey@eutonics.ru",
    description="Production-grade Kinetic Monitoring for Neural Networks (Semantic Velocity)",
    long_description="DeepDrift treats neural networks as dynamic systems, measuring the 'velocity' of hidden states to detect OOD, Fraud, and Hallucinations. Version 0.4.0 introduces Sparse Sampling (<1% overhead) and Robust Thresholding.",
    long_description_content_type="text/plain",
    url="https://github.com/Eutonics/DeepDrift",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires='>=3.8',
    install_requires=[
        "torch>=1.10.0",
        "numpy>=1.21.0",
        "scikit-learn>=1.0.0",
        "pandas>=1.3.0",
        "tqdm"
    ],
)
