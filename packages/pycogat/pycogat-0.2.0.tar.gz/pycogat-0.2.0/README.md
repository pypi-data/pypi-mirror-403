# Project Description
![PyPI - Downloads](https://img.shields.io/pypi/dd/pycogat) ![PyPI - Version](https://img.shields.io/pypi/v/pycogat) ![Static Badge](https://img.shields.io/badge/python-3.10-blue) [![Run tests](https://github.com/Scipio94/pycogat/actions/workflows/tests.yml/badge.svg)](https://github.com/Scipio94/pycogat/actions/workflows/tests.yml)


# pycogat
Python package that splits CogAT score report PDF export into single page PDFs and labels output by the ID extracted from the PDF. To report a bug,request a new feature, or for Q&A submit an [issue](https://github.com/Scipio94/pycogat/issues/new/choose).

## Installation
~~~ python
pip install pycogat
~~~

### Usage
~~~ python
import pycogat
from pycogat.cogat import cogat_split

cogat_split('C:\Documents\Reports\cogat_score_report.pdf',6)
~~~
>[!NOTE]
>pycogat can search for IDs on the CogAT score reports based on their length, in the case above the length of the ID is 6.
