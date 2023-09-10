from lxml import html, etree
import os, uuid
import dataclasses
                
from datetime import datetime
import re
import uuid
from pytz import timezone
from icalendar import Calendar, Event, vText


TIMEZONE = timezone("Europe/Zurich")
DATE_REGEX = re.compile(r"(\d\d).(\d\d).(\d\d\d\d)\s+(\d\d):(\d\d).+(\d\d):(\d\d)")
def parse_date(date_str):
  m = DATE_REGEX.search(date_str)
  if not m:
    raise ValueError
  day, month, year, start_h, start_m, end_h, end_m = map(int, m.groups())
  return (datetime(year, month, day, start_h, start_m, tzinfo=TIMEZONE),
          datetime(year, month, day, end_h, end_m, tzinfo=TIMEZONE))
                                 


@dataclasses.dataclass
class ParsedEvent:
  
  date: str
  kind: str
  title: str
  # teacher: str
  where: str

  @classmethod
  def make(cls, tds):
    attrs = {}
    for i, td in enumerate(tds):
      if i == 0:
        attrs["date"] = td.text
        attrs["kind"] = td[1].text
      elif i == 1:
        attrs["title"] = td.text_content().replace("\xa0", " / ")
      elif i == 2:
        attrs["where"] =  td.getchildren()[0].getchildren()[0].text
    return cls(**attrs)



class CalendarBuilder:

  def __init__(self):
    self.cal = Calendar()
    self.count = 0

  def add_parsed_event(self, parsed_event: ParsedEvent):
    
    event = Event()
    event.add('summary', parsed_event.title)
    start, end =  parse_date(parsed_event.date)
    event.add('dtstart', start)
    event.add('dtend', end)
    event['location'] = vText(parsed_event.where)
    self.cal.add_component(event)
    self.count += 1

  def as_bytes(self) -> bytes:
    #folder = f"tmp_ics_{str(uuid.uuid4())}"
    #os.makedirs(folder)
    #p = os.path.join(folder, "zhdk.ics")
    #with open(p, "wb") as f:
      #f.write(self.cal.to_ical())
    #return p
    return self.cal.to_ical()


class Pipe:

  def __init__(self, callback):
    self.callback = callback

  def __or__(self, text):
    self.callback(text)


class CalParseError(Exception):
  pass


def extract(content: str):

  tree = html.fromstring(content)
  xpath = '//*[@id="tabs--all"]/table'
  try:
    table = tree.xpath(xpath)[0]
  except IndexError as e:
    raise CalParseError() from e
  tbody = table.getchildren()[0]
  trs = tbody.getchildren()

  b = CalendarBuilder()
  for tr in trs:
    # print("NEW ROW")
    tds = tr.getchildren()
    if len(tds) == 1:
      # print("HEADER", etree.tostring(tds[0]))
      print(tds[0].text_content())
      continue 
    e = ParsedEvent.make(tds)
    b.add_parsed_event(e)

  #pipe | f'Found {b.count} events' 

  return b.as_bytes()
