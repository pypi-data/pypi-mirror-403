REQUIREMENTS_CONTENT = """
requests>=2.28,<3
python-dotenv>=1.0,<2
selenium>=4.0,<5
webdriver-manager>=4.0,<5
fastapi>=0.100,<1
uvicorn>=0.22,<1
"""

ENV_CONTENT = """
####################API-RPA CREDENCIAIS#######################
BASE_URL_API_RPA="https://api-rpa-v2-prod.tecksolucoes.com.br"
USERNAME_API_RPA=
PASSWORD_API_RPA=
##############################################################
LOG_LEVEL=DEBUG
LOG_TZ=America/Sao_Paulo

"""

MAIN_PY_CONTENT = '''
"""Ponto de entrada do projeto RPA."""
from src.core.logger import Logger
from src.core.driver import GerenciadorNavegador

'''

README_MD_CONTENT = """# Projeto RPA

Estrutura base gerada por [rpa-arc](https://pypi.org/project/rpa-arc/).

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

## Estrutura

- `src/core/` - Logger e gerenciador de navegador
- `src/api/` - Cliente API
- `src/app/` - Módulo principal da aplicação
- `config/` - Configurações
- `dados/` - Dados e arquivos processados
- `logs/` - Logs do sistema
"""

APP_PY_CONTENT = '''
"""Módulo principal da aplicação RPA."""
from src.core.logger import Logger

'''

INIT_PY_CONTENT = ""

API_CONTENT = '''
import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from src.core.logger import Logger
import pandas as pd
import base64
import time
import json

from dotenv import load_dotenv

load_dotenv(override=True)


class Api:
    def __init__(self, logger=None, max_retries=5, retry_delay=5.0):
        self.base_url = os.getenv("BASE_URL_API_RPA")
        if not self.base_url:
            raise ValueError("BASE_URL_API_RPA não configurada no .env")

        self.token: Optional[str] = None
        self.logger = logger or Logger(__name__).get_logger()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # ---------- Autenticação ----------
    def authenticate(self) -> None:
        url = f"{self.base_url}/v2/auth/token"
        resp = requests.post(url, json={"username": os.getenv("USERNAME_API_RPA"), "password": os.getenv("PASSWORD_API_RPA")})
        if resp.status_code != 200:
            msg = f"Erro ao autenticar: status={resp.status_code} body={resp.text}"
            self.logger.error(msg)
            raise Exception(msg)

        data = resp.json()
        self.token = data["access_token"]

    def _headers(self) -> Dict[str, str]:
        if not self.token:
            self.authenticate()
        return {"Authorization": f"Bearer {self.token}"}

    def CheckToken(self) -> None:
        """Valida/renova o token automaticamente."""
        if not self.token:
            self.authenticate()
        else:
            self.authenticate()

    def GetToken(self) -> str:
        """Retorna o token atual; autentica se necessário."""
        if not self.token:
            self.authenticate()
        return self.token

    # ---------- Requisição com Retry ----------
    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Executa requisição HTTP com retry automático para erros 429 (rate limit) e 5xx.
        
        Args:
            method: Método HTTP (GET, POST, etc)
            url: URL da requisição
            **kwargs: Parâmetros adicionais para requests
            
        Returns:
            Response object
        """
        for attempt in range(self.max_retries):
            try:
                resp = requests.request(method, url, **kwargs)
                
                # Se receber 429 (Too Many Requests), aguarda e tenta novamente
                if resp.status_code == 429:
                    retry_after = self._parse_retry_after(resp)
                    wait_time = retry_after if retry_after else (self.retry_delay * (2 ** attempt))
                    
                    self.logger.warning(f"Rate limit atingido (429). Aguardando {wait_time:.1f}s antes de tentar novamente... (Tentativa {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                
                # Se receber erro 5xx, tenta novamente com backoff exponencial
                if 500 <= resp.status_code < 600:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        self.logger.warning(f"Erro {resp.status_code} no servidor. Aguardando {wait_time:.1f}s antes de tentar novamente... (Tentativa {attempt + 1}/{self.max_retries})")
                        time.sleep(wait_time)
                        continue
                
                # Se a resposta for bem-sucedida ou outro erro (4xx exceto 429), retorna
                return resp
                
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(f"Erro na requisição: {str(e)}. Aguardando {wait_time:.1f}s antes de tentar novamente... (Tentativa {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    raise
        
        # Se todas as tentativas falharam, retorna a última resposta
        return resp
    
    def _parse_retry_after(self, response: requests.Response) -> Optional[float]:
        """
        Extrai o tempo de espera do header Retry-After ou do corpo da resposta.
        
        Args:
            response: Response object com erro 429
            
        Returns:
            Tempo em segundos para aguardar, ou None
        """
        # Tenta obter do header Retry-After
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        
        # Tenta extrair do corpo da mensagem (ex: "Tente novamente em 51 segundos")
        try:
            body = response.text
            import re
            match = re.search(r"(\\d+)\\s*segundos?", body)
            if match:
                return float(match.group(1))
        except:
            pass
        
        return None


    # ---------- Enviar Log para S3 ----------
    def EnviarArquivoS3(self, caminho_arquivo: str, caminho_destino: str = "") -> Dict[str, Any]:
        """Envia arquivo para S3 (alias para enviar_log_s3)."""
        return self.enviar_log_s3(caminho_arquivo, caminho_destino)

    def enviar_log_s3(self, caminho_arquivo: str, caminho_destino: str = "") -> Dict[str, Any]:
        """
        Envia um arquivo de log para o endpoint /logs_robos/enviar-s3/
        Retorna JSON com 'message' e 'url_temporaria'.
        """
        url = f"{self.base_url}/v2/logs_robos/enviar-s3/"
        headers = self._headers()

        with open(caminho_arquivo, "rb") as f:
            files = {"arquivo": (os.path.basename(caminho_arquivo), f, "application/octet-stream")}
            data = {"caminho": caminho_destino}
            resp = requests.post(url, headers=headers, files=files, data=data)

        resp.raise_for_status()
        return resp.json()

'''

