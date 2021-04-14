import numpy as np

from scipy.stats import randint as sp_randInt
from scipy.stats import uniform as sp_randFloat

from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import accuracy_score
from sklearn.calibration import CalibratedClassifierCV

CV = 5
N_ITER = 30
RANDOM_SEED = 32


class SVC_model:

    def __init__(self):
        self.model = CalibratedClassifierCV(SVC(probability=True))
        self.metric_learner = None

    def add_metric_learner(self, metric_learner):
        self.metric_learner = metric_learner

    def get_best_model_configuration(self, X, y):
        estimator = CalibratedClassifierCV(SVC(probability=True))
        if self.metric_learner:
            self.metric_learner.fit(X, y)

        parameters = {
            'base_estimator__kernel': ['linear', 'poly', 'rbf', 'sigmoid'],
            'base_estimator__degree': list(range(2, 7)),
            'base_estimator__gamma': ['scale'],
            'base_estimator__probability': [True]
            }

        decision = RandomizedSearchCV(estimator=estimator,
                                      param_distributions=parameters,
                                      cv=CV,
                                      n_iter=N_ITER,
                                      n_jobs=5,
                                      verbose=1,
                                      scoring=accuracy_score,
                                      random_state=RANDOM_SEED)
        X = self.metric_learner.transform(X) if self.metric_learner else X
        decision.fit(X, y)
        if self.metric_learner:
            decision = Pipeline([
                ('metric_learner', self.metric_learner),
                #('svc', estimator)
                ('svc', decision)
            ])
        return decision

    def fit(self, X, y):
        self.classes_ = np.unique(y)
        self.model = self.get_best_model_configuration(X, y)

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def get_params(self):
        return self.model.get_params()