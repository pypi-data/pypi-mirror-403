# Unidade Fiscal do Estado de São Paulo (UFESP)

[![Repo](https://img.shields.io/badge/GitHub-repo-blue?logo=github&logoColor=f5f5f5)](https://github.com/michelmetran/ufesp)
[![Read the Docs](https://img.shields.io/readthedocs/ufesp?logo=ReadTheDocs&label=Read%20The%20Docs)](https://ufesp.readthedocs.io/)<br>
[![Publish Python to PyPI](https://github.com/michelmetran/ufesp/actions/workflows/publish-to-pypi-uv.yml/badge.svg)](https://github.com/michelmetran/ufesp/actions/workflows/publish-to-pypi-uv.yml)
[![PyPI](https://img.shields.io/pypi/v/ufesp?logo=pypi&label=PyPI&color=blue)](https://pypi.org/project/ufesp/)
[![PyPI Test](https://img.shields.io/pypi/v/ufesp?logo=pypi&server=test&label=PyPI%20Test&color=orange)](https://test.pypi.org/project/ufesp/)

A Unidade Fiscal do Estado de São Paulo (UFESP) é utilizada, dentre outras funções, para calcular as multas ambientais do estado de São Paulo. É definida pela Secretaria da Fazenda do Estado de São Paulo ([SEFAZ](https://portal.fazenda.sp.gov.br/)).

Com objetivo de obter os dados, para cálculos de multas, optei por utilizar o [_site_ oficial](https://legislacao.fazenda.sp.gov.br/Paginas/ValoresDaUFESP.aspx) da SEFAZ com as informações. Fiz a partir de 1997 apenas.

O repositório [ufesp](https://github.com/michelmetran/ufesp) objetivou disponibilizar os valores de UFESP de maneira facilitada, por meio de um servidor, com atualização periódica.

![Photo by [**StellrWeb**](https://unsplash.com/photos/djb1whucfBY) on [Unsplash](https://unsplash.com)](./docs/assets/stellrweb2.jpg)

<br>

---

## Como Instalar?

```python
# Instala
!pip3 install ufesp --upgrade
```

<br>

---

## Como Usar?

Para testar fiz um [Google Colab](https://colab.research.google.com/drive/1NwV9mGUlPOlYFcZ6-ieEXL4HVPShO928?usp=sharing).

Toda a documentação encontra-se em [ufesp.readthedocs.io](https://ufesp.readthedocs.io/).

```python
import ufesp

# Pega UFESP para um dado dia
ufesp.get_ufesp_from_date(date='2025-04-02')

# Pega UFESP para um dado ano
dados = ufesp.get_ufesp_from_year(year=2024)
```

<br>

Outros métodos (que poderiam ser privados).

```python
# Pega Tabela Inteira
ufesp.get_table()

# Atualiza Tabela
ufesp.update_table()
```

<br>

A partir da versão 0.0.16, com contribuição de [ubalklen](https://github.com/ubalklen), o pacote busca os dados mais recentes do _site_ da SEFAZ-SP automaticamente.
