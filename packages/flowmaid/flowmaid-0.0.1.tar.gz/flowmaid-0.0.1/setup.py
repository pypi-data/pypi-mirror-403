import setuptools
import pathlib

component_name = "flowmaid"

# See https://docs.streamlit.io/library/components/publish
# rm -rf dist/;python3 setup.py sdist bdist_wheel;twine upload dist/*
setuptools.setup(
    name=component_name,
    version="0.0.1",
    description="A pure Python library designed to convert Mermaid flowcharts into SVG.",
    long_description=pathlib.Path('README.md').read_text(),
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    include_package_data=True,
    author='Alireza Ghasemi',
    author_email='ghasemi.a.ir@gmail.com',
    url='https://github.com/aghasemi/flowmaid.py',
    install_requires=[],
    keywords=['Python', 'Mermaid.js'],
    python_requires=">=3.8",
)