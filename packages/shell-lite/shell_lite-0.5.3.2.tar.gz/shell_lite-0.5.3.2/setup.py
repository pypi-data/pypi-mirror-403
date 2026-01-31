from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="shell-lite",
    version="0.05",
    author="Shrey Naithani",
    author_email="mrytshplays@gmail.com",
    description="ShellLite: The English-Like Programming Language with LLVM Backend",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Shrey-N/ShellDesk",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        "llvmlite>=0.40.0",
        "colorama",
        "prompt_toolkit",
        "pygments",
        "pyinstaller"
    ],
    entry_points={
        'console_scripts': [
            'shl=shell_lite.main:main',
        ],
    },
)
