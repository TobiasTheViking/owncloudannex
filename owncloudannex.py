#!/usr/bin/env python2
import os
import re
import sys
import json
import time
import base64
import inspect
import webbrowser
import cookielib
import urllib
import urllib2

conf = False
version = "0.1.1"
plugin = "owncloudannex-" + version

pwd = os.path.dirname(__file__)
if not pwd:
    pwd = os.getcwd()
sys.path.append(pwd + '/lib')

import davlib

if "--dbglevel" in sys.argv:
    dbglevel = int(sys.argv[sys.argv.index("--dbglevel") + 1])
else:
    dbglevel = 0

import CommonFunctions as common
client = False
encAuth = False

def login(user, pword):
    common.log("")
    global client, encAuth
    
    base = conf["url"]
    base = base[base.find("//") + 2: base.find("/", 8)]
    encAuth = {"Authorization": "Basic %s" % ( base64.encodestring(user+":"+pword).strip() ) }
    common.log("Using base: " + base + " - " +  repr(encAuth))
    client = davlib.DAV(base, protocol="https")
    client.set_debuglevel(0)

    common.log("res: " + repr(client), 0)

    return True
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

    base = conf["url"][conf["url"].find("/", 8):]
    tpath = ("%s%s%s" % (base, folder, subject)).replace("//", "/")
    common.log("tpath: " + repr(tpath))
    response = False
    with open(filename, "rb") as fh:
        response = client.put(tpath, fh, "application/octet-stream", None, encAuth)
        
    if response:
        cont = response.read()
        if response.status == 201:
            common.log("Done: " + repr(cont))
            return True
    common.log("Failure")
    sys.exit(1)

def findInFolder(subject, folder="/"):
    common.log("%s(%s) - %s(%s)" % (repr(subject), type(subject), repr(folder), type(folder)), 0)
    if folder[0] != "/":
        folder = "/" + folder
    host = conf["url"][:conf["url"].find("/", 8)]
    base = conf["url"][conf["url"].find("/", 8):]
    tpath = (base + folder).replace("//", "/")
    tpath = tpath[:len(tpath)-1]
    bla = client.propfind(tpath, depth=1, extra_hdrs=encAuth)
    content = bla.read()
    content = content.replace("<D:", "<d:").replace("</D:", "</d:") # Box.com fix
    common.log("propfind: " + tpath + " - " + repr(content))

    for tmp_file in common.parseDOM(content, "d:href"):
        tmp_file = urllib.unquote_plus(tmp_file)
        tmp_file = tmp_file.replace(host, "")
        tmp_path = (base + folder +  subject).replace("//", "/")
        common.log("folder: " + tmp_file + " - " + tmp_path, 3)
        if tmp_file == tmp_path or tmp_file == tmp_path + "/":
            tmp_file = folder + subject
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
        base = conf["url"][conf["url"].find("/", 8):]
        tmp_file = (base + tmp_file).replace("//", "/")
        common.log("tmp_file: " + repr(tmp_file))
        response = client.get(tmp_file, encAuth)
        if response.status == 200:
            cont = response.read()
            common.log("Got data: " + repr(len(cont)))
            saveFile(filename, cont, "wb")
            common.log("Done")
            return True
    common.log("Failure")

def deleteFile(subject, folder):
    common.log(subject)
    global m

    tmp_file = findInFolder(subject, folder)

    if tmp_file:
        base = conf["url"][conf["url"].find("/", 8):]
        response = client.delete(base + tmp_file, encAuth)
        common.log("response: " + repr(response))
        if response.status == 204:
            common.log("Done: " + repr(response.read()))
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
    base = conf["url"][conf["url"].find("/", 8):]
    tpath = (base + path + "/").replace("//", "/")
    res = client.mkcol(tpath, encAuth)
    content = res.read()
    if res.status == 201:
        common.log("Done: " + repr(res.status) + " - " + repr(content))
        return path
    common.log("Failure: " + repr(res.status) + " - " + repr(content))
    sys.exit(1)

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
        ANNEX_HASH_1 = ANNEX_HASH_1 + "-"
    if ANNEX_HASH_2:
        envargs += ["ANNEX_HASH_2=" + ANNEX_HASH_2]
        ANNEX_HASH_2 = ANNEX_HASH_2 + "-"
    if ANNEX_FILE:
        envargs += ["ANNEX_FILE=" + ANNEX_FILE]
    common.log("ARGS: " + repr(" ".join(envargs + args)))

    
    if "-c" in sys.argv:
        conf = readFile(sys.argv[sys.argv.index("-c") + 1])
    else:
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
        conf["url"] = raw_input("Please enter your webdav url: ")
        common.log("webdav url set to: " + conf["url"], 3)
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
    elif ANNEX_HASH_1:
        folder = createFolder(ANNEX_FOLDER + "/" + ANNEX_HASH_1)
        common.log("created folder1: " + repr(folder))
        ANNEX_FOLDER = folder + "/"

    folder = findInFolder(ANNEX_HASH_2, ANNEX_FOLDER)
    if folder:
        common.log("Using folder2: " + repr(folder))
        ANNEX_FOLDER = folder + "/"
    elif ANNEX_HASH_2:
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
        saveFile(pwd + "/owncloudannex.conf", json.dumps(conf))
        common.log("saving owncloudannex.conf file.")
        setup = '''
Please run the following commands in your annex directory:

git config annex.owncloud-hook '/usr/bin/python2 %s/owncloudannex.py'
git annex initremote owncloud type=hook hooktype=owncloud encryption=%s
git annex describe owncloud "the owncloud library"
''' % (os.getcwd(), "shared")
        print setup
        sys.exit(1)

t = time.time()
if dbglevel > 0:
    if "--stderr" in sys.argv:
        sys.stderr.write("\n")
    else:
        print("")

common.log("START")
if __name__ == '__main__':
    main()
common.log("STOP: %ss" % int(time.time() - t))
