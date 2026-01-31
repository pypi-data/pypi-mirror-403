from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = [
    "PyPDF2==3.0.1",
    "google-generativeai>=0.3.2",
    "rich>=13.7.0",
    "python-docx>=1.1.0",
    "matplotlib>=3.8.0",
    "pandas>=2.1.0",
    "seaborn>=0.13.0",
    "numpy>=1.26.0"
]

setup(
    name="lazycook",
    version="1.2.1",
    author="Hitarth Trivedi(Alpha.Kore),Harsh Bhatt(Alpha.Kore)",
    license="Proprietary",
    license_files=(),
    author_email="hitartht318@gmail.com, bhattharsh328@gmail.com",
    maintainer="Hitarth Trivedi(Alpha.Kore),Harsh Bhatt(Alpha.Kore)",
    maintainer_email="hitartht318@gmail.com, bhattharsh328@gmail.com",
    description="LazyCook is an autonomous multi-agent conversational assistant designed to intelligently process user queries, manage documents, store conversations, and maintain iterative AI reasoning loops. It uses Gemini 2.5 Flash model with a four-agent architecture for high-quality responses and continuous learning.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),

    python_requires=">=3.10",
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
)