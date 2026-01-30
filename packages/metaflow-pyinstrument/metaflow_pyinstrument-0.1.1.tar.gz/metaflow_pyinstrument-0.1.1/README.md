# metaflow-pyinstrument

Profile Metaflow steps with [pyinstrument](https://github.com/joerick/pyinstrument) and view results as interactive HTML cards.

## Installation

```bash
pip install metaflow-pyinstrument
```

## Usage

```python
from metaflow import FlowSpec, step, pypi_base
from metaflow_pyinstrument import pyinstrument_card

@pypi_base(packages={'pyinstrument': ''})
class MyFlow(FlowSpec):

    @pyinstrument_card()
    @step
    def start(self):
        # Your code here - will be profiled
        result = sum(i**2 for i in range(100000))
        self.next(self.end)

    @step
    def end(self):
        pass

if __name__ == '__main__':
    MyFlow()
```

Run with:
```bash
python myflow.py --environment=pypi --with kubernetes run
```

View the card:
```bash
python myflow.py card view start
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `card_id` | `"pyinstrument"` | Card identifier |
| `interval` | `0.001` | Sampling interval (seconds). Use `0.0001` for fast code |
| `html_attribute` | `"html"` | Artifact name for HTML output |
