
def authentication_failed(response):
    errMsg = response.css('.td-login-erro-msg')
    return len(errMsg) > 0

def with_headers(handler):
    def createHeaders(self, response):
        headers = dict()
        token = response.css('#__AjaxAntiForgeryForm input')[0].attrib['value']
        tokenName = response.css('#__AjaxAntiForgeryForm input')[0].attrib['name']
        headers[tokenName] = token
        return handler(self, response, headers)

    return createHeaders