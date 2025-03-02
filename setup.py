from setuptools import setup, find_packages

setup(
    name="EIT_Thigh_Force_Estimation",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
