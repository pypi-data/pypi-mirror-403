# Create a new file: main.py
import els_core

# Run ABAP code
code = """
*sia
DATA: counter TYPE I VALUE 0.
DO 5 TIMES.
  counter = counter + 1.
  WRITE: / counter.
ENDDO.
sia*
"""

result = els_core.run(code)
print(result)  # Outputs 1 2 3 4 5 on separate lines

# Or use REPL
els_core.repl()