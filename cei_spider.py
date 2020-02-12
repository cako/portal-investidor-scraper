import re
import os
import scrapy
from cei import response_handlers as CEI
from util import as_json


BASE_URL = 'https://cei.b3.com.br'
USER = os.environ["CEI_USER"]
PASS = os.environ["CEI_PASS"]
HEADERS = {
    'X-MicrosoftAjax': 'Delta=true',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36'
}

class CEISpider(scrapy.Spider):
    name = 'cei'
    start_urls = [BASE_URL]
    count = 0
    savedResponse = None

    def parse(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={'ctl00$ContentPlaceHolder1$txtLogin': USER, 'ctl00$ContentPlaceHolder1$txtSenha': PASS},
            callback=self.after_login
        )

    # @TD.with_headers
    def after_login(self, response):
        if CEI.authentication_failed(response):
            self.logger.error("Login failed")
            return

        yield scrapy.Request(BASE_URL + '/CEI_Responsivo/negociacao-de-ativos.aspx', callback=self.searchAtivos)

    def searchAtivos(self, response):
        agentes = response.xpath('//select[contains(@name, "Agentes")]')
        agentes = agentes.css('option::attr(value)').getall()[1:]
        data_ini = response.css('#ctl00_ContentPlaceHolder1_lblPeriodoInicialBolsa::text').get()
        data_fin = response.css('#ctl00_ContentPlaceHolder1_lblPeriodoFinalBolsa::text').get()
        self.count = self.count + 1
        data = {
            'ctl00$ContentPlaceHolder1$ddlAgentes': "386",
            'ctl00$ContentPlaceHolder1$ddlContas': "0",
            'ctl00$ContentPlaceHolder1$txtDataDeBolsa': "30/08/2018",
            'ctl00$ContentPlaceHolder1$txtDataAteBolsa': "10/02/2020",
            '__ASYNCPOST': "true"
        }

        if self.count == 1:
            res = response
            cb = self.searchAtivos
            self.savedResponse = response
        elif self.count == 2:
            res = self.savedResponse
            cb = self.parseAtivos
            updatedFields = response.text.split('|')
            for (i, field) in enumerate(updatedFields):
                if field in ['__VIEWSTATE', '__EVENTVALIDATION', '__VIEWSTATEGENERATOR']:
                    data[field] = updatedFields[i+1]

        yield scrapy.FormRequest.from_response(res, callback=cb, formdata=data, dont_filter=True, headers=HEADERS)

    def parseAtivos(self, response):
        table = response.css('#ctl00_ContentPlaceHolder1_rptAgenteBolsa_ctl00_rptContaBolsa_ctl00_pnAtivosNegociados')[0]
        for row in table.css('tbody tr'):  # get each row (tr) of the table
            info = {
                'Data do Negócio': row.xpath('td[1]/span//text()').get().strip(),
                'Compra/Venda': row.xpath('td[2]/text()').get().strip(),
                'Mercado': row.xpath('td[3]/text()').get().strip(),
                'Código': row.xpath('td[5]/text()').get().strip(),
                'Especificação do Ativo': row.xpath('td[6]/text()').get().strip(),
                'Quantidade': row.xpath('td[7]/text()').get().strip(),
                'Preço(R$)': row.xpath('td[8]/text()').get().strip(),
                'Total(R$)': row.xpath('td[9]/text()').get().strip(),
                'Fator de Cotação': row.xpath('td[10]/text()').get().strip()
            }
            print(info)
            yield info