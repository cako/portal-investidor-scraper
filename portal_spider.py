"""
Scrapes Portal Investidor to find all transactions of Tesouro Direto.
REQUIRES A LIST OF PROTOCOLS TO RUN:

    1. Navegue a https://portalinvestidor.tesourodireto.com.br/Consulta
    2. Preencha os Filtros e clique em Aplicar
    3. Vá até a transação mais antiga, no FIM da lista
    4. Abaixo de todos os ítens à direita, clique e segure o mouse
    5. Segurando o clique, mova o mouse para cima, até ele ficar no espaço em
       branco logo acima e ligeiramente à esquerda do primeiro "Investimento".
       Você deve ter todo o texto somente das operações selecionado.
    7. Copie e cole em um editor de texto.
    8. Cada ítem deve ser algo assim:
        Investimento
        03/01/2020
        Nº de protocolo - XXXXXXXX

        CORRETORA XXXX
        Status
        REALIZADO

        VER DETALHES
    9. Salve o arquivo e edite a varíavel logo abaixo para apontar para ele
"""
OPS_FILE = ""

import re
import os
import scrapy
from bs4 import BeautifulSoup

BASE_URL = 'https://portalinvestidor.tesourodireto.com.br'
USER = os.environ["PORTAL_INVESTIDOR_USER"]
PASS = os.environ["PORTAL_INVESTIDOR_PASS"]

REMOTE_PROTOCOLS = []
ALL_PROTOCOLS = []
with open(OPS_FILE, "r") as f:
    for line in f:
        line = line.split(' - ')
        if len(line) > 1:
            line = re.search(r'^\d+', line[1])
            if line:
                ALL_PROTOCOLS.append(line.group())


def authentication_failed(response):
    """ Verifica se login falhou """
    pass
    # soup = BeautifulSoup(response.body, 'html.parser')
    # if soup(text=re.compile('Valor líquido total')):
        # return True
    # return False


class PortalInvestidorSpider(scrapy.Spider):
    """
        Spider which crawls Portal Investidor to find all Tesouro Direto \
        transactions
    """
    name = 'portalinvestidor'
    start_urls = [BASE_URL]

    def parse(self, response):
        for pid in ALL_PROTOCOLS:
            filename = 'td/%s.html' % pid
            if os.path.isfile(filename):
                self.log("Achamos cópia local do protocolo %s" % pid)
                url = r"file://" + os.path.abspath(filename)
                yield scrapy.Request(url=url, callback=self.parse_protocolo)
            else:
                REMOTE_PROTOCOLS.append(pid)
        if REMOTE_PROTOCOLS:
            print("Buscando protocolos remotos")
            yield scrapy.FormRequest.from_response(
                response,
                formdata={'UserCpf': USER, 'UserPassword': PASS},
                callback=self.after_login
            )
        else:
            self.log("Todos protocolos têm cópia local")

    def after_login(self, response):
        if authentication_failed(response):
            self.logger.error("Login failed")
            return

        for pid in REMOTE_PROTOCOLS:
            url = "%s/Protocolo/%s/1" % (BASE_URL, pid)
            self.log("Buscando protocolo remoto %s" % pid)
            yield scrapy.Request(url=url, callback=self.parse_protocolo)

    def parse_protocolo(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        pid = soup.find("span", {"class": "td-protocolo-numero"}).text.strip()
        filename = 'td/%s.html' % pid
        if not os.path.exists(filename):
            with open(filename, 'wb') as f:
                f.write(response.body)
            self.log('Arquivo salvo: %s' % filename)
        info = {'protocolo': int(pid)}
        psoup = soup.find_all("p", {"class": "td-protocolo-info-base"})
        for item in psoup:
            key = item.find(text=True, recursive=False).strip()
            info[key] = item.find("span").get_text().strip()

        psoup = soup.find_all("h3", {"class": "td-protocolo-info-titulo"})
        if len(psoup) > 1:
            self.log("CUIDADO: Mais de um título presente")
        info["Título"] = psoup[0].text.strip()

        psoup = soup.find_all("p", {"class": "td-protocolo-info"})
        for item in psoup:
            key = item.find(text=True, recursive=False).strip()
            info[key] = item.find("span").get_text().strip()

        item = soup.find("p", {"class": "td-pedido-valor-total"})
        key = item.find(text=True, recursive=False).strip()
        info[key] = item.find("span").get_text().strip()
        self.log(info)
        yield info
