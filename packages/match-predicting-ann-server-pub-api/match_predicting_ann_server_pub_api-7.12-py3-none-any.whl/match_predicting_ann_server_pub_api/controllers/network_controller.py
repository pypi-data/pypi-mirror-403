# coding: utf-8
from flask import request, jsonify, Flask
from flask.views import MethodView
from injector import Injector, inject

from match_predicting_ann_server_pub_api.models.predicting_data import PredictingData
from match_predicting_ann_server_pub_api.models.training_data import TrainingData

class NetworkControllerApi(MethodView):
    def __init__(self):
        pass

    def predict_result(self):
        """POST /api/network/predict
        Predicts the result using the given network and input data
        """
        pass
    def start_training(self):
        """POST /api/network/train
        Starts the training with the given data
        """
        pass


def register_NetworkController_routes(app: Flask, injector: Injector):
    controller = injector.get(NetworkControllerApi)
    app.add_url_rule("/api/network/predict", view_func=controller.predict_result, methods=['POST'])
    app.add_url_rule("/api/network/train", view_func=controller.start_training, methods=['POST'])

