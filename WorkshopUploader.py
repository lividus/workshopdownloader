import os
import bsonjs
import json

WORK_DIR = ".\workarea"
OUTPUT_DIR = "output"
DEFAULT_NAME = "WorkshopUpload"


def inputf():
    return os.path.join(WORK_DIR, DEFAULT_NAME)


def resultf():
    fp = os.path.abspath(os.path.join(WORK_DIR, OUTPUT_DIR))
    if not os.path.exists(fp):
        os.makedirs(fp)
    return os.path.join(fp, "result.txt")


with open(inputf(), 'rb') as f:
    decoded_doc = bsonjs.dumps(f.read())
    decoded_doc = decoded_doc.replace(" inf", ' "inf"')
    data = json.loads(decoded_doc)

    #with open(resultf(), 'w') as fo:
    #    fo.writelines(json.dumps(data, indent=4, sort_keys=False))

    print(data.keys())
    ObjectStates = data['ObjectStates']
    for obj in ObjectStates:
        if len(obj["Nickname"]) > 0 and obj["Name"] == "Bag":
            print("({0}; {1})".format(obj["Name"], obj["Nickname"], obj["Description"]))
            ContainedObjects = obj["ContainedObjects"]
            for obj in ContainedObjects:
                print("\t ({0}; {1})".format(obj["Name"], obj["Nickname"], obj["Description"]))
            #print("\t {0}".format(obj))
        #print(type(obj))
    #with open("result.txt", 'w') as o:
    #    o.writelines(json.dumps(data, indent=4, sort_keys=False))

    #with open("result.txt", 'w') as o:
    #    o.writelines(decoded_doc)

    #print(type(data))


    