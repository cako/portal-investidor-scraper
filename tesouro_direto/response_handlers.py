
def authentication_failed(response):
    errMsg = response.css('.td-login-erro-msg')
    return len(errMsg) > 0