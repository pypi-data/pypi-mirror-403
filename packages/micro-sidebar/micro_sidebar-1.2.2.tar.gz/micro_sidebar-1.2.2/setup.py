from setuptools import setup, find_packages

setup(
    name="micro_sidebar",
    version="1.2.2",
    author="DeBeski",
    author_email="debeski1@gmail.com",
    description="A Reusable RTL Django Sidebar App",
    long_description=open('README.md').read() if open('README.md') else '',
    long_description_content_type="text/markdown",
    url="https://github.com/debeski/micro-sidebar",
    packages=["sidebar"],
    include_package_data=True,
    classifiers=[
        "Framework :: Django",
        "Framework :: Django :: 5",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "Django>=5.1",
    ],
    license="MIT",
)
