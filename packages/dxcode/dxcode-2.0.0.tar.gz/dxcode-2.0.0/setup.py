"""
dxcode - 带有 `dx` 前缀的自定义编码算法
Python 包安装配置
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dxcode",
    version="2.0.0",
    author="Dogxi",
    author_email="hi@dogxi.me",
    description="[dxcode] A distinctive, URL‑safe binary encoder with the signature `dx` prefix and CRC16 checksum.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dogxii/dxcode",
    project_urls={
        "Bug Tracker": "https://github.com/dogxii/dxcode/issues",
        "Homepage": "https://dxc.dogxi.me",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    py_modules=["dxcode"],
    python_requires=">=3.7",
    keywords="dx dxcode encoding decoding base64 dogxi binary text",
    license="MIT",
)
