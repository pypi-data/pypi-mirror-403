from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="vizpaint",
    version="0.1.5",  # 使用全新的版本号，避免任何缓存
    author="zhouxinjun",
    author_email="369013027@qq.com",
    description="A comprehensive Python data visualization library.",
    url="https://pypi.org/project/vizpaint/",
    # 长描述配置 - 确保紧跟基本元数据
    long_description=long_description,
    long_description_content_type="text/markdown",
    # 包和依赖
    packages=find_packages(),
    install_requires=["matplotlib>=3.3.0", "numpy>=1.19.0"],
    python_requires=">=3.7",
)
