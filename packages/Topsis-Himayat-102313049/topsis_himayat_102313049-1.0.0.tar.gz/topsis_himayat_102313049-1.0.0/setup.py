from setuptools import setup, find_packages

setup(
    name="Topsis-Himayat-102313049",
    version="1.0.0",
    author="Himayat",
    author_email="htiwana_be23@thapar.edu",
    description="TOPSIS Command Line Tool",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_himayat.main:main"
        ]
    },
)
