FROM kcratie/prereq:0.1
WORKDIR /root/
COPY ./ipop-vpn_19.2.2_amd64.deb .
RUN apt-get install -y ./ipop-vpn_19.2.2_amd64.deb && rm -rf /var/lib/apt/lists/* && apt-get autoclean

CMD ["/sbin/init"]
