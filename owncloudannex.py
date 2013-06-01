#!/usr/bin/env python2
import os
import re
import sys
import json
import time
import inspect
import webbrowser
import cookielib
import urllib
import urllib2

conf = False
version = "0.1.0"
plugin = "owncloudannex-" + version

pwd = os.path.dirname(__file__)
if not pwd:
    pwd = os.getcwd()
sys.path.append(pwd + '/lib')

import mppost
#import MultipartPostHandler
cookiejar = cookielib.LWPCookieJar()
cookie_handler = urllib2.HTTPCookieProcessor(cookiejar)
opener = urllib2.build_opener(cookie_handler)
#opener = urllib2.build_opener(cookie_handler, MultipartPostHandler.MultipartPostHandler)

if "--dbglevel" in sys.argv:
    dbglevel = int(sys.argv[sys.argv.index("--dbglevel") + 1])
else:
    dbglevel = 0

import CommonFunctions as common

def login(user, pword):
    common.log("")
    res = common.fetchPage({"link": conf["url"]})
    res = common.fetchPage({"link": conf["url"], "post_data": {"user": user, "password": pword, "remember_login": "1"}})
    common.log("res: " + repr(res["content"]), 3)
    if len(common.parseDOM(res["content"], "form", attrs={"id": "data-upload-form"})) > 0:
        common.log("Done")
    else:
        common.log("Failure")
        sys.exit(1)

def postFile(subject, filename, folder):
    common.log("%s to %s - %s" % ( filename, folder[0], subject))
    
    tmp_file = findInFolder(subject, folder)
    if tmp_file:
        common.log("File already exists: " + repr(tmp_file))
        return True
    common.log("BLA: " + repr(folder) + " - " + repr(filename))
    res = common.fetchPage({"link": conf["url"]})
    #post_data = {"user": user, "password": pword}
    post_data = []
    for name in common.parseDOM(res["content"], "input", ret="name"):
        if name != "dir":
            for val in common.parseDOM(res["content"], "input", attrs={"name": name}, ret="value"):
                post_data.append((name, val))

    post_data.append(("dir", folder))
    temp = readFile(filename, "rb")
    files = [("files[]", subject, temp)]

    tcookie = common.getCookieInfoAsHTML()
    cookie = ""
    tcookie = tcookie.replace("None", "'None'")
    common.log("cookies: " + repr(tcookie))
    for name in common.parseDOM(tcookie, "cookie", ret="name"):
        for val in common.parseDOM(tcookie, "cookie", attrs={"name": name}, ret="value"):
            cookie += "%s=%s; " % (name, val)
    cookie = cookie[:len(cookie) - 2]
    common.log("cookies: " + repr(cookie))
    res = mppost.post_multipart(conf["url"].replace("http://", "").replace("https://", "").replace("/", ":443"), "/?app=files&getfile=ajax%2Fupload.php", post_data, files, ssl=True, cookie=cookie)
    common.log("res: " + repr(res), 0)
    res = json.loads(res[1 : len(res) -1])
    if res["status"] == "success" and res["name"] == subject:
        common.log("Done: " + repr(res))
        return True
    else:
        sys.exit(1)

def findInFolder(subject, folder="/"):
    common.log("%s(%s) - %s(%s)" % (repr(subject), type(subject), repr(folder), type(folder)), 0)
    res = common.fetchPage({"link": conf["url"] + "?app=files&dir=" + folder})
    common.log("res: " + repr(res["content"]), 3)
    listing = common.parseDOM(res["content"], "tbody", attrs={"id": "fileList"})
    common.log("Listing: " + repr(listing), 3)
    if folder[0] != "/":
        folder = "/" + folder

    for tmp_file in common.parseDOM(listing, "tr", ret="data-file"):
        tmp_file = urllib.unquote_plus(tmp_file)
        common.log("folder: " + tmp_file)
        if tmp_file == subject:
            tmp_file = folder + tmp_file
            common.log("Done: " + repr(tmp_file))
            return tmp_file
    common.log("Failure")

def checkFile(subject, folder):
    common.log(subject)
    global m

    tmp_file = findInFolder(subject, folder)
    if tmp_file:
        common.log("Found: " + repr(tmp_file))
        print(subject)
    else:
        common.log("Failure")

def getFile(subject, filename, folder):
    common.log(subject)
    global m

    tmp_file = findInFolder(subject, folder)
    if tmp_file:
        common.log("tmp_file: " + repr(tmp_file))
        res = common.fetchPage({"link": "%s?app=files&getfile=ajax/download.php&files=%s&dir=%s" % (conf["url"], subject, folder)})
        saveFile(filename, res["content"], "wb")
        common.log("Done")
        return True
    common.log("Failure")


def deleteFile(subject, folder):
    common.log(subject)
    global m

    tmp_file = findInFolder(subject, folder)

    if tmp_file:
        res = common.fetchPage({"link": conf["url"]})
        requesttoken = common.parseDOM(res["content"], "input", attrs={"name": "requesttoken"}, ret="value")
        folder = folder[:len(folder)-1]
        # Important. Needs to recieve " instead of '. Hacked in common.
        res = common.fetchPage({"link": "%s?app=files&getfile=ajax/delete.php" % (conf["url"]), "post_data": {"dir": folder, "files": [subject], "requesttoken": requesttoken[0]}})
        common.log(repr(res))
        res = json.loads(res["content"])
        if len(res["data"]["files"]) > 0:
            common.log("Done")
            return True
    common.log("Failure")

def readFile(fname, flags="r"):
    common.log(repr(fname) + " - " + repr(flags))

    if not os.path.exists(fname):
        common.log("File doesn't exist")
        return False
    d = ""
    try:
        t = open(fname, flags)
        d = t.read()
        t.close()
    except Exception as e:
        common.log("Exception: " + repr(e), -1)

    common.log("Done")
    return d

