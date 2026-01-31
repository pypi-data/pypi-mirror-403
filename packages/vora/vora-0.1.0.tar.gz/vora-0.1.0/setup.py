from setuptools import setup

setup(
    name="vora",
    version="0.1.0",
    long_description="VoRA",
    long_description_content_type="text/markdown",
    packages=["vora"],
    install_requires=["numpy",  "h5py", "matplotlib", "pandas"],
)
