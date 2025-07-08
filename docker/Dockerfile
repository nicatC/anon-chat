FROM python:3.11-slim
WORKDIR /app

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        libpcap-dev gcc iptables tcpdump && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY python /app
RUN pip install --no-cache-dir pycryptodome scapy netifaces

ENV PYTHONUNBUFFERED=1
CMD sh -c 'iptables -I INPUT 1 -p udp --dport 5556 -j ACCEPT && \
           python -u -m src.bridge 5555'
