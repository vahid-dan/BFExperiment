FROM solita/ubuntu-systemd:18.04
WORKDIR /root/
#fix for bad network URL proxy
COPY ./99fixbadproxy /etc/apt/apt.conf.d/99fixbadproxy
# install ipop
COPY ./ipop-vpn_19.2.2_amd64.deb .
RUN apt-get update -y
RUN apt-get install -y psmisc iputils-ping nano
RUN apt-get install -y ./ipop-vpn_19.2.2_amd64.deb
# clean up container
RUN rm -rf /var/lib/apt/lists/*
RUN apt autoclean


# ports for Tincan/Controller comms
EXPOSE 5800/udp
EXPOSE 5801/udp
CMD ["/sbin/init"]
