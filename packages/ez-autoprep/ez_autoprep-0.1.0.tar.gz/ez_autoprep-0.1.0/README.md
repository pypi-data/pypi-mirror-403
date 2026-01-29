# AutoPrep

**Automated Data Preprocessing Library for Python**

AutoPrep is a powerful Python library designed to streamline data preprocessing workflows. It provides a comprehensive suite of tools for handling missing values, scaling features, detecting and managing outliers, encoding categorical variables, and correcting data skewness. With AutoPrep, you can clean and prepare your datasets in just a few lines of code, dramatically reducing preprocessing time and eliminating repetitive tasks.

---

## Features

- **Missing Value Handling**: Multiple strategies (mean, median, most_frequent, auto)
- **Feature Scaling**: StandardScaler and MinMaxScaler implementations
- **Outlier Detection**: IQR, MAD, and Huber-based outlier handling
- **Skew Correction**: Log1p and Bowley transformations
- **Categorical Encoding**: OneHot and Ordinal encoding with unknown category handling
- **Full Pipeline**: Automated end-to-end preprocessing with AutoPrep
- **NumPy Native**: Works directly with NumPy arrays, no Pandas required
- **Modular Design**: Use individual components or the complete pipeline

---

## Installation

Install AutoPrep directly from PyPI:

```bash
pip install autoprep
```

### Requirements

- Python 3.10+
- NumPy >= 1.25

---

## Quick Start

### Complete Pipeline

```python
import numpy as np
from autoprep import AutoPrep

# Sample data with missing values and outliers
X_train = np.array([
    [1.0, "red", 100],
    [2.0, "blue", 200],
    [np.nan, "red", 300],
    [4.0, "green", 10000],  # outlier
    [5.0, "blue", 500],
], dtype=object)

# Create preprocessing pipeline
prep = AutoPrep(
    num_cols=[0, 2],
    cat_cols=[1],
    nan_strategy="auto",
    outlier_handler=MyIQROutlierHandler(strategy="clip"),
    encoder=MyOrdinalEncoder()
)

# Fit and transform
X_clean = prep.fit_transform(X_train)
print(X_clean)
```

---

## Usage Guide

### 1. Handling Missing Values

```python
from autoprep import MyNanHandler
import numpy as np

# Create handler with mean strategy
nan_handler = MyNanHandler(strategy="mean")

# Fit and transform
X_clean = nan_handler.fit_transform(X)

# Available strategies: 'mean', 'median', 'most_frequent', 'constant', 'auto'
```

**Auto Strategy**: Automatically detects the best strategy based on data type:
- Categorical columns → `most_frequent`
- Numeric columns → `median`

### 2. Scaling Features

```python
from autoprep import MyStandardScaler

# Standard scaling (zero mean, unit variance)
scaler = MyStandardScaler()
X_scaled = scaler.fit_transform(X_clean)
```

### 3. Handling Outliers

```python
from autoprep import MyIQROutlierHandler, MyMADOutlierHandler

# IQR-based outlier detection
outlier_handler = MyIQROutlierHandler(strategy="clip", factor=1.5)
X_no_outliers = outlier_handler.fit_transform(X_scaled)

# MAD-based outlier detection (more robust)
mad_handler = MyMADOutlierHandler(strategy="clip")
X_no_outliers = mad_handler.fit_transform(X_scaled)
```

**Strategies**:
- `clip`: Clip outliers to boundaries
- `remove`: Remove outlier rows (fit only)

### 4. Skew Correction

```python
from autoprep import My1LogpSkew, MyBowleyLog1pSkew

# Simple log1p transformation
skew_handler = My1LogpSkew(threshold=0.5)
X_corrected = skew_handler.fit_transform(X_no_outliers)

# Bowley skewness-based log1p
bowley_handler = MyBowleyLog1pSkew(threshold=0.5)
X_corrected = bowley_handler.fit_transform(X_no_outliers)
```

### 5. Encoding Categorical Features

```python
from autoprep import MyOneHotEncoder, MyOrdinalEncoder

# One-hot encoding
encoder = MyOneHotEncoder(handle_unknown="ignore")
X_encoded = encoder.fit_transform(X_categorical)

# Ordinal encoding
ordinal_encoder = MyOrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
X_encoded = ordinal_encoder.fit_transform(X_categorical)
```

