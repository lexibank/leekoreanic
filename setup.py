from setuptools import setup
import json


with open("metadata.json", encoding="utf-8") as fp:
    metadata = json.load(fp)


setup(
    name="lexibank_leekoreanic",
    description=metadata["title"],
    license=metadata.get("license", ""),
    url=metadata.get("url", ""),
    py_modules=["lexibank_leekoreanic"],
    include_package_data=True,
    zip_safe=False,
    entry_points={"lexibank.dataset": ["leekoreanic=lexibank_leekoreanic:Dataset"]},
    install_requires=["pylexibank>=2.3.0", "openpyxl"],
    extras_require={"test": ["pytest-cldf"]},
)
