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
PRODUCT = ../bin/py_strip

default: lexer

lex.yy.cpp:	py_strip.lxx
	$(REFLEX) --nodefault $^

lexer: ../bin/py_strip

../bin/py_strip:  lex.yy.cpp
	$(CC) $(CCOPTS) -o ${PRODUCT} -I $(REFLEX_INCLUDE) -l reflex $^

clean:
	rm -f *.o
	rm -f lex.yy.cpp
	rm -f ${PRODUCT}


