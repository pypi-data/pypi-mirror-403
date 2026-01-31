import re
def remove_think_blocks(text):
    # Elimina todo lo que esté entre <think> y </think>, incluyendo las etiquetas
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)


def clean_response(text: str, user_name: str, influencer_name: str) -> str:
    text = text.strip()   

    # 0. Normalizar comillas curvas
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")

    # 1. Reemplazar comillas dobles duplicadas
    text = text.replace('""', '"')

    # 2. Eliminar el nombre del speaker al inicio (incluso si va seguido directamente de comilla sin espacio)
    #print("TEXT CHARACTERS:", [(i, c, f"{ord(c):04X}") for i, c in enumerate(text)])
    pattern = rf'^\s*["\']?\s*({re.escape(user_name)}|{re.escape(influencer_name)})\s*:\s*["\']?'
    text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()

    # 3. Eliminar comillas externas rectas simples o dobles si quedan
    if text.startswith('"') or text.startswith("'"):
        text = text[1:].strip()
    if text.endswith('"') or text.endswith("'"):
        text = text[:-1].strip()
    #print("TEXT CHARACTERS2:", [(i, c, f"{ord(c):04X}") for i, c in enumerate(text)])
    return text