---

## AutoPrep Pipeline

The `AutoPrep` class combines all preprocessing steps into a single, streamlined pipeline:

```python
from autoprep import AutoPrep, MyMADOutlierHandler, MyBowleyLog1pSkew, MyOrdinalEncoder

prep = AutoPrep(
    num_cols=[0, 2, 3],           # Numerical column indices
    cat_cols=[1],                  # Categorical column indices
    nan_strategy="auto",           # Auto-detect best NaN strategy
    outlier_handler=MyMADOutlierHandler(strategy="clip"),
    skew_handler=MyBowleyLog1pSkew(threshold=0.5),
    encoder=MyOrdinalEncoder(),
    scaler=MyStandardScaler()
)

# Fit on training data
X_train_clean = prep.fit_transform(X_train)

# Transform test data
X_test_clean = prep.transform(X_test)
```

### Pipeline Order

1. **NaN Handling** (numerical & categorical separately)
2. **Skew Correction** (numerical only, if specified)
3. **Outlier Detection** (numerical only)
4. **Scaling** (numerical only)
5. **Encoding** (categorical only)
6. **Concatenation** (numerical + categorical)

---

## Advanced Features

### Handling All-NaN Columns

```python
nan_handler = MyNanHandler(
    strategy="mean",
    handle_all_nan="zero"  # Options: 'zero', 'constant', 'error'
)
```

### Unknown Categories in Test Data

```python
# Ordinal encoder - assigns -1 to unknown categories
ordinal = MyOrdinalEncoder(
    handle_unknown="use_encoded_value",
    unknown_value=-1
)

# OneHot encoder - creates all-zero row for unknown categories
onehot = MyOneHotEncoder(handle_unknown="ignore")
```

---

## Project Structure

```
AutoPrep/
│
├── autoprep/
│   ├── __init__.py
│   ├── autoprep.py          # Main pipeline class
│   ├── nan_handler.py       # Missing value handling
│   ├── scaler.py            # Feature scaling
│   ├── outlier_handler.py   # Outlier detection and handling
│   ├── skew_handler.py      # Skewness correction
│   └── encoder.py           # Categorical encoding
│
├── tests/
│   └── test_pipeline.py     # Comprehensive test suite
│
├── setup.py
└── README.md
```

---

## Testing

Run the comprehensive test suite:

```bash
python tests/test_pipeline.py
```

The test suite covers:
- Default configurations
- Multiple NaN strategies (auto, mean, median)
- Various outlier handlers (IQR, MAD)
- Skew transformations
- Both encoders (OneHot, Ordinal)
- Edge cases (all-NaN columns, unknown categories)
- Large datasets (1000+ rows)
- Train-test consistency

---

## Examples

### Example 1: Simple Numerical Pipeline

```python
import numpy as np
from autoprep import AutoPrep

X = np.array([
    [1.0, 100],
    [2.0, 200],
    [np.nan, 300],
    [4.0, 10000],  # outlier
])

prep = AutoPrep(num_cols=[0, 1], nan_strategy="median")
X_clean = prep.fit_transform(X)
```

### Example 2: Mixed Data Types

```python
X_train = np.array([
    [25, "NYC", 50000, "Engineer"],
    [np.nan, "LA", 60000, "Designer"],
    [35, "NYC", 200000, "Manager"],  # outlier salary
    [28, np.nan, 55000, "Engineer"],
], dtype=object)

prep = AutoPrep(
    num_cols=[0, 2],
    cat_cols=[1, 3],
    nan_strategy="auto",
    encoder=MyOneHotEncoder()
)

X_clean = prep.fit_transform(X_train)
```

### Example 3: Custom Pipeline

```python
from autoprep import (
    AutoPrep, 
    MyMADOutlierHandler, 
    MyBowleyLog1pSkew,
    MyOrdinalEncoder
)

prep = AutoPrep(
    num_cols=[0, 1, 2],
    cat_cols=[3, 4],
    nan_strategy="median",
    outlier_handler=MyMADOutlierHandler(strategy="clip"),
    skew_handler=MyBowleyLog1pSkew(threshold=0.5),
    encoder=MyOrdinalEncoder(unknown_value=-999)
)
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

Built with care for the data science community.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/autoprep/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/autoprep/discussions)

---

**Happy Preprocessing!**