# The main Makefile is in the src directory

all:	
	echo "Building in src directory, product will go to bin directory"
	(cd src; make lexer;)