LOGGER_CONTENT = """
import logging
import os
import logging
import os
import re
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore[misc, assignment]


def _log_level_from_env():
    #Lê LOG_LEVEL do ambiente (DEBUG, INFO, WARNING, ERROR). Se não definido ou inválido, retorna None.
    s = (os.getenv("LOG_LEVEL") or "").strip().upper()
    if s in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        return getattr(logging, s)
    return None


def _get_log_tz():
    #Retorna o ZoneInfo para LOG_TZ (padrão: America/Sao_Paulo).
    if ZoneInfo is None:
        return None
    tz_name = (os.getenv("LOG_TZ") or "America/Sao_Paulo").strip()
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("America/Sao_Paulo")


def formatted_now() -> str:
    #Retorna o instante atual no fuso LOG_TZ, formatado para logs (ex.: main.py).
    tz = _get_log_tz()
    if tz:
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class TZFormatter(logging.Formatter):
    #Formatter que usa o fuso LOG_TZ (padrão America/Sao_Paulo) para %(asctime)s.

    def formatTime(self, record, datefmt=None):
        tz = _get_log_tz()
        if tz is None:
            return super().formatTime(record, datefmt)
        dt = datetime.fromtimestamp(record.created, tz=tz)
        if datefmt:
            return dt.strftime(datefmt)
        s = dt.strftime("%Y-%m-%d %H:%M:%S")
        s = s + ",%03d" % record.msecs
        return s


def _today_log_filename() -> str:
    #Nome do arquivo de log do dia no fuso LOG_TZ (ex.: 2026-01-22.log).
    tz = _get_log_tz()
    if tz:
        return datetime.now(tz).strftime("%Y-%m-%d.log")
    return datetime.now().strftime("%Y-%m-%d.log")


class DailyFileHandler(TimedRotatingFileHandler):
    def __init__(self, log_dir: str, log_level=logging.DEBUG):
        os.makedirs(log_dir, exist_ok=True)
        filename = os.path.join(log_dir, _today_log_filename())
        super().__init__(filename, when='midnight', interval=1, backupCount=0, encoding='utf-8')
        self.setLevel(log_level)
        fmt = TZFormatter('%(asctime)s - %(levelname)s - %(message)s')
        self.setFormatter(fmt)
        self.suffix = ""
        # Padrão que nunca casa (backupCount=0); evita type error em extMatch (Pattern[str])
        self.extMatch = re.compile(r"$.^")

    def doRollover(self):
        if self.stream:
            self.stream.close()
        new_name = _today_log_filename()
        self.baseFilename = os.path.join(self.baseFilename.rsplit(os.sep, 1)[0], new_name)
        self.stream = open(self.baseFilename, 'a', encoding=self.encoding)


class Logger:
    def __init__(self, name=__name__, log_dir='logs', log_level=logging.DEBUG):
        effective = _log_level_from_env()
        level = effective if effective is not None else log_level
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        # evita handlers duplicados
        if not self.logger.handlers:
            daily_handler = DailyFileHandler(log_dir, level)
            console = logging.StreamHandler()
            console.setLevel(level)
            console.setFormatter(TZFormatter('%(asctime)s - %(levelname)s - %(message)s'))

            self.logger.addHandler(daily_handler)
            self.logger.addHandler(console)

    def get_logger(self):
        return self.logger
"""



