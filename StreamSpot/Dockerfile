##########################################
# This is a docker built for running the #
# sample code of StreamSpot              #
##########################################

FROM ubuntu:15.10

RUN cp /usr/share/doc/apt/examples/sources.list /etc/apt/sources.list

RUN echo "deb http://old-releases.ubuntu.com/ubuntu/ wily main universe restricted multiverse" >> /etc/apt/sources.list
RUN echo "deb-src http://old-releases.ubuntu.com/ubuntu/ wily main universe restricted multiverse" >> /etc/apt/sources.list
RUN echo "deb http://old-releases.ubuntu.com/ubuntu/ wily-security main universe restricted multiverse" >> /etc/apt/sources.list
RUN echo "deb-src http://old-releases.ubuntu.com/ubuntu/ wily-security main universe restricted multiverse" >> /etc/apt/sources.list
RUN echo "deb http://old-releases.ubuntu.com/ubuntu/ wily-updates main universe restricted multiverse" >> /etc/apt/sources.list
RUN echo "deb-src http://old-releases.ubuntu.com/ubuntu/ wily-updates main universe restricted multiverse" >> /etc/apt/sources.list
# RUN sed 's@http://in\.archive\.ubuntu\.com/@http://archive.ubuntu.com/@' -i /etc/apt/sources.list

RUN apt-get update -y
RUN apt-get install -y gcc make g++
# RUN apt-get install -y wget zip
# RUN apt-get install -y bzip2

# RUN wget ftp://ftp.fu-berlin.de/unix/languages/gcc/releases/gcc-5.2.0/gcc-5.2.0.tar.bz2
# RUN tar xvjf gcc-5.2.0.tar.bz2

# RUN apt-get install -y libgmp-dev libmpfr-dev libmpc-dev

# RUN cd gcc-5.2.0 \
#           && ./configure --disable-multilib \
#           && make
#
# RUN make install
