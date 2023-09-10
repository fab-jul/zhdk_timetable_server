from http.server import BaseHTTPRequestHandler, HTTPServer
import enum
from urllib.parse import urlparse

from datetime import datetime
import logging

import re
import time
import contextlib
import cal_parse_lib

hostName = "0.0.0.0"
# note that this is a pair defined in the router!
serverPortInternal = 443
serverPortExternal = 9999

# TODO
POST_DESTINATION = f"http://77.109.152.38:{serverPortExternal}/"

ZHDK_IDENTIFICATION = '<meta name="copyright" content="(c) 2011 Zuercher Hochschule der Kuenste">'

FUCKING_HEADER = """
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

CONTENT = f"""
<h2>How to</h2>
<ol>
<li>
  <a href=https://intern.zhdk.ch/?meinetermine&tab%5Btabs%5D=all target="_blank">
    intern.zhdk.ch/?meinetermine
  </a> öffnen.</li>
<li> CMD + S um es als <code>.html</code> Datei zu speichern </li>
<li> Unten auf 'Choose File', dann die <code>.html</code> Datei auswählen und <strong>hochladen</strong>: </li>
</ol>
<form enctype="multipart/form-data" method="post" action="{POST_DESTINATION}">
  <input name="file" type="file"/>
  <input type="submit" value="hochladen"/>
</form>
<ol start="4">
<li>
  Die .ics Datei wird heruntergeladen. Öffne sie um es im Kalender zu adden!
</li>
</ol>
"""


class GetType(enum.Enum):
  START = "start"
  DOWNLOAD_ICS = "download_ics"
  DEEZ_NUTS = "deez_nuts"

  UNKNOWN = "unknown"

  @classmethod
  def from_path(cls, path: str):
    if path == "/":
      return GetType.START
    if path == "/deez":
      return GetType.DEEZ_NUTS
    components = path.split('/')
    print(path, '->', components)
    if path.endswith('.ics') and len(components) == 3:
      return GetType.DOWNLOAD_ICS
    return GetType.UNKNOWN


class Server(BaseHTTPRequestHandler):

  def _write_str(self, s: str):
    self.wfile.write(s.encode("utf-8"))

  @contextlib.contextmanager
  def output(self, status):
    self.send_response(status)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    self._write_str("<!doctype html>")
    self._write_str("<html>")
    self._write_str(FUCKING_HEADER)
    self._write_str("<body>")
    self._write_str(f"<h1>ZHDK Calendar Exporter</h1>")
    yield
    self._write_str("</body></html>\n")

  def do_GET(self):
    request_type: GetType = GetType.from_path(self.path)

    if request_type == GetType.START:
      with self.output(200):
        self._write_str(CONTENT)
    elif request_type == GetType.DEEZ_NUTS:
      with self.output(200):
        self._write_str('<p class="error">DEEZ NUTS</p>')
#    elif request_type == GetType.DOWNLOAD_ICS:
#      self.send_response(200)
#      self.send_header('Content-type', 'text')
#      self.send_header('Content-Disposition', 'attachment; filename="zhdk.ics"')
#      self.end_headers()
#      print(f'Serving {self.path} ...')
#      with open(self.path.lstrip('/'), 'rb') as f: 
#        self.wfile.write(f.read()) 
    else:
      with self.output(200):
        self._write_str('<p class="error">wtf</p>')

  def _reply_with_file(self, content):
    self.send_response(200)
    self.send_header('Content-type', 'text')
    self.send_header('Content-Disposition', 'attachment; filename="zhdk.ics"')
    self.end_headers()
    self.wfile.write(content) 
    #self._invalid_post()

  def _invalid_post(self):
    origin = self.headers.get('Origin')
    url = urlparse(origin)
    self.send_response(301)
    self.send_header('Location', f'{url.scheme}://{url.netloc}/error')
    self.end_headers()
#    with self.output(200):
#      self._write_str(
#          '<p><span class="error">Looks like incorrect HTML!</span></p>')
#    #self.rfile.close()

  def do_POST(self):
    content_len = int(self.headers.get('Content-Length'))
    print(f'Got {content_len} bytes...')
    START_NUM_BYTES = 1000
    if content_len < START_NUM_BYTES:
      self._invalid_post()
      return
    start = self.rfile.read(START_NUM_BYTES)
    if ZHDK_IDENTIFICATION not in start.decode():
      sep = "*" * 60
      print(f'Invalid file uploaded! Got:\n{sep}\n{start.decode()}\n{sep}')
      print(f'HTTP Header:\n{self.headers}')
      print(sep)
      self._invalid_post()
      return
    post_body = start + self.rfile.read(content_len - START_NUM_BYTES)
    findname(post_body)

    try:
      content = cal_parse_lib.extract(post_body)
    except Exception as e:
      print(e)
      with self.output(200):
        self._write_str(
         '<p><span class="error">Error</span> is this a valid HTML?!</p>')
    else:
      self._reply_with_file(content)


FINDNAMERE = re.compile('submit submit-small')

def findname(post_body: bytes):
    count = 0
    content = post_body.decode()
    for m in FINDNAMERE.finditer(content):
        i = m.start()
        print(content[i-10:i+40])
        count += 1
    if count == 0:
        print('No matches!')



if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPortInternal), Server)
    print("Server started http://%s:%s" % (hostName, serverPortInternal))
    print("  External: http://%s:%s" % (hostName, serverPortExternal))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
