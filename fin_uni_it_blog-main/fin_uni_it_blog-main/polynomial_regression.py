# polynomial_regression.py
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

class PolynomialRegressionModel:
    def __init__(self):
        self.poly = PolynomialFeatures(degree=2)
        self.model = LinearRegression()

    def train(self, X_train, y_train):
        X_poly = self.poly.fit_transform(X_train)
        self.model.fit(X_poly, y_train)

    def predict(self, X_test):
        X_poly_test = self.poly.transform(X_test)
        return self.model.predict(X_poly_test)
