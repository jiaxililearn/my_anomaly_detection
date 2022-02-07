##########################################
# This is a docker built for running the #
# sample code of StreamSpot              #
##########################################

FROM ubuntu:15.10

RUN cat>>/etc/apt/sources.list <<EOF
deb http://old-releases.ubuntu.com/ubuntu/ wily main universe restricted multiverse
deb-src http://old-releases.ubuntu.com/ubuntu/ wily main universe restricted multiverse

deb http://old-releases.ubuntu.com/ubuntu/ wily-security main universe restricted multiverse
deb-src http://old-releases.ubuntu.com/ubuntu/ wily-security main universe restricted multiverse

deb http://old-releases.ubuntu.com/ubuntu/ wily-updates main universe restricted multiverse
deb-src http://old-releases.ubuntu.com/ubuntu/ wily-updates main universe restricted multiverse
EOF

RUN apt-get update -y
RUN apt-get install -y checkinstall wget zip

RUN wget ftp://ftp.fu-berlin.de/unix/languages/gcc/releases/gcc-5.2.0/gcc-5.2.0.tar.bz2

RUN apt-get install -y libgmp-dev libmpfr-dev libmpc-dev

RUN cd gcc-5.2.0 \
          && ./configure --disable-multilib \
          && make

RUN make install
