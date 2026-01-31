from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='caspian-utils',
    version='0.0.32',
    author='Jefferson Abraham',
    packages=find_packages(),
    install_requires=[
        "fastapi~=0.110",
        "uvicorn~=0.27",
        "python-dotenv~=1.0",
        "jinja2~=3.1",
        "beautifulsoup4~=4.12",
        "tailwind-merge~=0.1",
        "slowapi~=0.1",
        "python-multipart~=0.0.9",
        "starsessions~=1.3",
        "httpx~=0.27",
        "werkzeug~=3.0",
        "cuid2~=2.0",
        "nanoid~=2.0",
        "python-ulid~=2.7",
    ],
    description='A utility package for Caspian projects',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/TheSteelNinjaCode/caspian_utils',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',
)
