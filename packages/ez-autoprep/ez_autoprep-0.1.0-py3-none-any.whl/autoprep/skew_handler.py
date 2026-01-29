import numpy as np

class My1LogpSkew:
    def __init__(self, threshold: float = 1.0) -> None:
        self.threshold = threshold
        self.skew_cols = []

    def get_skew(self, X_col):
        X_col = np.asarray(X_col, dtype=float)
        X_col = X_col[~np.isnan(X_col)]

        n = len(X_col)
        if n < 3:
            return 0.0  

        mean = np.mean(X_col)
        std = np.std(X_col, ddof=1)

        if std == 0:
            return 0.0

        g1 = (n / ((n - 1) * (n - 2))) * np.sum((X_col - mean)**3) / (std**3)
        return g1

    def fit(self, X):
        X = np.asarray(X, dtype=float)
        self.skew_cols = []

        for i in range(X.shape[1]):
            skew = self.get_skew(X[:, i])
            if abs(skew) >= self.threshold:
                self.skew_cols.append(i)

        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float).copy()

        for i in self.skew_cols:
            col = X[:, i]
            mask = col > -1
            col[mask] = np.log1p(col[mask])
            X[:, i] = col

        return X

    def fit_transform(self, X):
        return self.fit(X).transform(X)

class MyBowleyLog1pSkew:
    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold
        self.skew_cols = []

    def get_bowley_skew(self, X_col):
        X_col = np.asarray(X_col, dtype=float)
        X_col = X_col[~np.isnan(X_col)]

        if len(X_col) < 3:
            return 0.0

        q1, q2, q3 = np.percentile(X_col, [25, 50, 75])

        denom = q3 - q1
        if denom == 0:
            return 0.0

        bowley = (q3 + q1 - 2 * q2) / denom
        return bowley

    def fit(self, X):
        X = np.asarray(X, dtype=float)
        self.skew_cols = []

        for i in range(X.shape[1]):
            skew = self.get_bowley_skew(X[:, i])
            if abs(skew) >= self.threshold:
                self.skew_cols.append(i)

        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float).copy()

        for i in self.skew_cols:
            col = X[:, i]
            
            mask = col > -1
            col[mask] = np.log1p(col[mask])

            X[:, i] = col

        return X

    def fit_transform(self, X):
        return self.fit(X).transform(X)
