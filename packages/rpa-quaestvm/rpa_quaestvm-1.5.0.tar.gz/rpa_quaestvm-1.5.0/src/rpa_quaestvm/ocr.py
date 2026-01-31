import easyocr

idiomas = ["en"]
class OcrReader():
    """Singleton para leitor OCR"""
    
    _instance = None

    @classmethod
    def get_reader(cls):
        if cls._instance is None:
            print('Inicializando instância do easyocr.Reader')
            cls._instance = easyocr.Reader(idiomas, gpu=False, verbose=False)
        return cls._instance

def get_reader():
    return OcrReader.get_reader()


def get_text_from_image(
    reader: easyocr.Reader, image, threshold=0.2, text_threshold=0.7
):
    # O método readtext retorna uma lista de resultados.
    # Cada resultado é uma tupla: (coordenadas_bbox, texto_reconhecido, confiança)
    resultados = reader.readtext(
        image, batch_size=5, threshold=threshold, text_threshold=text_threshold
    )
    if resultados:
        texto_completo = "".join([res[1] for res in resultados]).strip()
        return texto_completo
    return ""
