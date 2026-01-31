from setuptools import setup, find_packages

setup(
    name="Topsis-Himanshu-102303786",  # Replace with your details
    version="0.1.0",
    author="Himanshu Bansal",
    author_email="himanshubansal162005@gmail.com",
    description="A Python package to solve Multi-Criteria Decision Making problems using TOPSIS.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),  # will find the 'topsis' folder
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        'console_scripts': [
            'topsis=topsis.topsis:main',  # makes 'topsis' command available
        ],
    },
    python_requires='>=3.7',
)
