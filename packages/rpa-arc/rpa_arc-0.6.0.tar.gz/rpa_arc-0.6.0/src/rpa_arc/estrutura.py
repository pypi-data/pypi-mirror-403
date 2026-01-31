import os
from pathlib import Path
from .conteudos import *


# Estrutura base que será criada
ESTRUTURA_PROJETO = {
    "src": {
        "app": ["app.py"],
        "core": ["logger.py", "driver.py"],
        "integracoes": [],
        "utils": {
            "helpers": []
        },
        "api": ["Api.py"]
    },
    "config": [],
    "dados": [],
    "logs": [],
    "tests": [],
    "root_files": [
        "requirements.txt",
        ".env",
        "Dockerfile",
        "README.md",
        "main.py",
        ".gitignore",
        ".dockerignore"
    ]
}

# Estrutura mínima (sem Docker, sem API)
ESTRUTURA_MINIMA = {
    "src": {
        "app": ["app.py"],
        "core": ["logger.py", "driver.py"],
        "integracoes": [],
        "utils": {"helpers": []},
    },
    "config": [],
    "dados": [],
    "logs": [],
    "tests": [],
    "root_files": [
        "requirements.txt",
        ".env",
        "README.md",
        "main.py",
        ".gitignore",
    ]
}

# Arquivos raiz com conteúdo pré-definido
ROOT_FILE_CONTENT = {
    "requirements.txt": REQUIREMENTS_CONTENT.strip() + "\n",
    "Dockerfile": DOCKERFILE_CONTENT.strip() + "\n",
    ".gitignore": GITIGNORE_CONTENT.strip(),
    ".dockerignore": DOCKERIGNORE_CONTENT.strip(),
    ".env": ENV_CONTENT.strip(),
    "main.py": MAIN_PY_CONTENT.strip() + "\n",
    "README.md": README_MD_CONTENT.strip() + "\n",
}


def _write_root_files(base_path: Path, root_files: list, skip_existing: bool = False) -> None:
    """Cria os arquivos na raiz do projeto."""
    for arquivo in root_files:
        caminho = base_path / arquivo
        if skip_existing and caminho.exists():
            continue
        if arquivo in ROOT_FILE_CONTENT:
            caminho.write_text(ROOT_FILE_CONTENT[arquivo], encoding="utf-8")
        else:
            caminho.touch(exist_ok=True)
        print(f"📄 Criado: {caminho}")


def _write_init_py(path: Path, skip_existing: bool = False) -> None:
    """Cria __init__.py vazio para tornar o diretório um pacote Python."""
    init_file = path / "__init__.py"
    if skip_existing and init_file.exists():
        return
    init_file.write_text(INIT_PY_CONTENT, encoding="utf-8")
    print(f"📄 Criado: {init_file}")


def criar_estrutura(base_path: Path, minimal: bool = False, force: bool = False) -> None:
    """
    Cria a estrutura base do projeto RPA.

    Args:
        base_path: Diretório onde a estrutura será criada.
        minimal: Se True, cria apenas estrutura mínima (sem Docker, sem API).
        force: Se True, em diretório existente apenas adiciona arquivos faltantes (não sobrescreve).
    """
    estrutura = ESTRUTURA_MINIMA if minimal else ESTRUTURA_PROJETO
    skip_existing = force

    print(f"🛠️  Criando estrutura em: {base_path.resolve()}")

    # Criar pastas de primeiro nível
    for pasta in ["config", "dados", "logs", "tests"]:
        caminho = base_path / pasta
        caminho.mkdir(parents=True, exist_ok=True)
        print(f"📁 Criado: {caminho}")

    # Criar arquivos na raiz
    _write_root_files(base_path, estrutura["root_files"], skip_existing=skip_existing)

    # Criar estrutura dentro de src/
    src_path = base_path / "src"
    src_path.mkdir(exist_ok=True)
    _write_init_py(src_path, skip_existing)

    for pasta, conteudo in estrutura["src"].items():
        caminho_pasta = src_path / pasta
        caminho_pasta.mkdir(parents=True, exist_ok=True)
        _write_init_py(caminho_pasta, skip_existing)

        if pasta == "core":
            for arquivo in conteudo:
                caminho_arquivo = caminho_pasta / arquivo
                if skip_existing and caminho_arquivo.exists():
                    continue
                if arquivo == "logger.py":
                    caminho_arquivo.write_text(LOGGER_CONTENT.strip(), encoding="utf-8")
                elif arquivo == "driver.py":
                    caminho_arquivo.write_text(DRIVER_CONTENT.strip(), encoding="utf-8")
                else:
                    caminho_arquivo.touch()
                print(f"📄 Criado: {caminho_arquivo}")

        elif pasta == "api":
            for arquivo in conteudo:
                caminho_arquivo = caminho_pasta / arquivo
                if skip_existing and caminho_arquivo.exists():
                    continue
                if arquivo == "Api.py":
                    caminho_arquivo.write_text(API_CONTENT.strip(), encoding="utf-8")
                else:
                    caminho_arquivo.touch()
                print(f"📄 Criado: {caminho_arquivo}")

        elif pasta == "app":
            for arquivo in conteudo:
                caminho_arquivo = caminho_pasta / arquivo
                if skip_existing and caminho_arquivo.exists():
                    continue
                if arquivo == "app.py":
                    caminho_arquivo.write_text(APP_PY_CONTENT.strip(), encoding="utf-8")
                else:
                    caminho_arquivo.touch()
                print(f"📄 Criado: {caminho_arquivo}")

        elif isinstance(conteudo, list):
            for arquivo in conteudo:
                (caminho_pasta / arquivo).touch(exist_ok=True)
                print(f"📄 Criado: {caminho_pasta / arquivo}")

        elif isinstance(conteudo, dict):
            for subpasta, arquivos in conteudo.items():
                caminho_sub = caminho_pasta / subpasta
                caminho_sub.mkdir(parents=True, exist_ok=True)
                _write_init_py(caminho_sub, skip_existing)
                for arq in arquivos:
                    (caminho_sub / arq).touch(exist_ok=True)
                    print(f"📄 Criado: {caminho_sub / arq}")

    print("✅ Estrutura criada com sucesso!\n")
