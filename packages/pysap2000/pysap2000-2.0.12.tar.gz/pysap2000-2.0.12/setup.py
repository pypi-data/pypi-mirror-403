from setuptools import setup, find_packages

setup(
    name="pysap2000",
    version="2.0.12",
    description="Python wrapper for SAP2000 structural analysis software API with LangChain AI agent support",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="jiangyao",
    author_email="631488424@qq.com",
    url="https://github.com/jiangyao/pysap2000",
    packages=find_packages(include=['PySap2000', 'PySap2000.*'], exclude=['PySap2000.tests', 'PySap2000.tests.*', 'PySap2000.docs', 'PySap2000.docs.*']),
    python_requires=">=3.8",
    install_requires=[
        "comtypes>=1.1.0",
    ],
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
    ],
)
