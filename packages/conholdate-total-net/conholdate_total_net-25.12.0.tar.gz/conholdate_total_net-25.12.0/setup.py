from setuptools import setup

setup(
    name="conholdate-total-net",
    version="25.12.0",
    description="Conholdate.Total for Python via .NET metapackage that enables you to install all available GroupDocs for Python via .NET products.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Conholdate",
    author_email="support@conholdate.com",
    url="https://products.conholdate.com/",
    license="Other/Proprietary License",
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: Other/Proprietary License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    keywords=[
        "Conholdate.Total for Python via .NET",
        "Conholdate for Python via .NET",
        "metapackage",
        "document conversion",
        "document viewing",
        "document comparison",
        "watermarking",
        "metadata",
        "document merger",
        "document assembly",
        "redaction",
        "digital signature",
    ],
    python_requires=">=3.9, <3.12",
    install_requires=[
        "aspose-total-net==25.12.0",
        "groupdocs-total-net==25.12"
    ],
    packages=[],
    zip_safe=False,
)
