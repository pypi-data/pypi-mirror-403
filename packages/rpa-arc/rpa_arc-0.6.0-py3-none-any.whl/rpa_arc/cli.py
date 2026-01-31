import argparse
from pathlib import Path
from rpa_arc.estrutura import criar_estrutura


def main() -> None:
    parser = argparse.ArgumentParser(
        description="🚀 Cria a estrutura base de um projeto RPA em Python."
    )
    parser.add_argument(
        "nome_projeto",
        nargs="?",
        default=None,
        type=str,
        help="(opcional) Nome da pasta onde o projeto será criado",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Permite usar pasta existente; apenas arquivos faltantes são criados (não sobrescreve).",
    )
    parser.add_argument(
        "--minimal",
        "-m",
        action="store_true",
        help="Cria estrutura mínima (sem Docker, sem API, apenas core + logger + driver + main).",
    )
    args = parser.parse_args()

    # Se veio nome, cria subpasta; se não, usa o cwd
    if args.nome_projeto:
        caminho_projeto = Path.cwd() / args.nome_projeto
        if caminho_projeto.exists() and not args.force:
            print(
                f"⚠️  A pasta '{args.nome_projeto}' já existe. "
                "Use --force para adicionar apenas o que faltar."
            )
            return
        if not caminho_projeto.exists():
            caminho_projeto.mkdir(parents=True)
    else:
        caminho_projeto = Path.cwd()

    criar_estrutura(caminho_projeto, minimal=args.minimal, force=args.force)

    if args.nome_projeto:
        print(f"\n🎉 Projeto '{args.nome_projeto}' criado com sucesso!")
    else:
        print("\n🎉 Estrutura criada na raiz do projeto com sucesso!")
    print(f"📂 Local: {caminho_projeto.resolve()}")


if __name__ == "__main__":
    main()