DRIVER_CONTENT = '''
import os
import platform
import re
import subprocess
import socket
import shutil
import tempfile
import atexit
import glob
import errno
import time
import uuid
try:
    import fcntl
except ImportError:
    pass
from tempfile import mkdtemp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import threading
import random


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class GerenciadorNavegador:
    def __init__(self, diretorio_arquivo=None, cod_convenio: str|int|None="RPA") -> None:
        if not diretorio_arquivo:
            diretorio_arquivo = os.path.abspath("dados/arquivos")
        os.makedirs(diretorio_arquivo, exist_ok=True)

        self._DIRETORIO_ARQUIVO = diretorio_arquivo
        self._driver = None
        self._cod = str(cod_convenio) if cod_convenio is not None else "GLOBAL"

        self._tmp_base = os.environ.get("TMPDIR") or tempfile.gettempdir()
        # prefixo com PID/TID + timestamp → zero colisão
        self._prefix_name = f"rpa_chrome_cod_{self._cod}_pid{os.getpid()}_tid{threading.get_ident()}_{int(time.time()*1000)}_"
        self._rpa_tmp_dir = None
        # Lock file para prune de diretórios temporários (evita corrida entre processos)
        self._gc_lockfile = os.path.join(self._tmp_base, f"rpa_chrome_gc_lock_{self._cod}_{os.getpid()}.lock")

    def _mk_fresh_tmp(self) -> str:
        try:
            return tempfile.mkdtemp(dir=self._tmp_base, prefix=self._prefix_name)
        except OSError as e:
            if e.errno == errno.ENOSPC:
                self._prune_stale_tmp_dirs(max_age_minutes=180)
                return tempfile.mkdtemp(dir=self._tmp_base, prefix=self._prefix_name)
            raise

    def _glob_my_dirs(self, pattern_suffix="*"):
        return glob.glob(os.path.join(self._tmp_base, f"rpa_chrome_cod_{self._cod}_*{pattern_suffix}"))

    def _prune_stale_tmp_dirs(self, max_age_minutes: int = 180):
        try:
            with open(self._gc_lockfile, "a+") as lf:
                try:
                    import fcntl
                    fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except Exception:
                    return
                cutoff = time.time() - (max_age_minutes * 60)
                for path in self._glob_my_dirs("*"):
                    try:
                        if os.path.getmtime(path) < cutoff:
                            shutil.rmtree(path, ignore_errors=True)
                    except Exception:
                        pass
        except Exception:
            pass

    def _cleanup(self):
        try:
            if self._driver:
                try: self._driver.quit()
                except: pass
        finally:
            self._driver = None
            try:
                if self._rpa_tmp_dir and os.path.isdir(self._rpa_tmp_dir):
                    shutil.rmtree(self._rpa_tmp_dir, ignore_errors=True)
            except: pass
            self._rpa_tmp_dir = None
            self._prune_stale_tmp_dirs(max_age_minutes=180)

    def _build_options(self, user_data_dir: str|None, cache_dir: str|None):
        options = Options()
        if platform.system() == "Linux":
            options.binary_location = "/usr/bin/google-chrome"
            options.add_argument('--headless=new')  # ative se quiser
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-insecure-localhost')
            options.add_argument('--disable-extensions')
            options.page_load_strategy = 'eager'

        if user_data_dir:
            options.add_argument(f'--user-data-dir={user_data_dir}')
        if cache_dir:
            options.add_argument(f'--disk-cache-dir={cache_dir}')

        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        # REMOVIDO: --remote-debugging-port (evita corrida de porta)
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        prefs = {
            "download.default_directory": self._DIRETORIO_ARQUIVO,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.automatic_downloads": 1,
        }
        options.add_experimental_option("prefs", prefs)
        return options

    def _start_chrome(self, options):
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        # jitter pra reduzir colisão de inicialização simultânea
        time.sleep(random.uniform(0.05, 0.25))
        drv = webdriver.Chrome(service=service, options=options)
        try:
            drv.execute_cdp_cmd("Page.setDownloadBehavior", {
                "behavior": "allow", "downloadPath": str(self._DIRETORIO_ARQUIVO)
            })
        except Exception:
            pass
        drv.delete_all_cookies()
        drv.implicitly_wait(10)
        drv.set_page_load_timeout(60)
        return drv

    def Open(self) -> webdriver.Chrome:
        base = self._mk_fresh_tmp()
        self._rpa_tmp_dir = base
        user_data_dir = os.path.join(base, "profile")
        cache_dir = os.path.join(base, "cache")
        os.makedirs(user_data_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(self._DIRETORIO_ARQUIVO, exist_ok=True)

        print(f"[Chrome] cod={self._cod} user_data_dir={user_data_dir}")

        options = self._build_options(user_data_dir, cache_dir)

        try:
            self._driver = self._start_chrome(options)
            atexit.register(self._cleanup)
            return self._driver
        except Exception as e:
            msg = str(e).lower()
            self._cleanup()
            if "user data directory is already in use" in msg:
                # fallback 1x sem user-data-dir
                try:
                    print("[Chrome] Retry sem --user-data-dir (fallback Docker).")
                    options2 = self._build_options(user_data_dir=None, cache_dir=None)
                    self._driver = self._start_chrome(options2)
                    atexit.register(self._cleanup)
                    return self._driver
                except Exception as e2:
                    self._cleanup()
                    raise RuntimeError(f"Falha ao iniciar ChromeDriver (cod={self._cod}) após fallback: {e2}") from e2
            raise RuntimeError(f"Falha ao iniciar ChromeDriver (cod={self._cod}): {e}") from e

    def fechar(self): self._cleanup()
    def reiniciar(self) -> webdriver.Chrome:
        self._cleanup()
        return self.Open()
    def obter_navegador(self) -> webdriver.Chrome:
        if not self._driver:
            return self.Open()
        return self._driver


'''



