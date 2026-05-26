import re

with open(r'e:\InaAi Competetion\proposal_incident_management.pdf', 'rb') as f:
    data = f.read()

# Try to extract readable text from PDF binary
text = data.decode('latin-1')

# Find text between BT and ET markers (PDF text objects)
text_objects = re.findall(r'BT(.*?)ET', text, re.DOTALL)

for obj in text_objects:
    # Extract text from Tj and TJ operators
    strings = re.findall(r'\((.*?)\)', obj)
    for s in strings:
        clean = s.strip()
        if len(clean) > 1:
            print(clean, end='')
    if strings:
        print()

# Also try to find readable strings directly
print("\n--- Additional text ---")
readable = re.findall(r'[\x20-\x7E]{5,}', text)
for r_text in readable:
    if any(c.isalpha() for c in r_text) and not r_text.startswith('/') and not r_text.startswith('%'):
        print(r_text)
