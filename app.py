import os
import asyncio
import PyPDF2
from flask import Flask, render_template, request, send_file
from googletrans import LANGUAGES, Translator
from googletrans.gtoken import TokenAcquirer
from httpx import AsyncClient, URL

class AsyncTranslator(Translator):
    def __init__(self, service_urls=None, user_agent=None, timeout=None):
        self.service_urls = service_urls or ['https://translate.google.com']
        self.client = AsyncClient(
            base_url=self.service_urls[0],
            timeout=timeout,
        )
        self.token_acquirer = TokenAcquirer(client=self.client)  # Pass the client argument
        self._update_params()
        self.raise_exception = True

    def _update_params(self):
        # Implement the logic for updating params here (if needed)
        pass

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

async def traduzir_texto(texto, idioma_destino='en'):
    translator = AsyncTranslator()
    traducao_coroutine = translator.translate(texto, dest=idioma_destino)
    traducao = await traducao_coroutine

    if traducao and traducao.response and traducao.response.status_code == 200:
        return traducao.text
    else:
        # Handle the error case
        return "Translation failed"

async def traduzir_e_salvar_pdf(caminho_pdf, idioma_destino='en'):
    pdf_texto = ""

    # Leitura do PDF
    with open(caminho_pdf, 'rb') as arquivo_pdf:
        leitor_pdf = PyPDF2.PdfReader(arquivo_pdf)
        num_paginas = len(leitor_pdf.pages)

        # Extração de texto de cada página
        for pagina_numero in range(num_paginas):
            pagina = leitor_pdf.pages[pagina_numero]
            pdf_texto += pagina.extract_text()

    # Tradução do texto extraído
    texto_traduzido = await traduzir_texto(pdf_texto, idioma_destino)

    # Criar um novo arquivo PDF com o texto traduzido
    caminho_arquivo_traduzido = caminho_pdf.replace('.pdf', f'_traduzido_{idioma_destino}.pdf')

    with open(caminho_arquivo_traduzido, 'w', encoding='utf-8') as novo_pdf:
        novo_pdf.write(texto_traduzido)

    return caminho_arquivo_traduzido

async def processar_traducao(caminho_arquivo_pdf, idioma_destino='en'):
    caminho_pdf_traduzido = await traduzir_e_salvar_pdf(caminho_arquivo_pdf, idioma_destino)
    return caminho_pdf_traduzido

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            caminho_arquivo_pdf = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(caminho_arquivo_pdf)

            idioma_destino = 'en'  # Idioma para o qual você deseja traduzir (pode ser alterado)
            caminho_pdf_traduzido = asyncio.run(processar_traducao(caminho_arquivo_pdf, idioma_destino))

            return send_file(caminho_pdf_traduzido, as_attachment=True)

    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)