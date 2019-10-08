# Project 0
A simple project that converts some plain text into HTML.
Single and double quotes are replaced with appropriate html entities and
line breaks are added to new lines.  

## To build
After downloading the repo use the following command to create a docker image:

`docker build --tag=proj0`

Then to run the image:

`docker run -it proj0`

## To run
Once in the docker image use the binary proj0 in bin to convert some text to HTML.
It takes in the location of a text file as a command and will produce an output
file called output.html.
For example using the included test.txt file:

`bin/proj0 data/test.txt`
