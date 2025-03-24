# pip install -e . -> 개발 패키지로 설치 후 수정 가능

from setuptools import setup, find_packages

setup(
    name="data_analysis",
    version="1.0",
    packages=find_packages(),
)