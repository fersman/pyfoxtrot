# pyfoxtrot

Python library to simplify communication with Tecomat Foxtrot using PLCcomS <https://www.tecomat.cz/ke-stazeni/software/plccoms/>

## Install:

```
python3 -m pip install pyfoxtrot
```

## Usage:

```
from pyfoxtrot import pyfoxtrot
foxtrot = pyfoxtrot.Foxtrot("10.253.16.19")
list = foxtrot.readVariables()
```
