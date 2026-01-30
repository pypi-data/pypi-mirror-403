"""Setup script for js2 - Just Screen Share."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="js2",
    version="0.1.0",
    author="Sirojiddin Dushaev",
    author_email="sirojiddin@example.com",
    description="Just Screen Share - Share your screen with a public URL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sirojiddindushaev/js2",
    project_urls={
        "Bug Reports": "https://github.com/sirojiddindushaev/js2/issues",
        "Source": "https://github.com/sirojiddindushaev/js2",
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "js2_pkg": ["static/*.html"],
    },
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "js2=js2_pkg.cli:main",
        ],
    },
    keywords="screen-share, screenshare, screen, share, ngrok, tunnel, remote",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications",
        "Topic :: Multimedia :: Video",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
