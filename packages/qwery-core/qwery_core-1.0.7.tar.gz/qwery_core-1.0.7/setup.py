from setuptools import setup, find_packages

setup(
    name="qwery_core",
    version="1.0.7",
    author="DEVIL",
    author_email="pxgito@gmail.com",
    description="Qwery Core Binary Runner",
    long_description_content_type="text/markdown",
    url="https://t.me/NexLangPy",

    packages=find_packages(),

    include_package_data=True,
    package_data={
        "qwery_core": [
            "bin/android/Devil",
            "bin/ish/Devil",
        ]
    },

    entry_points={
        "console_scripts": [
            "qwery=qwery_core.launcher:main"
        ]
    },

    python_requires=">=3.7",
)