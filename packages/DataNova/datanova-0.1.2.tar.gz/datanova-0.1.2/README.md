<p align="center">
  <img src="https://raw.githubusercontent.com/Riley25/DataNova/refs/heads/main/images/supernova.jpg" alt="DataNova Logo" width="800">
</p>

# 🌌 DataNova
**DataNova** — a toolkit for data exploration in Python with a few lines of code!

---

## 🚀 Features
- **Instant profiling**: Summarize your data with `profile(df)`
- **Bar Graph**: Shows the top 5 most common values `bar(df, 'Column_Name')`
- **Histogram**: Plots the distribution of numerical data `hist(df, 'Column_Name')`
- **Exploratory Data Analysis**: `EDA(df)`
- **Simple Linear Regression**: `lm(df, x_var, y_var)`

*what's next?*
- **Logistic Regression** (coming soon!)




---

## 🧭 Examples

Examples below use a dataset provided in the package called `WINE_DF`

```python
from datanova import *
profile( WINE_DF )
```
- Most of our data is not blank, expect for 'price' (*only 5% blank*).

|   | Variable Name | Variable Type | Missing Count | % Blank | Unique Values | Most Frequent Value | Mean  | Standard Deviation | Min | 25% | Median | 75% | Max |
|---|---------------|---------------|---------------|---------|----------------|---------------------|-------|--------------------|-----|-----|--------|-----|-----|
| 0 | country       | object        | 0             | 0       | 24             | US                  |     |                  |   |   |      |   |   |
| 1 | province      | object        | 0             | 0       | 120            | California          |     |                 |   |   |      |   |   |
| 2 | points        | int64         | 0             | 0       | 13             | 90                  | 89.55 | 2.32               | 84.0| 88.0| 90.0   | 91.0| 96.0|
| 3 | price         | float64       | 88            | 5       | 110            | 20.0                | 38.71 | 29.39              | 7.0 | 20.0| 30.0   | 48.0| 500.0|
| 4 | variety       | object        | 0             | 0       | 161            | Pinot Noir          |       |                    |     |     |        |     |     |



$$\\:$$
$$\\:$$


```python
bar( WINE_DF , 'province', top_n=7)
```
- California accounts for 32% of total wine sales, and the top five regions collectively contribute over half of all sales.

<p align="center">
  <img src="https://raw.githubusercontent.com/Riley25/DataNova/refs/heads/main/images/bar_graph.png" alt="Bar Graph Example" width="800">
</p>


$$\\:$$
$$\\:$$


```python
hist( WINE_DF , 'price' , xlim = [0,105], n_bins = 25)
```
- On average, a bottle of wine costs $38. The price ranges from: $20-$48

<p align="center">
  <img src="https://raw.githubusercontent.com/Riley25/DataNova/refs/heads/main/images/histogram.png" alt="Histogram Example" width="800">
</p>


$$\\:$$
$$\\:$$

```python
eda( WINE_DF )
```
- Creates bar graphs **and** histograms for all columns in the dataset.

$$\\:$$

### Regression Modeling 

```python
figure, model = lm(WINE_DF, 'points' , 'price' ,  ylimit = [0,150] ,
                   xtitle = 'Points' , ytitle = 'Price ($)' , 
                   show_summary=False , alpha = 0.8 ) 

display( figure )  
```

- Creates a simple linear regression 
- As the quality of wine increases (points), the price also increases.

<p align="center">
  <img 
  src="https://raw.githubusercontent.com/Riley25/DataNova/refs/heads/main/images/lm_plot.png" alt="Linear Model" 
  width="500">
</p>



--- 

## 🛠️ Installation
```bash
pip install DataNova
``` 

