# coding: utf-8
from flask import request, jsonify, Flask
from flask.views import MethodView
from injector import Injector, inject

from match_predicting_ann_server_pub_api.models.dummy_dto import DummyDTO

class DummyControllerApi(MethodView):
    def __init__(self):
        pass

    def dummy(self):
        """GET /dummy
        dummy
        """
        pass


def register_DummyController_routes(app: Flask, injector: Injector):
    controller = injector.get(DummyControllerApi)
    app.add_url_rule("/dummy", view_func=controller.dummy, methods=['GET'])

