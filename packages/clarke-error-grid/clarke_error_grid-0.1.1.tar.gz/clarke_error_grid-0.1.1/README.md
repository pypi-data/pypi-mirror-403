# Clarke Error Grid

A simple Python implementation of the Clarke Error Grid for evaluating glucose prediction models.

## Installation

```bash
pip install clarke-error-grid
```


```python
import clarke_error_grid as ceg

ref = [100, 120, 180]
pred = [110, 130, 160]

# Ploting
plt = ceg.plot(ref, pred)
plt.show()

# Samples per region
zones = ceg.zone(ref, pred)
print(zones)
```

# Screenshots

![Plot](https://raw.githubusercontent.com/barthwalsaurabh0/clarke-error-grid/refs/heads/main/plot.png)
