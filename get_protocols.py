import re
import os
import scrapy
from tesouro_direto import response_handlers as TD
from util import as_json


BASE_URL = 'https://portalinvestidor.tesourodireto.com.br'
USER = os.environ["PORTAL_INVESTIDOR_USER"]
PASS = os.environ["PORTAL_INVESTIDOR_PASS"]


class PortalInvestidorSpider(scrapy.Spider):
    name = 'portalinvestidor'
    start_urls = [BASE_URL]

    def parse(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={'UserCpf': USER, 'UserPassword': PASS},
            callback=self.after_login
        )

    @TD.with_headers
    def after_login(self, response, headers):
        if TD.authentication_failed(response):
            self.logger.error("Login failed")
            return

        data = {
            'Operacao': '1',
            'InstituicaoFinanceira': "386",
            'DataInicial': '',
            'DataFinal': ''
        }

        yield scrapy.http.JsonRequest(
            url=BASE_URL + "/Consulta/ConsultarOperacoes",
            method='POST',
            headers=headers,
            data=data,
            callback=self.getProtocolList
        )

    @as_json
    def getProtocolList(self, jsonResponse):
        protocols = jsonResponse['Operacoes']
        pass