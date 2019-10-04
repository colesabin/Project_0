#
# Makefile for building scanner.  You may prefer to use cmake, especially
# if you use CLion.  I don't know cmake well enough to give you a good
# portable CMakelists.txt
#
# Local tool paths and commands  (Varies by installation)
CCOPTS = -L /usr/local/lib
# REFLEX_LIB = /usr/local/lib/libreflex.a
REFLEX_INCLUDE = /usr/local/include/reflex
REFLEX = reflex
CC = g++ -std=c++11 -stdlib=libc++

default: lexer

lex.yy.cpp:	py_strip.lxx
	$(REFLEX) --nodefault $^

lexer: ../bin/lexer

../bin/lexer:  lex.yy.cpp
	$(CC) $(CCOPTS) -o ../bin/lexer -I $(REFLEX_INCLUDE) -l reflex $^

# There should be more dependencies for the header files, but I'm lazy.

clean:
	rm -f *.o
	rm -f lex.yy.cpp
	rm -f .../bin/*


