from API.RequestSender import RequestSender
from API.Request import Request
from API.RequestHandler import RequestHandler

class DomesticRequestSender(RequestSender):
    def __init__(self, requestHandler: RequestHandler):
        self.requestHandler = requestHandler

    def sendRequest(self, request: Request,data=None):
        if not isinstance(request, Request):  # Corrected `instance` to `isinstance`

            return self.requestHandler.handleRequest(request,data)
        else:
            return self.requestHandler.handleRequest(request.to_dict())


    def handleBelt(self):
        self.requestHandler.handleBelt()

