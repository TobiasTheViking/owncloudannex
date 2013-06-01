import httplib
import mimetypes

def post_multipart(host, selector, fields, files, ssl=False, cookie=False):
    content_type, body = encode_multipart_formdata(fields, files)
    if ssl:
        h = httplib.HTTPS(host.replace(":443", ""), 443)
    else:
        h = httplib.HTTP(host)

    h.putrequest('POST', selector)
    h.putheader('User-Agent', "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1")
    h.putheader('Cookie', cookie)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    if errcode != 200:
        print("%s - %s - %s" % ( errcode, errmsg, headers))
    return h.file.read()

def encode_multipart_formdata(fields, files):
    LIMIT = '----------lImIt_of_THE_fIle_eW_'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + LIMIT)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + LIMIT)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + LIMIT + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % LIMIT
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

