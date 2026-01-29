"""
Funções
nov.22
"""

from datetime import datetime

import pandas as pd

from .paths import data_path


def update_table() -> pd.DataFrame:
    """
    Atualiza a tabela de valores da UFESP fazendo scraping do site oficial da SEFAZ-SP.

    Esta função busca os dados mais recentes no site da Secretaria da Fazenda do Estado
    de São Paulo, processa os dados (conversões de tipo, limpeza de caracteres especiais,
    parsing de datas) e substitui completamente o arquivo CSV existente com os novos dados.

    :return: DataFrame com os dados atualizados da UFESP
    :rtype: pandas.DataFrame
    :raises ValueError: Se não for possível extrair a tabela do HTML
    :raises Exception: Para erros de conexão, parsing ou escrita do arquivo

    .. note::
       Esta função sempre faz uma requisição ao site da SEFAZ-SP, independente
       da última atualização. Use com moderação para evitar sobrecarga no servidor.

    Example::
        >>> df = update_table()
        >>> print(df.tail())
    """

    # URL do site oficial da SEFAZ-SP
    URL = 'https://legislacao.fazenda.sp.gov.br/Paginas/ValoresDaUFESP.aspx'

    try:
        # Extrai tabelas HTML da página
        dfs = pd.read_html(io=URL)

        if len(dfs) < 4:
            raise ValueError(
                f'Esperado pelo menos 4 tabelas no HTML, encontrado {len(dfs)}'
            )

        # Seleciona a quarta tabela (índice 3) que contém os dados da UFESP
        df = dfs[3]

        # Processa coluna de valores
        df['VALOR EM R$'] = df['VALOR EM R$'].replace(',', '', regex=True)
        df['VALOR EM R$'] = df['VALOR EM R$'].replace('\u200b', '', regex=True)
        df['VALOR EM R$'] = df['VALOR EM R$'].astype(float)
        df['VALOR EM R$'] = df['VALOR EM R$'] / 100

        # Processa coluna de período
        df['PERÍODO'] = df['PERÍODO'].replace('de ', '', regex=True)
        df['PERÍODO'] = df['PERÍODO'].replace(' a ', ' A ', regex=True)
        df['PERÍODO'] = df['PERÍODO'].replace('\u200b', '', regex=True)
        df['PERÍODO'] = df['PERÍODO'].replace('\xa0', ' ', regex=True)

        # Separa data de início e fim
        df[['data_inicio', 'data_fim']] = df['PERÍODO'].str.split(
            pat='A',
            n=1,
            expand=True,
        )

        # Ajusta Data do Início
        df['data_inicio'] = df.loc[:, 'data_inicio'].str.strip()
        df['data_inicio'] = pd.to_datetime(df['data_inicio'], format='%d/%m/%Y')

        # Ajusta Data do Fim
        df['data_fim'] = df.loc[:, 'data_fim'].str.strip()
        df['data_fim'] = pd.to_datetime(df['data_fim'], format='%d/%m/%Y')

        # Cria coluna ano_mes
        df.loc[:, 'ano_mes'] = pd.to_datetime(df['data_inicio']).dt.to_period(
            'M'
        )

        # Processa coluna base legal
        df['BASE LEGAL'] = df['BASE LEGAL'].replace('\u200b', '', regex=True)
        df['BASE LEGAL'] = df['BASE LEGAL'].replace('\xa0', ' ', regex=True)
        df['BASE LEGAL'] = df['BASE LEGAL'].replace(
            '88/ 25', '88/25', regex=True
        )
        df['base_legal'] = df.loc[:, 'BASE LEGAL'].str.strip()

        # Renomeia coluna de valor
        df = df.rename(
            {'VALOR EM R$': 'valor'},
            axis=1,
            inplace=False,
        )

        # Seleciona apenas as colunas necessárias
        df = df[
            [
                'data_inicio',
                'data_fim',
                'ano_mes',
                'valor',
                'base_legal',
            ]
        ].copy()

        # Valida que o DataFrame não está vazio
        if df.empty:
            raise ValueError(
                'DataFrame resultante está vazio após processamento'
            )

        # Salva o arquivo CSV (substitui completamente o arquivo existente)
        df.to_csv(
            data_path / 'ufesp.csv',
            index=False,
            decimal=',',
        )

        return df

    except Exception as e:
        raise Exception(f'Erro ao atualizar tabela UFESP: {str(e)}') from e


