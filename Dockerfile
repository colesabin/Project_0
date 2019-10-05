# Build a Docker project atop the CIS 461/561 shared platform,
# which is an Ubuntu machine with gcc, build tools including Make,
# and the RE/flex lexical analyzer builder.
#
# To build:
#    docker build --tag=proj0 .
#
# To run in the resulting Docker container:
#   docker run -it proj0
#
FROM michalyoung/cis461:base
COPY . /usr/src/proj0
WORKDIR /usr/src/proj0
RUN make
