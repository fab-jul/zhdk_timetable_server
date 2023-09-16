
import dataclasses
import enum
import socket

import re

"""
/ HTTP/1.1\r\nHost: 85.195.207.87:9000\r\nConnection: keep-alive\r\nContent-Length: 1
73823\r\nCache-Control: max-age=0\r\nUpgrade-Insecure-Requests: 1\r\nOrigin: http://85.195.207.8
7:9000\r\nContent-Type: multipart/form-data; boundary=----WebKitFormBoundaryyvCDO0AHNKvSQzv8\r\n
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Geck
o) Chrome/117.0.0.0 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0
.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7\r\nReferer:
     http://85.195.207.87:9000/\r\nAccept-Encoding: gzip, deflate\r\nAccept-Language: de-DE,de;q=0.9
     ,en-US;q=0.8,en;q=0.7\r\n\r\n------WebKitFormBoundaryyvCDO0AHNKvSQzv8\r\nContent-Disposition: fo
     rm-data; name="file"; filename="ZHdK_\xc2\xa0Termine.html"\r\nContent-Type: text/html\r\n\r\n<!D
     OCTYPE html>\n<html lang="de">\n<head>\n\n<meta http-equiv="Content-Type" content="text/html; ch
     arset=utf-8">\n<!-- \n\tThis website is powered by TYPO3 - inspiring people to share!\n\tTYPO3 i
     s a free open source Content Management Framework initially created by Kasper Skaarhoj and licen
     sed under GNU/GPL.\n\tTYPO3 is copyright 1998-2023 of Kasper Skaarhoj. Extensions are copyright
     of their respective owners.\n\tInformation and contribution at https://typo3.org/\n-->\n\n\n\n\n
     <meta name="generator" content="TYPO3 CMS">\n<meta name="copyright" content="(c) 2011 Zuercher H
     ochschule der Kuenste">\n<meta name="description" content="Hier finden Sie Ihre aktuellen, verga
     ngenen und k\xc3
     """


ZHDK_IDENTIFICATION = '<meta name="copyright" content="(c) 2011 Zuercher Hochschule der Kuenste">'

HTML_HEADER = """
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CalScrape</title>
    <style type="text/css">
	body {
	    margin: 40px auto;
	    max-width: 650px;
	    line-height: 1.6;
	    font-size: 18px;
            font-family: sans-serif;
	    color: #444;
	    padding: 0 10px
	}

	.error {
	font-weight: bold;
	    color: purple;
	}

	h1,h2,h3 {
	    line-height: 1.2
	}
    </style>
</head>
""".strip()

CONTENT = """
<h2>How to</h2>
<ol>
<li>
  <a href=https://intern.zhdk.ch/?meinetermine&tab%5Btabs%5D=all target="_blank">
    intern.zhdk.ch/?meinetermine
  </a> öffnen.</li>
<li> CMD + S um es als <code>.html</code> Datei zu speichern </li>
<li> Unten auf 'Choose File', dann die <code>.html</code> Datei auswählen und <strong>hochladen</strong>: </li>
</ol>
<form enctype="multipart/form-data" method="post" action="{post_destination}">
  <input name="file" type="file"/>
  <input type="submit" value="hochladen"/>
</form>
<ol start="4">
<li>
  Die .ics Datei wird heruntergeladen. Öffne sie um es im Kalender zu adden!
</li>
</ol>
"""


def _req_starts_with_http(req, path):
    return req.startswith(f"GET {path} HTTP")


class GetType(enum.Enum):
  START = "start"
  DOWNLOAD_ICS = "download_ics"
  DEEZ_NUTS = "deez_nuts"
  FAVICON = "favicon"

  UNKNOWN = "unknown"

  @classmethod
  def from_req(cls, req):
      if _req_starts_with_http(req, "/"):
          return GetType.START
      if _req_starts_with_http(req, "/deez"):
          return GetType.DEEZ_NUTS
      if _req_starts_with_http(req, "/favicon.ico"):
          return GetType.FAVICON
        # components = path.split('/')
        # print(path, '->', components)
        # if path.endswith('.ics') and len(components) == 3:
        #   return GetType.DOWNLOAD_ICS
      return GetType.UNKNOWN



def server(address):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(address)
    s.listen(5)  # How many unaccepted connections
    print("Waiting at", address)
    while True:
        client, addr = s.accept()
        print("New Connection", addr)
        handler(client)

port = 9000
public_ip = "85.195.207.87"



@dataclasses.dataclass
class HTTPResponse:

    code: int
    header: str
    content: str

    @property
    def code_str(self) -> str:
        return {200: "OK", 404: "Not Found", 301: "Redirect"}

    def send_and_close(self, client):
        client.send(f'HTTP/1.1 {self.code} {self.code_str}\n'.encode('ascii'))
        client.send(b'Content-Type: text/html\n')
        client.send(b'\r\n')
        client.send(self.header.encode("ascii"))
        client.send(self.content.encode('utf-8'))
        client.close()


def error(info):
    origin = self.headers.get('Origin')
    url = urlparse(origin)
    self.send_response(301)
    self.send_header('Location', f'{url.scheme}://{url.netloc}/error')
    content =f'<p><span class="error">Error</span>{info}</p>'
    return HTTPResponse(200, HTML_HEADER, content)


def _serve(get_type: GetType):
    post_destination = f"http://{public_ip}:{port}/"

    if get_type == GetType.START:
        content = CONTENT.format(post_destination=post_destination) + "\n"
        return HTTPResponse(200, HTML_HEADER, content)
    if get_type == GetType.FAVICON:
        return HTTPResponse(200, '', '')

    raise NotImplemented(get_type)


def _drain(client, remaining_len):
    buf = []
    while remaining_len > 0:
        print("Draining buffer, remaining=", remaining_len)
        result = client.recv(min(4096, remaining_len))
        remaining_len -= len(result)
        buf.append(result)
    return buf


def _handle_post(initial_req: bytes, client):
    initial_req_s = initial_req.decode()
    match = re.search(r"Content-Length: (\d+)\s", initial_req_s)
    if not match:
        raise ValueError
    content_len = int(match.group(1))
    remaining_len = content_len - len(initial_req)
    print("Receiving", content_len, "bytes total. Remaining:", remaining_len)

    if ZHDK_IDENTIFICATION not in initial_req_s:
        print("Invalid request, missing ZHDK!")
        _drain(client, remaining_len)
        return error("Invalid File")


def handler(client):
    while True:
        # Get some bytes from the client.
        req = client.recv(4096)
        print("Got", req)
        if not req:
            print("Nothing, done")
            break
        get_type = GetType.from_req(req[:200].decode())
        print("->", get_type)
        if get_type != GetType.UNKNOWN:
            _serve(get_type).send_and_close(client)
            break
        if req.startswith(b"POST / HTTP"):
            _handle_post(initial_req=req, client=client).send_and_close(client)
            break
            
        #resp = str("Hi").encode('ascii') + b'\n'
        #client.send(resp)
        print("Invalid request...")
    print("Closed", client)

server(('',port))
