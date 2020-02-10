import json

def asJson(handler):
    def loadJson(self, response):
        handler(self, json.loads(response.text))

    return loadJson