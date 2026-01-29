import numpy as np

class MyOrdinalEncoder:
    def __init__(self, handle_unknown="use_encoded_value", unknown_value=-1):
      
        if handle_unknown not in ["error", "use_encoded_value"]:
            raise ValueError(
                f"handle_unknown must be 'error' or 'use_encoded_value', got {handle_unknown}"
            )
        self.handle_unknown = handle_unknown
        self.unknown_value = unknown_value
        self.categories_ = None
        
    def fit(self, X):
       
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_features = X.shape[1]
        self.categories_ = []

        for i in range(n_features):
            col = X[:, i]
            uniques = np.unique(col)
            self.categories_.append({cat: idx for idx, cat in enumerate(uniques)})

        return self
    
    def transform(self, X):
        
        if self.categories_ is None:
            raise RuntimeError("Encoder has not been fitted!")

        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        X_out = np.empty_like(X, dtype=float)

        for i in range(X.shape[1]):
            mapping = self.categories_[i]
            for j, val in enumerate(X[:, i]):
                if val in mapping:
                    X_out[j, i] = mapping[val]
                else:
                    if self.handle_unknown == "error":
                        raise ValueError(
                            f"Unknown category '{val}' in column {i}. "
                            f"Known categories: {list(mapping.keys())}"
                        )
                    else:  # use_encoded_value
                        X_out[j, i] = self.unknown_value

        return X_out
    
    def fit_transform(self, X):
        """Fit and transform in one step."""
        self.fit(X)
        return self.transform(X)


class MyOneHotEncoder:
    def __init__(self, handle_unknown="ignore"):
        
        if handle_unknown not in ["error", "ignore"]:
            raise ValueError(
                f"handle_unknown must be 'error' or 'ignore', got {handle_unknown}"
            )
        self.handle_unknown = handle_unknown
        self.categories_ = None
        self.feature_indices_ = None
        
    def fit(self, X):
        
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.categories_ = []
        self.feature_indices_ = []

        start = 0
        for i in range(X.shape[1]):
            cats = np.unique(X[:, i])
            self.categories_.append(cats)
            self.feature_indices_.append((start, start + len(cats)))
            start += len(cats)

        return self
    
    def transform(self, X):
        
        if self.categories_ is None:
            raise RuntimeError("Encoder has not been fitted!")

        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples = X.shape[0]
        n_features = self.feature_indices_[-1][1]
        X_out = np.zeros((n_samples, n_features), dtype=float)

        for i in range(X.shape[1]):
            cats = self.categories_[i]
            start, end = self.feature_indices_[i]

            for j, val in enumerate(X[:, i]):
                matches = np.where(cats == val)[0]
                if matches.size:
                    X_out[j, start + matches[0]] = 1.0
                elif self.handle_unknown == "error":
                    raise ValueError(
                        f"Unknown category '{val}' in column {i}. "
                        f"Known categories: {list(cats)}"
                    )
                

        return X_out
    
    def fit_transform(self, X):
        """Fit and transform in one step."""
        self.fit(X)
        return self.transform(X)