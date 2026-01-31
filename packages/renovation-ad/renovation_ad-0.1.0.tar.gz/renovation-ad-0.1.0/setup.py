import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="renovation-ad",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A high-performance HTML ad cleaner using Adblock rules (Pure Python + lxml).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/renovation-ad",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires='>=3.7',
    install_requires=[
        "requests>=2.25.0",
        "lxml>=4.6.0",
        "cssselect>=1.1.0",      # 必須! 用於將 CSS 轉為 XPath
        "beautifulsoup4>=4.9.0", # 作為備援解析器
    ],
)