def get_table() -> pd.DataFrame:
    """
    Carrega a tabela completa de valores históricos da UFESP do arquivo CSV local.

    Esta função lê o arquivo CSV armazenado localmente contendo todos os valores históricos
    da UFESP, realizando o parse automático das colunas de data para datetime.

    :return: DataFrame contendo os valores históricos da UFESP com as colunas:
             'data_inicio', 'data_fim', 'ano_mes', 'valor' e 'base_legal'
    :rtype: pandas.DataFrame

    Example::
        >>> df = get_table()
        >>> print(df.head())
        >>> print(df.info())
    """

    return pd.read_csv(
        data_path / 'ufesp.csv',
        parse_dates=['data_inicio', 'data_fim'],
        decimal=',',
    )


def get_ufesp_from_date(date: datetime | str):
    """
    Obtém o valor da UFESP para uma determinada data.

    Busca na tabela de valores da UFESP o registro que corresponde à data especificada.
    Se a data não estiver nos dados carregados, a função automaticamente atualiza a tabela
    consultando o site oficial da SEFAZ-SP.

    :param date: Data para a qual se deseja obter o valor da UFESP
    :type date: datetime.datetime or str
    :return: Dicionário contendo os dados da UFESP para a data especificada, com as chaves:
             'data_inicio', 'data_fim', 'ano_mes', 'valor' e 'base_legal'
    :rtype: dict
    :raises ValueError: Se a data não for encontrada nos dados disponíveis, mesmo após atualização

    .. note::
       A data deve estar dentro de um período válido (entre data_inicio e data_fim) de um
       registro da tabela UFESP.

    Example::
        >>> # Com string no formato YYYY-MM-DD
        >>> dados = get_ufesp_from_date('2021-11-15')
        >>> print(dados['valor'])

        >>> # Com objeto datetime
        >>> from datetime import datetime
        >>> data = datetime(2021, 11, 15)
        >>> dados = get_ufesp_from_date(data)
        >>> print(dados['base_legal'])
    """
    # Get Dataframe
    df = get_table()

    # Converte date para datetime se necessário
    if isinstance(date, str):
        date = pd.to_datetime(date)

    # Verifica se a data está fora do intervalo disponível
    min_date = df['data_inicio'].min()
    max_date = df['data_fim'].max()

    if date < min_date or date > max_date:
        # Update
        update_table()

        # Recarrega após atualização
        df = get_table()

    # Json
    mask = (df['data_inicio'] <= date) & (df['data_fim'] >= date)
    results = df.loc[mask].to_dict('records')

    if not results:
        raise ValueError(
            f'Data {date.date()} não encontrada nos dados disponíveis. '
            f'Intervalo disponível: {df["data_inicio"].min().date()} a {df["data_fim"].max().date()}'
        )

    return results[0]


def get_ufesp_from_year(year):
    """
    Obtém o valor da UFESP para um determinado ano.

    Busca na tabela de valores da UFESP o registro que corresponde ao ano especificado.
    Se o ano não estiver nos dados carregados, a função automaticamente atualiza a tabela
    consultando o site oficial da SEFAZ-SP.

    :param year: Ano para o qual se deseja obter o valor da UFESP
    :type year: int or str
    :return: Dicionário contendo os dados da UFESP para o ano especificado, com as chaves:
             'data_inicio', 'data_fim', 'ano_mes', 'valor' e 'base_legal'
    :rtype: dict
    :raises ValueError: Se o ano não for encontrado nos dados disponíveis, mesmo após atualização

    Example::
        >>> dados_2021 = get_ufesp_from_year(2021)
        >>> print(dados_2021['valor'])

        >>> # Também aceita string
        >>> dados_2022 = get_ufesp_from_year('2022')
    """
    # Adjust Year
    year = int(year)

    # Get Dataframe
    df = get_table()

    # Create Year Columns
    df['data_inicio_year'] = pd.DatetimeIndex(df['data_inicio']).year
    df['data_fim_year'] = pd.DatetimeIndex(df['data_fim']).year

    # Verifica se o ano está fora do intervalo disponível
    min_year = df['data_inicio_year'].min()
    max_year = df['data_fim_year'].max()

    if year < min_year or year > max_year:
        # Update
        update_table()

        # Recarrega após atualização
        df = get_table()

        # Recria as colunas de ano
        df['data_inicio_year'] = pd.DatetimeIndex(df['data_inicio']).year
        df['data_fim_year'] = pd.DatetimeIndex(df['data_fim']).year

    # Json
    mask = (df['data_inicio_year'] <= year) & (df['data_fim_year'] >= year)
    results = df.loc[mask].to_dict('records')

    if not results:
        raise ValueError(
            f'Ano {year} não encontrado nos dados disponíveis. '
            f'Intervalo disponível: {df["data_inicio_year"].min()} a {df["data_fim_year"].max()}'
        )

    return results[0]
