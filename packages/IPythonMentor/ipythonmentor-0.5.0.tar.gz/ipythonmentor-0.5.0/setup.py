from setuptools import find_packages, setup


setup(
    name="IPythonMentor",
    version="0.5.0",
    description="Grade Python submissions with Gemini feedback.",
    packages=find_packages(),
    include_package_data=False,
    install_requires=[
        "google-genai>=0.4.0",
    ],
    python_requires=">=3.9",
)
