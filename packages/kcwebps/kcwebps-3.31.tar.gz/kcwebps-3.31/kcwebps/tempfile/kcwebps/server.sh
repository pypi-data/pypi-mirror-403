chmod -R 777 /kcwebps
kcwebps stop
sleep 1
pkill kcwebps
cd /kcwebps
nohup kcwebps --host 0.0.0.0 --port 39001 --processcount 4 --timeout 600 server -start > app/runtime/log/server.log 2>&1 &