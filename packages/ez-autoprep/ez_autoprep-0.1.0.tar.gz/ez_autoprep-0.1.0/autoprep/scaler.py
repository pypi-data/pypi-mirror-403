import numpy as np

class MyStandardScaler:
    def __init__(self) -> None:
        self.mean_ = None
        self.std_ = None
    
    def fit(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 0:   # 
            raise ValueError("Input must be array-like, not scalar")
        if X.ndim == 1:
            X = X.reshape(-1, 1)
            
        X = np.array(X)
        self.mean_ = np.mean(X, axis=0)
        self.std_ = np.std(X, axis=0)
        return X
    
    def transform(self, X):
        
        X = np.asarray(X, dtype=float)
        if X.ndim == 0:   # 
            raise ValueError("Input must be array-like, not scalar")
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        if self.mean_ is None or self.std_ is None:
            raise ValueError("Must fit before transform")
        return (X - self.mean_) / self.std_
    
    def fit_transform(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 0:   # 
            raise ValueError("Input must be array-like, not scalar")
        if X.ndim == 1:
            X = X.reshape(-1, 1)
            
        self.fit(X)
        return self.transform(X)
