with open('mattermemorys.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Search for any relevant terms
for term in ['Autore', 'Biografia', 'senza', 'titoli', 'academic', 'degree', 'formal', 'affiliation', 'background']:
    idx = content.lower().find(term.lower())
    if idx >= 0:
        print('FOUND "' + term + '" at ' + str(idx) + ': ' + repr(content[max(0,idx-50):idx+100]))
        print('---')
    else:
        print('NOT FOUND: ' + term)