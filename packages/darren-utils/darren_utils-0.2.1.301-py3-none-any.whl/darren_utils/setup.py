from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="darren_utils",
    version="0.2.1.301",
    author="Darren",
    author_email="2775856@qq.com",
    description="一个功能丰富的工具包",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Darren5211314",
    packages=['darren_utils', 'darren_utils.encry', 'darren_utils.proxy'],
    package_dir={'darren_utils': '.', 'darren_utils.encry': 'encry', 'darren_utils.proxy': 'proxy'},
    py_modules=['darren'],  # 支持 import darren
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "setuptools",
        "requests",
        "pyarmor>=9.0",
        "cryptography",
        "gmssl",
        "send2trash",
        "pyperclip",
        "psutil",
        "pillow",
        "redis",
        'httpx[http2]'
    ],
)
