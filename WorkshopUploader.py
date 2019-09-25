import os
import bsonjs
import json

WORK_DIR = r".\workarea"
OUTPUT_DIR = "output"
DEFAULT_NAME = "WorkshopUpload"


def inputf():
    return os.path.join(WORK_DIR, DEFAULT_NAME)


def resultf():
    fp = os.path.abspath(os.path.join(WORK_DIR, OUTPUT_DIR))
    if not os.path.exists(fp):
        os.makedirs(fp)
    return os.path.join(fp, "result.txt")


def jsonresultf():
    fp = os.path.abspath(os.path.join(WORK_DIR, OUTPUT_DIR))
    if not os.path.exists(fp):
        os.makedirs(fp)
    return os.path.join(fp, "result.json")


def parse_custom_mesh(result, obj, level):
    # print("{0}CustomMesh".format("\t" * (level + 1)))
    CustomMesh = obj["CustomMesh"]
    result["CustomMesh"] = {"MeshURL": CustomMesh.get("MeshURL", None),
                            "DiffuseURL": CustomMesh.get("DiffuseURL", None),
                            "NormalURL": CustomMesh.get("NormalURL", None),
                            "ColliderURL": CustomMesh.get("ColliderURL", None)}
    # print("{0}MeshURL: {1}\n{0}DiffuseURL: {2}\n{0}NormalURL: {3}".format("\t" * (level + 2),
    #                                                                       CustomMesh.get("MeshURL", None),
    #                                                                       CustomMesh.get("DiffuseURL", None),
    #                                                                       CustomMesh.get("NormalURL", None)))


def parse_custom_deck(result, obj, level):
    # print("{0}CustomDeck".format("\t" * (level + 1)))
    CustomDeck = obj["CustomDeck"]
    result["CustomDeck"] = {}
    for key in CustomDeck.keys():
        result["CustomDeck"][key] = {"FaceURL": CustomDeck[key].get("FaceURL", None),
                                "BackURL": CustomDeck[key].get("BackURL", None)}
        # print("{0}{1}".format("\t" * (level + 2), key))
        # print("{0}FaceURL: {1}\n{0}BackURL: {2}".format("\t" * (level + 3),
        #                                             CustomDeck[key].get("FaceURL", None),
        #                                             CustomDeck[key].get("BackURL", None)))


def parse_custom_image(result, obj, level):
    # print("{0}CustomImage".format("\t" * (level + 1)))
    CustomImage = obj["CustomImage"]
    result["CustomImage"] = {"ImageURL": CustomImage.get("ImageURL", None),
                            "ImageSecondaryURL": CustomImage.get("ImageSecondaryURL", None)}
    # print("{0}ImageURL: {1}\n{0}ImageSecondaryURL: {2}".format("\t" * (level + 2),
    #                                           CustomImage.get("ImageURL", None),
    #                                           CustomImage.get("ImageSecondaryURL", None)))


def parse_color_diffuse(result, obj, level):
    #print("{0}ColorDiffuse".format("\t" * (level + 1)))
    ColorDiffuse = obj["ColorDiffuse"]
    result["ColorDiffuse"] = {"r": ColorDiffuse.get("r", None),
                            "g": ColorDiffuse.get("g", None),
                            "b": ColorDiffuse.get("b", None)}
    # print("{0}({1}; {2}; {3})".format("\t" * (level + 2), ColorDiffuse.get("r", None),
    #                     ColorDiffuse.get("g", None),
    #                     ColorDiffuse.get("b", None)))


def paser_object(result, data_dict, level):
    if "CustomMesh" in data_dict:
        parse_custom_mesh(result, data_dict, level)
    if "CustomDeck" in data_dict:
        parse_custom_deck(result, data_dict, level)
    if "CustomImage" in data_dict:
        parse_custom_image(result, data_dict, level)
    if "ColorDiffuse" in data_dict:
        parse_color_diffuse(result, data_dict, level)


def data_walker(result, data_dict, level=0):
    if isinstance(data_dict, dict):
        result["Name"] = data_dict.get("Name", "No name")
        result["Nickname"] = data_dict.get("Nickname", "No Nickname")
        result["GUID"] = data_dict.get("GUID", "No GUID")
        # print("{0}{1} '{2}' ({3})".format("\t" * (level), data_dict.get("Name", "No name"),
        #                                   data_dict.get("Nickname", "No nickname"),
        #                                   data_dict.get("GUID", "No GUID")))
        paser_object(result, data_dict, level)
        if "ContainedObjects" in data_dict:
            result["ContainedObjects"] = []
            for obj in data_dict["ContainedObjects"]:
                res_buf = {}
                data_walker(res_buf, obj, level+1)
                result["ContainedObjects"].append(res_buf)
    elif isinstance(data_dict, list):
        for obj in data_dict:
            if isinstance(obj, list) or isinstance(obj, dict):
                res_buf = {}
                data_walker(res_buf, obj, level+1)
                result.append(res_buf)


def main():
    with open(inputf(), 'rb') as f:
        decoded_doc = bsonjs.dumps(f.read())
        decoded_doc = decoded_doc.replace(" inf", ' "inf"')
        data = json.loads(decoded_doc)
        #print(data.keys())
        parsed_data = {}
        for key in data.keys():
            print([key])
            obj = data[key]
            #parsed_key = key
            buf = {}
            if isinstance(obj, list):
                buf = []
                data_walker(buf, data[key], 0)
            elif isinstance(obj, dict) and obj.get("Name", None) is not None:
                data_walker(buf, data[key], 0)
            parsed_data[key] = buf
        #t1 = json.loads(parsed_data)
        #print(json.dumps(parsed_data, indent=4, sort_keys=False))
        with open(jsonresultf(), "w", encoding='utf8') as of:
            of.writelines(json.dumps(parsed_data, indent=4, sort_keys=False))


if __name__ == "__main__":
    main()