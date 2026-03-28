sudo fuser -k 7000/tcp && sudo netstat -tuln | grep 7000 && sudo lsof -i :8000 && sudo netstat -tuln | grep 8000
