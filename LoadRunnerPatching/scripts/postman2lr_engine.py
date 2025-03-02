import json
from urllib.parse import urlparse
import sys
import os

def get_postman(path):
    with open(path, 'r', encoding='UTF-8') as postman_f:
        result_dict = json.load(postman_f)
        return result_dict

#Your Postman collection JSON file goes here

# Read input parameters from command line
input_file = sys.argv[1]  # Postman JSON file
output_folder = sys.argv[2]  # Output folder where LoadRunner script will be saved

output_file_path = os.path.join(output_folder, os.path.splitext(os.path.basename(input_file))[0] + ".lr")

# Ensure output folder exists
#os.makedirs(output_folder, exist_ok=True)

# Load Postman collection data
data = get_postman(input_file)

#data=get_postman(sys.argv[1])
names = ""

c_web_set_user = """
    web_set_user("my_uname",
    "my_pwd",
    "my_url:my_port");
    """

c_web_header = """
    web_add_header("my_key",
    "my_value");
    """

c_get_request = """
    web_url("request_name",
            "URL=request_url",
            "Resource=0",
            "RecContentType=application/json",
            "Referer=",
            "Snapshot=snapshot_number.inf",
            "Mode=HTML",
            LAST);
    """

c_post_request = """
    web_custom_request("request_name",
        "URL=request_url",
        "Method=POST",
        "Resource=0",
        "RecContentType=application/json",
        "Referer=",
        "Snapshot=snapshot_number.inf",
        "Mode=HTML",
        "EncType=application/json",
        "Body=request_body",
        LAST);
    """

uname = ""
pwdvalue = ""
ictr=0

#Consolidation Dictionary for all items
dicts = []


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

# Generate LoadRunner script content
loadrunner_script = ""

#print(dicts)
#traverse the final dictionary to create the result file
for names in dicts:
    ictr = ictr + 1
    my_web_header = ""

    my_web_set_user = c_web_set_user
    my_get_request = c_get_request
    my_post_request = c_post_request

#        print(px["method"])
   # Authentication part processing module
    if "auth" in names["request"]:

        parsed = urlparse(names["request"]["url"]["raw"])

        if(names["request"]["auth"]["type"] == "basic"):
            for values in (names["request"]["auth"]["basic"]):
                if values["key"] == "password":
                    pwdvalue = values["value"]
                elif values["key"] == "username":
                    uname = values["value"]
            my_web_set_user = my_web_set_user.replace("my_uname", uname)
            my_web_set_user = my_web_set_user.replace("my_pwd", pwdvalue)
            my_web_set_user = my_web_set_user.replace("my_url", parsed.netloc)
            my_web_set_user = my_web_set_user.replace("my_port",
                                                      "443" if names["request"]["url"]["protocol"] == "https" else "80")
            print(my_web_set_user)

        if (names["request"]["auth"]["type"] == "bearer"):
            my_web_header = c_web_header
            my_web_header = my_web_header.replace("my_key", "Authorization")
            my_web_header = my_web_header.replace("my_value", "Bearer " + names["request"]["auth"]["bearer"][0]["value"])
            print(my_web_header)

        if (names["request"]["auth"]["type"] == "apikey"):
            my_web_header = c_web_header
            my_web_header = my_web_header.replace("my_key", names["request"]["auth"]["apikey"][1]["value"])
            my_web_header = my_web_header.replace("my_value",  names["request"]["auth"]["apikey"][0]["value"])
            print(my_web_header)

    # Header Part processing module
    if "header" in names["request"]:
        for i in range(len(names["request"]["header"])):
            my_web_header = c_web_header
            my_web_header = my_web_header.replace("my_key", names["request"]["header"][i]["key"])
            my_web_header = my_web_header.replace("my_value", names["request"]["header"][i]["value"])
            print(my_web_header)
    #
    # # GET BODY REQUEST Handling
    #
    if names["request"]["method"] == "GET":
        my_final_string = my_get_request
        my_final_string = my_final_string.replace("request_name", names["name"])
        my_final_string = my_final_string.replace("request_url", names["request"]["url"]["raw"])
        my_final_string = my_final_string.replace("snapshot_number", "t" + str(ictr))

        print("   lr_start_transaction(\"" + names["name"] + "\");")
        print(my_final_string)
        print("   lr_end_transaction(\"" + names["name"] + "\",LR_AUTO);" + "\n")
    # #
    # # # POST BODY REQUEST Handling
    if names["request"]["method"] == "POST":
        my_final_string = my_post_request
        my_body_string = (names["request"]["body"]['raw'])
        my_body_string = my_body_string.replace("\r\n", "")
        my_body_string = my_body_string.replace("\"", '\\"')

        my_final_string = my_final_string.replace("request_name", names["name"])
        my_final_string = my_final_string.replace("request_url", names["request"]["url"]["raw"])
        my_final_string = my_final_string.replace("snapshot_number", "t" + str(ictr))
        my_final_string = my_final_string.replace("request_body", my_body_string)

        # print("   lr_start_transaction(\"" + names["name"] + "\");")
        # print(my_final_string)
        # print("   lr_end_transaction(\"" + names["name"] + "\",LR_AUTO);" + "\n")

        loadrunner_script += f'   lr_start_transaction("{names["name"]}");\n'
        loadrunner_script += my_final_string + "\n"
        loadrunner_script += f'   lr_end_transaction("{names["name"]}",LR_AUTO);\n\n'

# Save output to file
with open(output_file_path, "w", encoding="UTF-8") as output_file:
    output_file.write(loadrunner_script)

print(f"Conversion successful! LoadRunner script created: {os.path.basename(output_file_path)}")
