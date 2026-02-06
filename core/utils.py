#!/usr/bin/env python3
"""
Utilitários - Core
Gerador de Iniciais Arbitrais

Funções utilitárias para formatação de dados.
"""

import re
from datetime import date
from typing import Any, List


def formatar_cpf(cpf: str) -> str:
    """
    Formata CPF para XXX.XXX.XXX-XX

    Args:
        cpf: CPF em qualquer formato

    Returns:
        CPF formatado ou string original se inválido
    """
    if not cpf:
        return ""
    numeros = re.sub(r'\D', '', str(cpf))
    if len(numeros) == 11:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    return cpf


def formatar_telefone(telefone: str) -> str:
    """
    Formata telefone para (XX) XXXXX-XXXX

    Args:
        telefone: Telefone em qualquer formato

    Returns:
        Telefone formatado ou string original se inválido
    """
    if not telefone:
        return ""
    # Remove tudo que não é número (incluindo decimal)
    numeros = re.sub(r'\D', '', str(telefone).split('.')[0])
    # Remove código do país
    if numeros.startswith('55') and len(numeros) > 11:
        numeros = numeros[2:]
    if len(numeros) == 11:
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
    elif len(numeros) == 10:
        return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
    elif len(numeros) >= 8:
        # Assume DDD 11 se não tiver
        return f"(11) {numeros[-5:-4]}{numeros[-4:]}"
    return telefone


def formatar_valor(valor: float) -> str:
    """
    Formata valor para R$ X.XXX,XX

    Args:
        valor: Valor numérico

    Returns:
        Valor formatado em reais
    """
    return f"R${valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def valor_por_extenso(valor: float) -> str:
    """
    Converte valor para extenso em português

    Args:
        valor: Valor numérico

    Returns:
        Valor por extenso
    """
    if valor == 0:
        return "zero reais"

    unidades = ['', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove']
    especiais = ['dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove']
    dezenas = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
    centenas = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos', 'oitocentos', 'novecentos']

    def _extenso_ate_999(n):
        if n == 0:
            return ''
        if n == 100:
            return 'cem'

        resultado = []
        if n >= 100:
            resultado.append(centenas[n // 100])
            n = n % 100
        if n >= 20:
            resultado.append(dezenas[n // 10])
            if n % 10 > 0:
                resultado.append(unidades[n % 10])
        elif n >= 10:
            resultado.append(especiais[n - 10])
        elif n > 0:
            resultado.append(unidades[n])

        return ' e '.join([r for r in resultado if r])

    valor = round(valor, 2)
    inteiro = int(valor)
    centavos = int(round((valor - inteiro) * 100))

    resultado = []

    if inteiro >= 1000000:
        milhoes = inteiro // 1000000
        if milhoes == 1:
            resultado.append("um milhão")
        else:
            resultado.append(f"{_extenso_ate_999(milhoes)} milhões")
        inteiro = inteiro % 1000000

    if inteiro >= 1000:
        milhares = inteiro // 1000
        if milhares == 1:
            resultado.append("mil")
        else:
            resultado.append(f"{_extenso_ate_999(milhares)} mil")
        inteiro = inteiro % 1000

    if inteiro > 0:
        resultado.append(_extenso_ate_999(inteiro))

    texto = ' e '.join([r for r in resultado if r])

    if int(round(valor, 2)) == 1:
        texto += " real"
    elif int(round(valor, 2)) > 0:
        texto += " reais"

    if centavos > 0:
        if texto:
            texto += " e "
        texto += _extenso_ate_999(centavos)
        texto += " centavo" if centavos == 1 else " centavos"

    return texto if texto else "zero reais"


def formatar_data(dt: date = None) -> str:
    """
    Formata data para 'DD de mês de AAAA'

    Args:
        dt: Data a formatar (usa data atual se None)

    Returns:
        Data formatada
    """
    if dt is None:
        dt = date.today()
    meses = ['', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
             'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    return f"{dt.day} de {meses[dt.month]} de {dt.year}"


def limpar_texto(texto: Any) -> str:
    """
    Limpa e converte texto para string

    Args:
        texto: Texto a limpar

    Returns:
        Texto limpo
    """
    import pandas as pd
    if pd.isna(texto) or texto is None:
        return ""
    return str(texto).strip()


def separar_valores(texto: str, separadores: str = r'[,;|]') -> List[str]:
    """
    Separa múltiplos valores em uma string

    Args:
        texto: Texto com múltiplos valores
        separadores: Padrão regex de separadores

    Returns:
        Lista de valores separados
    """
    if not texto:
        return []
    partes = re.split(separadores, texto)
    return [p.strip() for p in partes if p.strip()]
