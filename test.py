#!/usr/bin/env python3

import pyfoxtrot as pyfoxtrot

foxtrot = pyfoxtrot.Foxtrot("10.253.16.19")
foxtrot.readEntities()
list = foxtrot.readVariables()

print("Going to read quick variables")
list = foxtrot.readQuickVariables()
print(list)

foxtrot._disconnect()

