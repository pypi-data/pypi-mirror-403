# ipy-modal-backport

[![PyPI](https://img.shields.io/pypi/v/ipy-modal-backport)](https://pypi.org/project/ipy-modal-backport/)
[![Downloads](https://static.pepy.tech/personalized-badge/ipy-modal-backport?period=total&units=abbreviation&left_color=grey&right_color=green&left_text=pip%20installs)](https://pepy.tech/project/ipy-modal-backport)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A project to backport new modal features into interactions.py v5.

## Installation

```bash
pip install ipy-modal-backport
```

## Usage

```python
import interactions as ipy
import modal_backport

client = ipy.Client(
    ...
    modal_context=modal_backport.ModalContext,
)
```
