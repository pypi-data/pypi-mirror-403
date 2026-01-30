# pycogat

Python script that splits CogAT socre reports into single page PDFs and labels outputs based on ID extracted from the score report.

## Installation

install pycogat using pip:

```python
pip install pycogat
```

### Usage

```python
import pycogat
from pycogat.cogat import cogat_split

# simple example
cogat_split('C:\Documents\Reports\cogat_score_report.pdf',6)
```
