with open('mattermemorys.html', 'r', encoding='utf-8') as f:
    content = f.read()

for term in ['Autore', 'Chi sono', 'About', 'Biografia', 'N47Lab', 'N47 Lab']:
    idx = content.find(term)
    if idx >= 0:
        print(f'Found "{term}" at {idx}: {repr(content[max(0,idx-30):idx+150])}')
        print('---')