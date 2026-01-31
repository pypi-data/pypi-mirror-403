from setuptools import setup, find_packages

setup(
    name="pundesh",
    version="0.0.3",
    description="Automation Toolkit: Google Maps Scraper + Electronics Bazaar Review Automation",
    author="Sidharth",
    packages=find_packages(),

    python_requires=">=3.8",

    install_requires=[
        "playwright>=1.40,<2.0",
        "pandas>=1.5,<3.0",
    ],

    extras_require={
        "stealth": [
            "playwright-stealth>=1.0.6",
        ],
    },

    include_package_data=True,

    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Automation",
    ],
)

