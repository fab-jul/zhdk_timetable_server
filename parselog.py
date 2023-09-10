import re

with open('log', 'r') as f:
    content = f.read()

#i =content.index('Luisa')
#i =content.index('submit submit-small')
r = re.compile('submit submit-small')
for m in r.finditer(content):
    i = m.start()
    print(content[i-10:i+40])

