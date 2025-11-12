# Server Troubleshootng

Guide on how to solve server issues.

## How to get server running independently

### **Nginx service** 

Create file called `statschat-api`

```
sudo nano /etc/nginx/sites-available/statschat-api
```

```
server { 
listen 80; 
server_name [put in the ip]; 
location ~* /(admin|login|config|password|php|boaform) { 
deny all; 
return 403; 
} 
location / { 
proxy_pass http://127.0.0.1:8000; 
proxy_set_header Host $host; 
proxy_set_header X-Real-IP $remote_addr; 
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; 
proxy_set_header X-Forwarded-Proto $scheme; 
proxy_read_timeout 300s; 
proxy_connect_timeout 300s; 
proxy_send_timeout 300s; 
} 
access_log /home/user1/statschat-ke/statschat/log/nginx-access.log; 
error_log /home/user1/statschat-ke/statschat/log/nginx-error.log; 
}
```

To start `nginx` run the commands below one by one: 
```
sudo apt install nginx
```
```
sudo nginx -t 
```
```
sudo systemctl start nginx 
```
```
sudo systemctl status nginx
```

### **Api service file** 

Create service file called `statschat-api.service`
```
sudo nano /etc/systemd/system/statschat-api.service
```

In this file add the below. Please be aware the paths are generic so match to your current setup
```
[Unit] 
Description=StatsChat FastAPI Server for KNBS 
After=network.target 

[Service] 
User=user1 
Group=user1 
WorkingDirectory=/home/user1/statschat-ke/fast-api 
Environment="PATH=/home/user1/statschat-ke/venv/bin" 
ExecStart=/home/user1/statschat-ke/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 -
workers 4 --timeout-keep-alive 300 --timeout-graceful-shutdown 30 
Restart=always 
RestartSec=5 
StandardOutput=append:/home/user1/statschat-ke/statschat/log/statschat-api.log 
StandardError=append:/home/user1/statschat-ke/statschat/log/statschat-api-error.log 

[Install] 
WantedBy=multi-user.target 
```

To start the service run the commands below: 
```
sudo systemctl daemon-reload 
```
```
sudo systemctl enable statschat-api 
```
```
sudo systemctl start statschat-api.service 
```
```
sudo systemctl status statschat-api.service 
```
To check logs: 
```
tail -f /home/user1/statschat-ke/statschat/log/statschat-api-error.log
```
