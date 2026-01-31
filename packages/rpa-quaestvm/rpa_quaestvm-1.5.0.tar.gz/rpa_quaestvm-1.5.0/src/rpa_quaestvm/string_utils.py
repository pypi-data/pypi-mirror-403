import re


# extrair o número da loja do nome_local (Loja 1 -> 1)
def get_loja_local(nome_local: str):
    try:
        return int(re.search(r'(\d+)', nome_local, flags=re.IGNORECASE).group(1))
    except AttributeError:
        raise ValueError(f"Erro: Não foi possível extrair o número da loja do nome_local '{nome_local}'")
    
def remove_non_numbers(input_string):
    return str(int(re.sub(r'\D', '', input_string)))