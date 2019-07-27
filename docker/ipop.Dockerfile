FROM kcratie/prereq:0.2
WORKDIR /root/
COPY ./ipop-vpn_19.7.10_amd64.deb .
RUN apt-get install -y ./ipop-vpn_19.7.10_amd64.deb && rm -rf /var/lib/apt/lists/* && apt-get autoclean

CMD ["/sbin/init"]
