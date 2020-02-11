def authentication_failed(response):
    errMsg = response.css('#ctl00_ContentPlaceHolder1_msgSenha')
    return len(errMsg) > 0