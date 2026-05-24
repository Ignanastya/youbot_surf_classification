from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


import joblib


class Classifier:
    def __init__(self):
        self.models = {}
        self.metrics = {}
        self.info = {}

        self.prev_dir = None
        self.prev_results = None
        self.alpha = 0.5

    def __copy__(self):
        cls = Classifier()
        cls.models = self.models.copy()
        cls.metrics = self.metrics.copy()
        cls.info = self.info.copy()
        cls.alpha = self.alpha
        return cls

    def add_surf(self, model, metric):
        """
        Adds surface to classify
        :param model: surface median model
        :param metric: surface metric
        :return: None
        """
        assert model.name == metric.name and model.feature_name == metric.feature_name, \
            'Model and metrics must have the same surfaces and feature name'

        name = model.name
        self.models[name] = model
        self.metrics[name] = metric

    def classify(self, direction, feature) -> dict:
        """
        Identifies a surface type by measured feature
        :param direction: movement direction in degs
        :param feature: value of single feature
        :return: surface type
        """
        results = {}
        for surf, model in self.models.items():
            prediction = model.predict(direction)
            deviation = self.calc_deviation(feature, prediction)
            results[surf] = self.metrics[surf].calc_metric(deviation)

        return results

    def prep_results(self, results):
        names = list(results.keys())
        values_raw = np.array(list(results.values()))
        values_raw /= np.sum(values_raw)

        max_idx = np.argmax(values_raw)
        surf_name_raw = names[max_idx]

        surf_name_upd = surf_name_raw
        values_upd = values_raw
        if self.prev_results is not None:
            values_upd = self.alpha * self.prev_results + (1 - self.alpha) * values_raw
            values_upd /= np.sum(values_upd)

            max_idx = np.argmax(values_upd)
            surf_name_upd = names[max_idx]
        self.prev_results = values_upd

        return surf_name_raw, values_raw, surf_name_upd, values_upd

    def classify_type(self, direction, feature) -> str:
        results = self.classify(direction, feature)
        surf_name, = self.prep_results(results)
        return surf_name

    def classify_type_and_prob(self, direction, feature):
        """

        :param direction: motion direction
        :param feature: feature value
        :return: (raw classification result, raw probabilities for ALL surfaces..., memory classification result,
        memory probabilities for ALL surfaces...)
        """
        results = self.classify(direction, feature)
        surf_name_raw, values_raw, surf_name_upd, values_upd = self.prep_results(results)
        return surf_name_raw, *values_raw, surf_name_upd, *values_upd

    @staticmethod
    def calc_deviation(val, pred_val):
        return val - pred_val


class MedianModel:
    def __init__(self, name, feature_name):
        self.name = name
        self.feature_name = feature_name
        self.func = None

    def predict(self, direction):
        """
        Predicts median value of Feature for surface with Name using Func
        :param direction: movement's direction in degrees
        :return: None
        """
        return self.func(direction)


class Metric:
    def __init__(self, name, feature_name):
        self.name = name
        self.feature_name = feature_name

    def calc_metric(self, value):
        pass


class MetricNormal(Metric):
    """
    Metric using normal distribution
    """

    def __init__(self, name, feature_name, std):
        super().__init__(name, feature_name)
        self.std = std

    def calc_metric(self, value):
        """
        Calculates metric for surface with Name using Normal distribution with (mean=0, self.std)
        :param value: real_value - pred_value
        :return: metric value
        """
        return norm(0, self.std).pdf(value) + 1e-3



