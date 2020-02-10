import re
import os
import scrapy
from tesouro_direto import response_handlers as TD
from util import asJson


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

    def after_login(self, response):
        if TD.authentication_failed(response):
            self.logger.error("Login failed")
            return

        headers = dict()
        token = response.css('#__AjaxAntiForgeryForm input')[0].attrib['value']
        tokenName = response.css('#__AjaxAntiForgeryForm input')[0].attrib['name']
        headers[tokenName] = token

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

    @asJson
    def getProtocolList(self, jsonResponse):
        protocols = jsonResponse['Operacoes']
        pass