from setuptools import setup, find_packages


setup(
    name="rpa-arc",
    version="0.7.0",
    description="CLI para gerar estrutura de projetos RPA com padrão definido",
    author="Luis Henrique",
    author_email="luis.costa@tecksolucoes.com.br",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        "requests",
        "python-dotenv",
        "selenium",
        "webdriver-manager"
    ],
    entry_points={
        "console_scripts": [
            "rpa-arc = rpa_arc.cli:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)

#python setup.py sdist bdist_wheel