import re

with open('landing/templates/landing/property_detail.html', 'r') as f:
    lines = f.readlines()

for i in range(3025, 3060):
    lines[i] = lines[i].replace('color:#FFFFFF', 'color:#111111')
    lines[i] = lines[i].replace('rgba(255,255,255,0.08)', 'rgba(0,0,0,0.08)')
    lines[i] = lines[i].replace('rgba(255,255,255,0.05)', 'rgba(0,0,0,0.05)')

with open('landing/templates/landing/property_detail.html', 'w') as f:
    f.writelines(lines)
