with open('accounts/templates/accounts/base_auth.html', 'r') as f:
    content = f.read()

if 'cdn.tailwindcss.com' not in content:
    content = content.replace('</title>', '</title>\n    <script src="https://cdn.tailwindcss.com"></script>')
    with open('accounts/templates/accounts/base_auth.html', 'w') as f:
        f.write(content)
    print('Added Tailwind CSS to base_auth.html')
else:
    print('Tailwind already in base_auth.html')
