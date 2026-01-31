import pytest
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestIntegration:
    """Testes de integração para a biblioteca rpa-arc."""

    def setup_method(self):
        """Configuração antes de cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)

    def teardown_method(self):
        """Limpeza após cada teste."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_integration_completa(self):
        """Testa integração completa da CLI."""
        # Arrange
        nome_projeto = "projeto-teste-integracao"
        caminho_projeto = self.test_dir / nome_projeto
        
        # Act
        with patch('sys.argv', ['rpa-arc', nome_projeto]):
            with patch('rpa_arc.cli.Path.cwd', return_value=self.test_dir):
                from rpa_arc.cli import main
                main()
        
        # Assert
        assert caminho_projeto.exists(), "Projeto não foi criado"
        assert (caminho_projeto / "src").exists(), "Diretório src não foi criado"
        assert (caminho_projeto / "requirements.txt").exists(), "requirements.txt não foi criado"

    def test_estrutura_integration_completa(self):
        """Testa integração completa da criação de estrutura."""
        # Act
        from rpa_arc.estrutura import criar_estrutura
        criar_estrutura(self.test_dir)
        
        # Assert - Verifica estrutura completa
        estrutura_esperada = {
            "src": {
                "app": ["app.py"],
                "core": ["logger.py", "driver.py"],
                "api": ["Api.py"],
                "integracoes": [],
                "utils": []
            },
            "config": [],
            "dados": [],
            "logs": [],
            "tests": [],
            "root_files": [
                "requirements.txt", ".env", "Dockerfile", "README.md",
                "main.py", ".gitignore", ".dockerignore"
            ]
        }
        
        # Verifica diretórios
        for diretorio in ["config", "dados", "logs", "tests", "src"]:
            assert (self.test_dir / diretorio).exists(), f"Diretório {diretorio} não criado"
        
        # Verifica subdiretórios de src
        src_path = self.test_dir / "src"
        for subdir in ["app", "core", "integracoes", "utils", "api"]:
            assert (src_path / subdir).exists(), f"Subdiretorio {subdir} não criado"
        
        # Verifica arquivos principais
        for arquivo in estrutura_esperada["root_files"]:
            assert (self.test_dir / arquivo).exists(), f"Arquivo {arquivo} não criado"
        
        # Verifica arquivos específicos
        assert (src_path / "core" / "logger.py").exists()
        assert (src_path / "core" / "driver.py").exists()
        assert (src_path / "api" / "Api.py").exists()

    def test_conteudos_integration(self):
        """Testa se os conteúdos são aplicados corretamente."""
        # Act
        from rpa_arc.estrutura import criar_estrutura
        criar_estrutura(self.test_dir)
        
        # Assert - Verifica conteúdos específicos
        requirements_path = self.test_dir / "requirements.txt"
        requirements_content = requirements_path.read_text(encoding='utf-8')
        
        # Verifica dependências no requirements.txt
        dependencias = ["requests", "python-dotenv", "selenium", "webdriver-manager"]
        for dep in dependencias:
            assert dep in requirements_content, f"Dependência {dep} não encontrada"
        
        # Verifica conteúdo do logger.py
        logger_path = self.test_dir / "src" / "core" / "logger.py"
        logger_content = logger_path.read_text(encoding='utf-8')
        assert "class Logger:" in logger_content
        assert "class DailyFileHandler" in logger_content
        
        # Verifica conteúdo do driver.py
        driver_path = self.test_dir / "src" / "core" / "driver.py"
        driver_content = driver_path.read_text(encoding='utf-8')
        assert "class GerenciadorNavegador:" in driver_content
        assert "selenium" in driver_content
        
        # Verifica conteúdo do Api.py
        api_path = self.test_dir / "src" / "api" / "Api.py"
        api_content = api_path.read_text(encoding='utf-8')
        assert "class Api:" in api_content
        assert "requests" in api_content

    @pytest.mark.parametrize("nome_entrada,nome_esperado", [
        ("projeto-simples", "projeto-simples"),
        ("projeto/com/subpastas", "projeto/com/subpastas"),
        ("projeto_com_underscores", "projeto_com_underscores"),
        ("123-projeto-numerico", "123-projeto-numerico"),
    ])
    def test_cli_argumentos_variados(self, nome_entrada, nome_esperado):
        """Testa CLI com diferentes tipos de argumentos."""
        # Arrange
        caminho_esperado = self.test_dir / nome_esperado

        # Act
        with patch('sys.argv', ['rpa-arc', nome_entrada]):
            with patch('rpa_arc.cli.Path.cwd', return_value=self.test_dir):
                with patch('rpa_arc.cli.criar_estrutura') as mock_criar:
                    from rpa_arc.cli import main
                    main()

        # Assert
        mock_criar.assert_called_once_with(caminho_esperado, minimal=False, force=False)

    def test_estrutura_permissoes_arquivos(self):
        """Testa se os arquivos criados têm permissões corretas."""
        # Act
        from rpa_arc.estrutura import criar_estrutura
        criar_estrutura(self.test_dir)
        
        # Assert - Verifica se arquivos são legíveis
        arquivos_teste = [
            self.test_dir / "requirements.txt",
            self.test_dir / "src" / "core" / "logger.py",
            self.test_dir / "src" / "core" / "driver.py",
            self.test_dir / "src" / "api" / "Api.py"
        ]
        
        for arquivo in arquivos_teste:
            assert arquivo.exists(), f"Arquivo {arquivo} não existe"
            # Verifica se é possível ler
            try:
                conteudo = arquivo.read_text(encoding='utf-8')
                assert len(conteudo) > 0, f"Arquivo {arquivo} está vazio"
            except Exception as e:
                pytest.fail(f"Não foi possível ler {arquivo}: {e}")

    def test_estrutura_encoding_utf8(self):
        """Testa se todos os arquivos são criados com encoding UTF-8."""
        # Act
        from rpa_arc.estrutura import criar_estrutura
        criar_estrutura(self.test_dir)
        
        # Assert - Verifica encoding de arquivos importantes
        arquivos_teste = [
            self.test_dir / "requirements.txt",
            self.test_dir / "src" / "core" / "logger.py",
            self.test_dir / "src" / "api" / "Api.py"
        ]
        
        for arquivo in arquivos_teste:
            try:
                # Tenta ler com UTF-8
                conteudo = arquivo.read_text(encoding='utf-8')
                # Verifica se não há caracteres inválidos
                conteudo.encode('utf-8')
            except UnicodeDecodeError:
                pytest.fail(f"Arquivo {arquivo} não está em UTF-8")
            except UnicodeEncodeError:
                pytest.fail(f"Arquivo {arquivo} contém caracteres inválidos")

    def test_cli_mensagens_usuario(self):
        """Testa se as mensagens para o usuário são exibidas corretamente."""
        # Arrange
        nome_projeto = "projeto-mensagens"
        
        # Act
        with patch('sys.argv', ['rpa-arc', nome_projeto]):
            with patch('rpa_arc.cli.Path.cwd', return_value=self.test_dir):
                with patch('builtins.print') as mock_print:
                    with patch('rpa_arc.estrutura.criar_estrutura'):
                        from rpa_arc.cli import main
                        main()
        
        # Assert - Verifica mensagens de sucesso
        calls_str = str(mock_print.call_args_list)
        assert f"Projeto '{nome_projeto}' criado com sucesso" in calls_str
        assert "Local:" in calls_str
        assert "projeto-mensagens" in calls_str

    def test_estrutura_conteudo_especifico(self):
        """Testa conteúdo específico de arquivos importantes."""
        # Act
        from rpa_arc.estrutura import criar_estrutura
        criar_estrutura(self.test_dir)
        
        # Assert - Verifica conteúdo específico
        # Dockerfile deve ter FROM python:3.12-slim
        dockerfile_path = self.test_dir / "Dockerfile"
        dockerfile_content = dockerfile_path.read_text(encoding='utf-8')
        assert "FROM python:3.12-slim" in dockerfile_content
        
        # .gitignore deve ter padrões Python
        gitignore_path = self.test_dir / ".gitignore"
        gitignore_content = gitignore_path.read_text(encoding='utf-8')
        assert "__pycache__/" in gitignore_content
        assert "*.py[cod]" in gitignore_content
        
        # requirements.txt deve ter dependências específicas
        requirements_path = self.test_dir / "requirements.txt"
        requirements_content = requirements_path.read_text(encoding='utf-8')
        assert "requests" in requirements_content
        assert "selenium" in requirements_content

    def test_cli_tratamento_erros(self):
        """Testa tratamento de erros na CLI."""
        # Teste: pasta já existe
        nome_projeto = "pasta-existente"
        pasta_existente = self.test_dir / nome_projeto
        pasta_existente.mkdir(parents=True)
        
        with patch('sys.argv', ['rpa-arc', nome_projeto]):
            with patch('rpa_arc.cli.Path.cwd', return_value=self.test_dir):
                with patch('builtins.print') as mock_print:
                    from rpa_arc.cli import main
                    main()
        
        # Verifica mensagem de erro (menciona --force)
        assert any(
            "já existe" in str(call) and "--force" in str(call)
            for call in mock_print.call_args_list
        ), "Mensagem sobre pasta existente e --force não encontrada"

    def test_estrutura_recriacao_segura(self):
        """Testa se a estrutura pode ser recriada sem erros."""
        # Act - Cria estrutura duas vezes
        from rpa_arc.estrutura import criar_estrutura
        
        # Primeira criação
        criar_estrutura(self.test_dir)
        
        # Segunda criação (deve funcionar sem erro)
        try:
            criar_estrutura(self.test_dir)
        except Exception as e:
            pytest.fail(f"Recriação da estrutura falhou: {e}")
        
        # Assert - Verifica se estrutura ainda está intacta
        assert (self.test_dir / "src").exists()
        assert (self.test_dir / "config").exists()
        assert (self.test_dir / "requirements.txt").exists() 