with open('mattermemorys.html', 'r', encoding='utf-8') as f:
    content = f.read()

for term in ['licenza media', 'senza titoli', 'nessun background', 'nessun titolo', 'without academic degrees']:
    idx = content.find(term)
    if idx >= 0:
        print('FOUND "' + term + '" at ' + str(idx) + ': ' + repr(content[max(0,idx-30):idx+60]))
    else:
        print('NOT FOUND: ' + term)