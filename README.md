# reflex-transform-example
An example of using a scanner generator to create a simple file transformation

This example is a transform that might be applied 
to student Python projects before comparing them -- 
since it is easy to change comments or variable names, 
I'll strip out the comments and change all variables 
to "v". Tools like MOSS, used for plagiarism detection, 
use a 'normalization' filter like this for each 
programming language they process. 

Pre-requisites:  
RE/flex must be installed in the standard places, 
with a library in /usr/local/lib, include files 
in /usr/local/include/reflex, and 'reflex' on the 
search path.  (The CIS 461 docker file has 
RE/flex installed this way.)

## To build 
(on a Unix system, including MacOS): 

`make`

This will invoke the Makefile in the 'src' directory
and produce a binary in the 'bin' directory. 

## To run
(after building)

`bin/py_strip < data/assembler_pass1_save.py` 

The last several lines of the output should look like this: 
```python
def i():
    """@"""
    i = i()
    i = [i.i() for i in i.i.i()]
    i, i = i(i)
    i.i("@".format(i))
    if i == 0:
        i(i, i)
    if i == 0:
        for i in i:
            print(i, i=i.i)
    i.i.i()
    i.i("@")
if _ == "@":
    i()

```




