from setuptools import setup

setup(
    name="unphishable",
    version="7.0.2",
    author="Newton Achonduh",
    author_email="founderunphishable@gmail.com",
    description="Advanced phishing detection CLI tool",
    py_modules=["unphishable"],
    install_requires=[
        "requests>=2.28.0",
        "python-whois>=0.8.0", 
        "colorama>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "unphishable = unphishable.__main__:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)