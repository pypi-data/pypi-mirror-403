# FairyEx

FairyEx (for FEE Extraction) is a Python package to perform extraction with some ZIP solution file.


## Magical extraction

- Fast: focus on speed
- Efficient: low memory usage
- Easy: to install and to use


## Quickstart

```bash
pip install fairyex
```

```python
from fairyex import DarkSol

with DarkSol("Model Open World Solution.zip") as ds:
    df = ds.query(
        phase="STSchedule",
        children_class="Generator",
        children=ds.query_children("Generator"),
        properties=["Generation"],
        samples=["1", "2", "3"],
    )
```
