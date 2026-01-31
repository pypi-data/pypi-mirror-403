# 📊 InstaViz - Intelligent Data Visualization

[![PyPI version](https://badge.fury.io/py/instaviz.svg)](https://badge.fury.io/py/instaviz)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**See truth, not just charts.**

InstaViz is a next-generation Python visualization library built on top of Matplotlib that **automatically chooses the best chart type** for your data and provides **natural language insights**.

---

## ✨ Features

- 🎯 Smart Auto-Selection
- 📈 Built-in Insights
- 🎨 Beautiful Themes
- 🔍 One-Line EDA
- 📊 Statistical Annotations
- 🚀 Zero Configuration

---

## 📦 Installation

```bash
pip install instavizlib
```

---

## 🚀 Quick Start

```bash
import instaviz as viz
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'category': ['A', 'B', 'C', 'D'] * 25,
    'value': np.random.randn(100),
    'score': np.random.exponential(50, 100)
})

viz.show(df)
viz.plot(df, x='category', y='value')
viz.distribution(df, 'score')
viz.compare(df, x='category', y='value')
viz.correlate(df)


```

## 📖 API Reference

| Function | Description |
|--------|------------|
| viz.show(df) | Automatic EDA |
| viz.plot(df, x, y) | Smart plot |
| viz.distribution(df, column) | Distribution |
| viz.compare(df, x, y) | Comparison |
| viz.trend(df, date, value) | Time series |
| viz.correlate(df) | Correlation |
| viz.relationship(df, x, y) | Relationships |
| viz.target(df, target) | Target analysis |

---

## 🎨 Themes

```bash
# Available themes: 'dark', 'minimal', 'vibrant', 'corporate'
viz.set_theme('dark')
```

---

## ⚙️ Configuration

```bash
viz.set_config(
    figsize=(12, 8),
    show_insights=True,
    auto_annotate=True,
    max_categories=20
)
```

---

## 📋 Requirements

- Python >= 3.8
- NumPy >= 1.20
- Pandas >= 1.3
- Matplotlib >= 3.5
- SciPy >= 1.7

---

## 👨‍💻 Author

Md. Ujayer Hasnat  
Email: dev.ujayerhasnat@gmail.com  
LinkedIn: https://linkedin.com/in/ujayerhasnat  
GitHub: https://github.com/CodexUjayer  

---

## 📄 License

MIT License

---

⭐ If you find this useful, please give it a star!