def saveFile(fname, content, flags="w"):
    common.log(fname + " - " + str(len(content)) + " - " + repr(flags))
    t = open(fname, flags)
    t.write(content)
    t.close()
    common.log("Done")

def createFolder(path):
    common.log(path)
    if path.find("/") > -1:
        folder = path[:path.rfind("/")]
        name = path[path.rfind("/") + 1:]
    else:
        folder = "/"
        name = path
    common.log("BLA: " + repr(folder) + " - " + repr(name))
    res = common.fetchPage({"link": conf["url"]})
    requesttoken = common.parseDOM(res["content"], "input", attrs={"name": "requesttoken"}, ret="value")

    res = common.fetchPage({"link": conf["url"] + "?app=files&getfile=ajax/newfolder.php", "post_data": {"dir": folder, "foldername": name, "requesttoken": "".join(requesttoken)}})
    common.log("res: " + repr(res["content"]), 0)
    listing = common.parseDOM(res["content"], "tbody", attrs={"id": "fileList"})
    common.log("Listing: " + repr(listing))
    
    for tmp_file in common.parseDOM(listing, "tr", ret="data-file"):
        tmp_file = urllib.unquote_plus(tmp_file)
        common.log("folder: " + tmp_file)
        if tmp_file == subject:
            common.log("Done: " + repr(tmp_file))
            return tmp_file
    common.log(res)
    return path

def main():
    global conf
    args = sys.argv

    ANNEX_ACTION = os.getenv("ANNEX_ACTION")
    ANNEX_KEY = os.getenv("ANNEX_KEY")
    ANNEX_HASH_1 = os.getenv("ANNEX_HASH_1")
    ANNEX_HASH_2 = os.getenv("ANNEX_HASH_2")
    ANNEX_FILE = os.getenv("ANNEX_FILE")
    envargs = []
    if ANNEX_ACTION:
        envargs += ["ANNEX_ACTION=" + ANNEX_ACTION]
    if ANNEX_KEY:
        envargs += ["ANNEX_KEY=" + ANNEX_KEY]
    if ANNEX_HASH_1:
        envargs += ["ANNEX_HASH_1=" + ANNEX_HASH_1]
    if ANNEX_HASH_2:
        envargs += ["ANNEX_HASH_2=" + ANNEX_HASH_2]
    if ANNEX_FILE:
        envargs += ["ANNEX_FILE=" + ANNEX_FILE]
    common.log("ARGS: " + repr(" ".join(envargs + args)))
    ANNEX_HASH_1 = ANNEX_HASH_1 + "-"
    ANNEX_HASH_2 = ANNEX_HASH_2 + "-"

    conf = readFile(pwd + "/owncloudannex.conf")
    try:
        conf = json.loads(conf)
    except Exception as e:
        common.log("Traceback EXCEPTION: " + repr(e))
        common.log("Couldn't parse conf: " + repr(conf))
        conf = {"folder": "gitannex"}

    common.log("Conf: " + repr(conf), 2)
    changed = False
    if "uname" not in conf:
        conf["uname"] = raw_input("Please enter your owncloud email address: ")
        common.log("e-mail set to: " + conf["uname"])
        changed = True

    if "pword" not in conf:
        conf["pword"] = raw_input("Please enter your owncloud password: ")
        common.log("password set to: " + conf["pword"], 3)
        changed = True

    if "url" not in conf:
        conf["url"] = raw_input("Please enter your owncloud url: ")
        common.log("url set to: " + conf["url"], 3)
        changed = True

    login(conf["uname"], conf["pword"])
    
    folder = findInFolder(conf["folder"])
    if folder:
        common.log("Using folder: " + repr(folder))
        ANNEX_FOLDER = folder + "/"
    else:
        folder = createFolder("/" + conf["folder"])
        common.log("created folder0: " + repr(folder))
        ANNEX_FOLDER = folder + "/"

    folder = findInFolder(ANNEX_HASH_1, ANNEX_FOLDER)
    if folder:
        common.log("Using folder1: " + repr(folder))
        ANNEX_FOLDER = folder + "/"
    else:
        folder = createFolder(ANNEX_FOLDER + "/" + ANNEX_HASH_1)
        common.log("created folder1: " + repr(folder))
        ANNEX_FOLDER = folder + "/"

    folder = findInFolder(ANNEX_HASH_2, ANNEX_FOLDER)
    if folder:
        common.log("Using folder2: " + repr(folder))
        ANNEX_FOLDER = folder + "/"
    else:
        folder = createFolder(ANNEX_FOLDER + "/" + ANNEX_HASH_2)
        common.log("created folder2: " + repr(folder))
        ANNEX_FOLDER = folder + "/"

    if "store" == ANNEX_ACTION:
        postFile(ANNEX_KEY, ANNEX_FILE, ANNEX_FOLDER)
    elif "checkpresent" == ANNEX_ACTION:
        checkFile(ANNEX_KEY, ANNEX_FOLDER)
    elif "retrieve" == ANNEX_ACTION:
        getFile(ANNEX_KEY, ANNEX_FILE, ANNEX_FOLDER)
    elif "remove" == ANNEX_ACTION:
        deleteFile(ANNEX_KEY, ANNEX_FOLDER)
    else:
        if changed:
            saveFile(pwd + "/owncloudannex.conf", json.dumps(conf))
            common.log("saving owncloudannex.conf file.")
        else:
            common.log("ERROR")
            sys.exit(1)

t = time.time()
common.log("START")
if __name__ == '__main__':
    main()
common.log("STOP: %ss" % int(time.time() - t))
