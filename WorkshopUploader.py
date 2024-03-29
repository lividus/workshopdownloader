import os
import sys
import time
import bsonjs
import json
from pathvalidate import sanitize_filepath
from pathvalidate import sanitize_filename
from tqdm import tqdm
import requests
import re
from urllib.parse import urlparse

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


def output_path(folder):
    fp = os.path.abspath(os.path.join(WORK_DIR, OUTPUT_DIR, folder))
    if not os.path.exists(fp):
        os.makedirs(fp)
    return fp


def build_path(root_folder, *paths):
    fp = os.path.abspath(os.path.join(root_folder, *paths))
    fp = sanitize_filepath(fp)
    if not os.path.exists(fp):
        os.makedirs(fp)
    return fp


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


def save_color_diffuse(save_path, data):
    ColorDiffuse = data.get("ColorDiffuse", None)
    if ColorDiffuse is not None:
        with open(os.path.join(save_path,"ColorDiffuse.json"), "w", encoding="utf8") as fo:
            json.dump(ColorDiffuse, fo, indent=4, sort_keys=False)


def get_name_from_content_disposition(fname, ContentDisposition):
    result = re.findall('filename=\"(.+)\"', ContentDisposition)
    if len(result) > 0:
        result_name, result_ext = os.path.splitext(result[0])
        return sanitize_filename(fname + result_ext)
    return None


def download_and_save_url(save_path, fname, url):
    url_parse = os.path.splitext(urlparse(url).path)[1]
    if len(url_parse) > 0:
        file_name = fname+url_parse
    else:
        r = requests.head(url, stream=True, allow_redirects=True)
        file_name = fname
        ContentDisposition = r.headers.get("Content-Disposition", None)
        name_error = False

        if ContentDisposition is None:
            name_error = True
        else:
            file_name = get_name_from_content_disposition(fname, ContentDisposition)

        if name_error or file_name is None:
            r = requests.get(url, stream=True, allow_redirects=True)
            ContentDisposition = r.headers.get("Content-Disposition", None)
            if ContentDisposition is not None:
                file_name = get_name_from_content_disposition(file_name, ContentDisposition)
            else:
                print(url)
                print("Server file name error. Use default name.")
                print(r.headers)
                file_name += ".bin"

    r = requests.get(url, stream=True, allow_redirects=True)
    file_size = int(r.headers.get('content-length', 0))
    initial_pos = 0

    file_path = sanitize_filepath(os.path.join(save_path, file_name))
    #if len(file_path) > 260:
    #    file_path = '\\\\?\\' + file_path
    #TODO: add check file exists.

    print("Start download url: {0} To: {1}".format(url, file_name))

    try:
        with open(file_path, 'wb') as f:
            with tqdm(total=file_size, unit='B',
                      unit_scale=True, unit_divisor=1024,
                      desc=file_name, initial=initial_pos,
                      ascii=True, miniters=1,
                      file=sys.stdout) as pbar:
                for chunk in r.iter_content(32 * 1024):
                    f.write(chunk)
                    pbar.update(len(chunk))
    except IOError as ioe:
        print(ioe)
        quit()

    print("\n")


def download_and_save_custom_image(save_path, file_name, data):
    CustomImage = data.get("CustomImage", None)
    if CustomImage is not None:
        ImageURL = CustomImage.get("ImageURL", None)
        if ImageURL is not None and len(ImageURL) > 0:
            download_and_save_url(save_path, file_name, ImageURL)
        ImageSecondaryURL = CustomImage.get("ImageSecondaryURL", None)
        if ImageSecondaryURL is not None and len(ImageSecondaryURL) > 0:
            download_and_save_url(save_path, file_name, ImageSecondaryURL)


def download_and_save_custom_mesh(save_path, file_name, data):
    CustomMesh = data.get("CustomMesh", None)
    if CustomMesh is not None:
        MeshURL = CustomMesh.get("MeshURL", None)
        if MeshURL is not None and len(MeshURL) > 0:
            download_and_save_url(save_path, file_name, MeshURL)
        DiffuseURL = CustomMesh.get("DiffuseURL", None)
        if DiffuseURL is not None and len(DiffuseURL) > 0:
            download_and_save_url(save_path, file_name, DiffuseURL)
        NormalURL = CustomMesh.get("NormalURL", None)
        if NormalURL is not None and len(NormalURL) > 0:
            download_and_save_url(save_path, file_name, NormalURL)
        ColliderURL = CustomMesh.get("ColliderURL", None)
        if ColliderURL is not None and len(ColliderURL) > 0:
            download_and_save_url(save_path, file_name, ColliderURL)


def download_and_save_custom_deck(save_path, file_name, data):
    CustomDeck = data.get("CustomDeck", None)
    if CustomDeck is not None:
        for key in CustomDeck.keys():
            deck_path = build_path(save_path, sanitize_filename(key))
            key_data = CustomDeck[key]
            FaceURL = key_data.get("FaceURL", None)
            if FaceURL is not None and len(FaceURL) > 0:
                download_and_save_url(deck_path, file_name, FaceURL)
            BackURL = key_data.get("BackURL", None)
            if BackURL is not None and len(BackURL) > 0:
                download_and_save_url(deck_path, file_name, BackURL)


def process_dirs(key_path, data):
    if isinstance(data, list):
        for obj in data:
            process_dirs(key_path, obj)
    elif isinstance(data, dict):
        # obj_name = data.get("Nickname", "")
        # ObjName = data.get("Name", "")
        # if len(obj_name) == 0 and len(ObjName) > 0:
        #     obj_name = ObjName
        # GUID = data.get("GUID", "")
        # if len(obj_name) == 0 and len(GUID) > 0:
        #     obj_name = GUID

        obj_name = "{0} {1}".format(data.get("Nickname", ""), data.get("GUID", ""))
        fp = build_path(key_path, obj_name)
        save_color_diffuse(fp, data)
        download_and_save_custom_image(fp, obj_name, data)
        download_and_save_custom_mesh(fp, obj_name, data)
        download_and_save_custom_deck(fp, obj_name, data)
        ContainedObjects = data.get("ContainedObjects", [])
        for obj in ContainedObjects:
            process_dirs(fp, obj)


def download_files(data):
    for key in data.keys():
        if isinstance(data[key], dict) and data[key]:
            fp = output_path("")
            process_dirs(fp, data[key])
        elif isinstance(data[key], list) and len(data[key]) > 0:
            fp = output_path(key)
            process_dirs(fp, data[key])


def main():
    with open(inputf(), 'rb') as f:
        decoded_doc = bsonjs.dumps(f.read())
        decoded_doc = decoded_doc.replace(" inf ", ' "inf" ').replace(" inf,", ' "inf",')

        with open(resultf(), "w", encoding='utf8') as of:
            of.writelines(decoded_doc)

        data = json.loads(decoded_doc)

        parsed_data = {}
        for key in data.keys():
            print([key])
            obj = data[key]
            buf = {}
            if isinstance(obj, list):
                buf = []
                data_walker(buf, data[key], 0)
            elif isinstance(obj, dict) and obj.get("Name", None) is not None:
                data_walker(buf, data[key], 0)
            parsed_data[key] = buf

        with open(jsonresultf(), "w", encoding='utf8') as of:
            of.writelines(json.dumps(parsed_data, indent=4, sort_keys=False))

        download_files(parsed_data)


if __name__ == "__main__":
    main()