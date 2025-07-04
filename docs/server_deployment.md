# Server deployment 

## **In case of issues with server setup on Ubuntu try these steps below:**

```
nano .env
```
- Opens the `.env` file in the Nano text editor to edit the HF_TOKEN = ""
- HF_TOKEN is huggingface API token

```
sudo lsof -i :8000
```
- Lists all processes using port 8000.
- Checks if uvicorn is running on port 8000.
- Finds and kills conflicting processes if the port is "already in use".

```
ps aux | grep uvicorn
```
- Searches all running processes for uvicorn.
- Helps confirm that the FastAPI server is currently running.
- Can find the PID (process ID) to stop it manually if needed (kill).

```
uvicorn fast-api.main_api_local:app --host 0.0.0.0 --port 8000
```

- Starts the FastAPI server using uvicorn.

```
curl http://102.220.23.39:8000/search?q=what+was+inflation
```
Sends a test HTTP GET request to the FastAPI /search endpoint. Tests if the deployed server is: 
- running and reachable
- accepting and responding to queries (like a question about inflation)

## **In case of issues with SSL Certification errors on Ubuntu:**

This regards to an issue with **`pdf_downloader.py`** when trying to scrape PDF's from the KNBS website. 
A SSL certification kept occurring most. A temporary fix for this was to add **`verify = False`** as a parameter
to all the response variables.

![image](https://github.com/user-attachments/assets/fabb2012-26b1-48b6-be43-43cd45d601d9)

**For a more permanent solution first check the certificate used on the website. Run: **
```
openssl s_client -connect [website name]:[port] -showcerts < /dev/null
```
Look out for the Certificate Chain and for a line like this: i:C = US, O = Let's Encrypt, CN = E5 , the O=Let’s Encrypt shows the name and CN=R5 gives the version.
In this case the certificate being used is the Let's Encrypt E5 certificate
Installation process of the certificate;

Download the Let’s Encrypt E5 certificate:
wget https://letsencrypt.org/certs/2024/e5.pem -O /tmp/lets-encrypt-e5.pem
Add to the CA store:
sudo cp /tmp/lets-encrypt-e5.pem /usr/local/share/ca-certificates/lets-encrypt-e5.crt
sudo update-ca-certificates
Then verify:
ls -l /etc/ssl/certs/ | grep lets-encrypt
cat /etc/ssl/certs/ca-certificates.crt | grep "Let's Encrypt"
Test the connectivity:
openssl s_client -connect [website name]:[port] -showcerts < /dev/null
Check for Verification: OK.
Test with curl: curl -v https://[website]
Expect HTTP 200 without certificate problem.
