import re

with open('landing/templates/landing/property_detail.html', 'r') as f:
    lines = f.readlines()

# Fix 1: line 2276
for i in range(2270, 2280):
    if 'color:#FFFFFF' in lines[i] and 'Flexible pricing' in lines[i]:
        lines[i] = lines[i].replace('color:#FFFFFF', 'color:#111111')

# Fix 2: line 3513
for i in range(3500, 3530):
    if 'color:#FFFFFF' in lines[i] and 'House Rules & Policies' in lines[i]:
        lines[i] = lines[i].replace('color:#FFFFFF', 'color:#111111')

# Fix 3: Room select modal (lines 4790 to end)
for i in range(4790, len(lines)):
    # Replace white text with dark text
    lines[i] = lines[i].replace('color:#FFFFFF', 'color:#111111')
    lines[i] = lines[i].replace("borderColor='#FFFFFF'", "borderColor='#111111'")
    # Replace white rgba with black rgba for borders/hovers
    lines[i] = lines[i].replace('rgba(255,255,255,0.08)', 'rgba(0,0,0,0.08)')
    lines[i] = lines[i].replace('rgba(255,255,255,0.05)', 'rgba(0,0,0,0.05)')
    lines[i] = lines[i].replace('rgba(255,255,255,0.02)', 'rgba(0,0,0,0.02)')
    lines[i] = lines[i].replace('rgba(255,255,255,0.1)', 'rgba(0,0,0,0.1)')

with open('landing/templates/landing/property_detail.html', 'w') as f:
    f.writelines(lines)
print("Fixed invisible text.")
