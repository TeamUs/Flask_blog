# gradient_boosting.py
from sklearn.ensemble import GradientBoostingClassifier

class GradientBoostingModel:
    def __init__(self):
        self.model = GradientBoostingClassifier()

    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)

    def predict(self, X_test):
        return self.model.predict(X_test)
