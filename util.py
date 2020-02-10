import json

def as_json(handler):
    def loadJson(self, response):
        return handler(self, json.loads(response.text))

    return loadJson