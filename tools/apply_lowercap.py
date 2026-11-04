#!/usr/bin/env python3
"""Down on the second row no longer walks into a third row. Only the dock and one row below it are on screen (the stack is shifted up by one row), so with more apps than two rows
hold, Down moved the focus onto rows that cannot be seen: the second row went dark and the focus seemed gone. Down now stops on the second row; with "Hide the dock" set to
Down arrow or Both it hides the dock from there (it used to take the last row of all)."""
import os
APP = os.path.expanduser('~/Developer/webos-launcher-tvos/app')
p = os.path.join(APP, 'src/screens/Home.tsx')
s = open(p).read()
a = "if (rowIndex >= allRows.length - 1 && (hideMode === 'down' || hideMode === 'both')) n.dockHidden = true;\n\t\t\t\telse moveRow(Math.min(allRows.length - 1, rowIndex + 1));"
b = "if (rowIndex >= Math.min(allRows.length - 1, 1) && (hideMode === 'down' || hideMode === 'both')) n.dockHidden = true;\n\t\t\t\telse moveRow(Math.min(allRows.length - 1, 1, rowIndex + 1));"
assert s.count(a) == 1
open(p, 'w').write(s.replace(a, b, 1))
