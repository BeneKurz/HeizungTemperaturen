 #!/bin/sh
# passt zwar hier nicht rein:
# service grafana-server restart

cd /u1/HeizungTemperaturen
/usr/local/bin/python3.6 /u1/HeizungTemperaturen/HeizungTemperaturen.py > /u1/HeizungTemperaturen/temp.log 2>&1

