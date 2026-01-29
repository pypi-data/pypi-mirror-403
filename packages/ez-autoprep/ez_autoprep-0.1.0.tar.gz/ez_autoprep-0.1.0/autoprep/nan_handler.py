import numpy as np

class MyNanHandler:
    def __init__(self,
                 missing_values=np.nan,
                 strategy="mean",  # can be 'mean', 'median', 'most_frequent', 'constant', or 'auto'
                 fill_value=None,
                 handle_all_nan="zero"  # 'zero', 'constant', or 'error'
                 ):
        self.missing_values = missing_values
        self.strategy = strategy
        self.fill_value = fill_value
        self.handle_all_nan = handle_all_nan
        self.statistics_ = None
        self.col_strategies_ = None  # store per-column strategy for 'auto'
        self.all_nan_cols_ = []  # track columns with all NaNs
    
    def _get_mask(self, X):
        """Get boolean mask of missing values."""
        if np.isnan(self.missing_values):
            return np.isnan(X)
        return X == self.missing_values
    
    def _detect_strategy(self, col):
    
        if col.dtype.kind in {'U', 'S', 'O'}:  # object/string
            return "most_frequent"
        elif col.dtype.kind in {'i', 'f'}:
            # If small number of unique values, treat as categorical
            if len(np.unique(col[~np.isnan(col)])) <= 10:
                return "most_frequent"
            else:
                return "median"
        else:
            return "median"  # fallback
    
    def fit(self, X):
      
        X = np.asarray(X, dtype=float)
        if X.ndim == 0:
            raise ValueError("Input must be array-like, not scalar")
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        n_features = X.shape[1]
        self.statistics_ = np.empty(n_features, dtype=float)
        self.col_strategies_ = [self.strategy] * n_features
        self.all_nan_cols_ = []
        
        mask = self._get_mask(X)
        
        for i in range(n_features):
            col = X[:, i]
            missing = mask[:, i]
            valid = col[~missing]

            # Handle all-NaN columns
            if valid.size == 0:
                self.all_nan_cols_.append(i)
                
                if self.handle_all_nan == "error":
                    raise ValueError(f"Column {i} has all missing values!")
                elif self.handle_all_nan == "zero":
                    self.statistics_[i] = 0.0
                elif self.handle_all_nan == "constant":
                    if self.fill_value is None:
                        raise ValueError(
                            f"Column {i} has all NaNs and handle_all_nan='constant', "
                            "but fill_value is None!"
                        )
                    self.statistics_[i] = self.fill_value
                else:
                    raise ValueError(
                        f"Invalid handle_all_nan: {self.handle_all_nan}. "
                        "Must be 'zero', 'constant', or 'error'."
                    )
                
                # Set strategy to constant for all-NaN columns
                self.col_strategies_[i] = "constant"
                continue

            # Determine strategy for this column
            strategy = self.strategy
            if self.strategy == "auto":
                strategy = self._detect_strategy(valid)
            self.col_strategies_[i] = strategy

            # Calculate statistic based on strategy
            if strategy == "mean":
                self.statistics_[i] = valid.mean()
            elif strategy == "median":
                self.statistics_[i] = np.median(valid)
            elif strategy == "most_frequent":
                values, counts = np.unique(valid, return_counts=True)
                self.statistics_[i] = values[np.argmax(counts)]
            elif strategy == "constant":
                if self.fill_value is None:
                    raise ValueError("fill_value must be set for strategy: constant!")
                self.statistics_[i] = self.fill_value
            else:
                raise ValueError(f"Invalid strategy: {strategy}")
        
        # Warn user about all-NaN columns
        if self.all_nan_cols_:
            fill_method = "0" if self.handle_all_nan == "zero" else str(self.fill_value)
            print(f"Warning: Columns {self.all_nan_cols_} have all NaN values. "
                  f"Filling with {fill_method}.")
        
        return self
    
    def transform(self, X):
        
        X = np.asarray(X, dtype=float)
        if X.ndim == 0:
            raise ValueError("Input must be array-like, not scalar")
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        if self.statistics_ is None:
            raise RuntimeError("NanHandler has not been fitted!")

        X = np.asarray(X, dtype=float).copy()
        mask = self._get_mask(X)

        for i in range(X.shape[1]):
            X[mask[:, i], i] = self.statistics_[i]

        return X
    
    def fit_transform(self, X):
       
        self.fit(X)
        return self.transform(X)