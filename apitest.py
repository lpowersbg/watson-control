import requests

resp1 = requests.get('http://10.201.37.151:8000/session_status')
resp2 = requests.get('http://10.201.37.150:8000/session_status')

json1 = resp1.json()
json2 = resp2.json()

print (json1["session_status"])
print (json2["session_status"])

if json1["session_status"] == "1":
    print ("cc1 on")
if json2["session_status"] == "1":
    print ("cc2 on")
if json1["session_status"] == "0":
    print ("cc1 off")
if json2["session_status"] == "0":
    print ("cc2 off")

