from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="thinkhive",
    version="3.2.0",
    author="ThinkHive",
    author_email="support@thinkhive.ai",
    description="AI agent observability SDK with business metrics, ROI analytics, and 25+ trace format support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Abdul-Omira/ThinkHiveMind",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "opentelemetry-exporter-otlp-proto-http>=1.20.0",
        "requests>=2.28.0",
    ],
)
