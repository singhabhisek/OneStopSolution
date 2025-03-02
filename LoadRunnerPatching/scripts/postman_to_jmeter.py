import json
import os
import sys
import uuid
from urllib.parse import urlparse
from JMeterTemplate import JMeterTemplate

def get_postman(path):
    with open(path, 'r', encoding='UTF-8') as postman_f:
        result_dict = json.load(postman_f)
        return result_dict

#check if command line parameter is provided else print usage-
if len(sys.argv) <= 1:
    print('ERROR!! Usage: PostmanToJmeter.py inputPostmanJSONFileFullPath')
    exit(1)

#Your Postman collection JSON file goes here
#data=get_postman('C:\\Users\\Abhisek\\Desktop\\Sample.postman_collection_mod.json')
data = get_postman(sys.argv[1])

#Load Template script structure
getRequest = JMeterTemplate.getRequestSample("")
postRequest = JMeterTemplate.postRequestSample("")
endRequest = JMeterTemplate.endRequestScript("")
startRequest = JMeterTemplate.startRequestScript("")
HeaderTags = JMeterTemplate.HeaderTagSample("")


mtr = """<elementProp name="" elementType="Header">
                <stringProp name="Header.name">$headKey$</stringProp>
                <stringProp name="Header.value">$headValue$</stringProp>
              </elementProp>"""
finalS = ""
TestPlanCompleteString = ""

#Consolidation Dictionary for all items
dicts = []
HeaderDict = {}

for x in range(len(data['item'])):
    #handle the folders
    try:
        # px = data['item'][x]['item'];
        #loop for multiple requests ina given folder

        for i in range(len(data['item'][x]['item'])):
            names = (data['item'][x]['item'][i]);
            #Append to the final dictionary
            dicts.append(names)

    except KeyError:
        px = (data['item'][x]);
        names = px
        # Append to the final dictionary
        dicts.append(names)


outputFile = os.path.splitext(sys.argv[1]) [0] + ".jmx"

outputFileName = open(outputFile, "a")
#Print the Jmeter start Request tags from sample request in template
print(startRequest, file=outputFileName)

for names in dicts:
    #reset variables for new collection request parsing
    HeaderDict={}
    finalS = ""

    #handle the authentication part
    if "auth" in names["request"]:
        parsed = urlparse(names["request"]["url"]["raw"])

        if(names["request"]["auth"]["type"] == "basic"):
            for values in (names["request"]["auth"]["basic"]):
                if values["key"] == "password":
                    pwdvalue = values["value"]
                elif values["key"] == "username":
                    uname = values["value"]
            HeaderDict['Authorization'] = "${__base64Encode(" + uname + ":" + pwdvalue + ",)}"

        if (names["request"]["auth"]["type"] == "bearer"):
            bearerToken = "Bearer " + names["request"]["auth"]["bearer"][0]["value"]
            HeaderDict["Authorization"] = bearerToken

        if (names["request"]["auth"]["type"] == "apikey"):
            API_Key_Name = names["request"]["auth"]["apikey"][1]["value"]
            API_Key_Value = names["request"]["auth"]["apikey"][0]["value"]
            HeaderDict[API_Key_Name] = API_Key_Value

    # Handle all the headers in the request
    if "header" in names["request"]:
        for i in range(len(names["request"]["header"])):
            HeaderKey = names["request"]["header"][i]["key"]
            HeaderValue = names["request"]["header"][i]["value"]
            HeaderDict[HeaderKey] = HeaderValue

    # GET BODY REQUEST Handling
    if names["request"]["method"] == "GET":
        #print (names["name"] + "--" + names["request"]["url"]["raw"])
        requestName = names["name"]
        domain = urlparse(str(names["request"]["url"]["raw"])).netloc
        path = urlparse(str(names["request"]["url"]["raw"])).path
        portNumber = "443" if names["request"]["url"]["protocol"] == "https" else "80"

        getRequestString = (getRequest.replace("$requestname$",requestName).replace("$portNumber$",portNumber).replace("$servername$",domain).replace("$pathname$",path))
        print (getRequestString, file=outputFileName)

    # POST BODY REQUEST Handling
    if names["request"]["method"] == "POST":
        #print(names["name"] + "--" + names["request"]["url"]["raw"] + "--" + names["request"]["body"]['raw'])
        requestName = names["name"]
        domain = urlparse(str(names["request"]["url"]["raw"])).netloc
        path = urlparse(str(names["request"]["url"]["raw"])).path
        portNumber = "443" if names["request"]["url"]["protocol"] == "https" else "80"
        body = str(names["request"]["body"]['raw']).replace('"',"&quot;")
        HeaderDict["Content-Type"] = "application/json"
        postRequestString = (postRequest.replace("$body$", body.strip()).replace("$requestname$",requestName).replace("$portNumber$",portNumber).replace("$servername$", domain).replace("$pathname$", path))
        print(postRequestString, file=outputFileName, end="")


    #Print all the headers to create a string containing header values
    for key in HeaderDict:
        finalS = finalS +  mtr.replace("$headKey$",key).replace("$headValue$", HeaderDict[key]) + "\n"

    #replace the value of headers
    print (HeaderTags.replace("$HeaderTags$",finalS), file=outputFileName)

#Print the Jmeter End Request tags from sample request in template
print(endRequest, file=outputFileName)

outputFileName.close()

#Strip blank lines (optional and can be removed)
with open(outputFile, 'r') as r, open(outputFile + ".x", 'w') as o:
    for line in r:
        #strip() function
        if line.strip():
            o.write(line)
os.remove(outputFile)
os.rename(outputFile+".x", outputFile)
print ("Output file at: " + outputFile)

