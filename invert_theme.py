import re

def invert_css_colors(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find the style block
    style_start = content.find('<style>')
    # Wait, there are multiple style blocks. Let's process the one from line 15.
    style_start = content.find('<style>', style_start + 1) 
    style_end = content.find('</style>', style_start)
    
    if style_start == -1 or style_end == -1:
        print("Style block not found")
        return
        
    css = content[style_start:style_end]
    
    # Invert root vars
    css = css.replace('--canvas:        #121212;', '--canvas:        #F5F5F5;')
    css = css.replace('--accent:        #FFFFFF;', '--accent:        #111111;')
    css = css.replace('--charcoal:      #FFFFFF;', '--charcoal:      #111111;')
    css = css.replace('--dark:          #F8FAFC;', '--dark:          #111111;')
    css = css.replace('--mid:           #CBD5E1;', '--mid:           #71717A;')
    css = css.replace('--muted:         #94A3B8;', '--muted:         #52525B;')
    css = css.replace('--border:        rgba(255, 255, 255, 0.08);', '--border:        rgba(0, 0, 0, 0.1);')
    css = css.replace('--border-light:  rgba(255, 255, 255, 0.04);', '--border-light:  rgba(0, 0, 0, 0.05);')
    css = css.replace('--surface:       rgba(255, 255, 255, 0.05);', '--surface:       rgba(255, 255, 255, 0.6);')
    
    # Invert other hardcoded values
    css = css.replace('#FFFFFF', '#111111')
    css = css.replace('#fff', '#111')
    css = css.replace('#000000', '#F5F5F5')
    
    # Invert rgbas
    css = re.sub(r'rgba\(255,\s*255,\s*255,\s*([0-9.]+)\)', r'rgba(0, 0, 0, \1)', css)
    
    # Some specific fixes
    css = css.replace('rgba(0, 0, 0, 0.05) !important;', 'rgba(255, 255, 255, 0.6) !important;')
    
    # Re-assemble
    new_content = content[:style_start] + css + content[style_end:]
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print("Theme inverted successfully!")

invert_css_colors('landing/templates/landing/property_detail.html')