DOCKERFILE_CONTENT = """
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

# Dependências do sistema + libs do Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    xdg-utils \
    tzdata \
    # libs gráficas/áudio usadas pelo Chrome
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    libgbm1 \
    libxshmfence1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxtst6 \
    libgtk-3-0 \
    libdrm2 \
    libxcb-dri3-0 \
    libgdk-pixbuf-2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Repositório oficial do Google Chrome (com keyring moderno) --DESCOMENTE CASO SEU PROJETO USE AUTOMAÇÃO DE NAVEGADOR
# RUN mkdir -p /etc/apt/keyrings && \
#     curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-linux.gpg && \
#     echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-linux.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
#       > /etc/apt/sources.list.d/google-chrome.list && \
#     apt-get update && apt-get install -y --no-install-recommends \
#       google-chrome-stable \
#       && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar e instalar requirements primeiro pra cachear melhor
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do projeto
COPY . .

CMD ["python3", "main.py"]


# docker build --no-cache -t nome_da_imagem .
# docker run -d -p 3000:3000 --name meu_container nome_da_imagem

"""

GITIGNORE_CONTENT = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
#   For a library or package, you might want to ignore these files since the code is
#   intended to run in multiple environments; otherwise, check them in:
# .python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# UV
#   Similar to Pipfile.lock, it is generally recommended to include uv.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#uv.lock

# poetry
#   Similar to Pipfile.lock, it is generally recommended to include poetry.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#   https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control
#poetry.lock

# pdm
#   Similar to Pipfile.lock, it is generally recommended to include pdm.lock in version control.
#pdm.lock
#   pdm stores project-wide configurations in .pdm.toml, but it is recommended to not include it
#   in version control.
#   https://pdm.fming.dev/latest/usage/project/#working-with-version-control
.pdm.toml
.pdm-python
.pdm-build/

# PEP 582; used by e.g. github.com/David-OConnor/pyflow and github.com/pdm-project/pdm
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
.wvenv
wvenv/
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
#  JetBrains specific template is maintained in a separate JetBrains.gitignore that can
#  be found at https://github.com/github/gitignore/blob/main/Global/JetBrains.gitignore
#  and can be added to the global gitignore or merged into this file.  For a more nuclear
#  option (not recommended) you can uncomment the following to ignore the entire idea folder.
#.idea/

# Ruff stuff:
.ruff_cache/

# PyPI configuration file
.pypirc

"""

DOCKERIGNORE_CONTENT = """
# Ignore o ambiente virtual
venv/
.venv/
ENV/
env/
env.bak/
venv.bak/

# Ignore arquivos Python compilados
__pycache__/
*.py[cod]
*$py.class

# Ignore arquivos de log
*.log
logs/

# Ignore arquivos e diretórios de testes
tests/
.pytest_cache/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/

                
# Ignore dependências temporárias
*.egg-info/
.eggs/
dist/
build/
*.egg
pip-log.txt
pip-delete-this-directory.txt

# Ignore cache e lixo
*.DS_Store
*.swp
*.bak
*.tmp

# Ignore documentação gerada
docs/_build/

# Ignore arquivos de IDEs
.idea/
.vscode/
*.code-workspace

# Jupyter Notebooks
.ipynb_checkpoints/

# Arquivos de controle de versionamento que não devem ir pro container
.git/
.gitignore
.dockerignore
"""