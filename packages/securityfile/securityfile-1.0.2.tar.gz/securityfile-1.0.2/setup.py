from setuptools import setup, find_packages

setup(
    name="securityfile",  # 包名
    keywords="securityfile",
    version="1.0.2",  # 版本号
    packages=find_packages(),  # 自动查找包
    author="ASMan",
    author_email="",
    description="python security",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="",  # 项目主页
    entry_points={
        "console_scripts": [
            "securityfile=securityfile.main:main",
        ],
    },
    install_requires=[
        "pycryptodome",
    ],  # 依赖包列表
)
