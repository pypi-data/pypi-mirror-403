# Estrutura do Projeto

Esse tópico tem a finalidade de apresentar a estrutura do projeto facilitando eventuais contribuidores.

<br>

O **gerenciamento de pacote** é feito com o [uv](https://docs.astral.sh/uv/). Dessa forma, apos fazer um `git clone`, basta dar o comando abaixo. Os grupos `docs` e `dev` instalam também as dependências relativas a documentação (que abordaremos a seguir) e aos pacotes de desenvolvimento (grosso modo: _jupyter notebook_ para facilitar as tentativas de rodar).

```shell
uv sync --group docs --group dev
```

<br>

Uma vez com ambiente `.venv` criado, basta acessa-lo.

```shell
# Windows
.venv\Scripts\activate

# Linux
source .venv/bin/activate
```

<br>

A **documentação** é feita com o [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/), com _deploy_ no [Read The Docs](https://about.readthedocs.com/).

Para instanciar a documentação, basta dar um

```shell
mkdocs serve
```
