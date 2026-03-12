# -*- coding: utf-8 -*-
import zipfile
import re
import os

path = r'templ/urist3/Опись имущества.docx'
out_path = path

with zipfile.ZipFile(path, 'r') as z:
    file_dict = {name: z.read(name) for name in z.namelist()}

# Fix document.xml
xml = file_dict['word/document.xml'].decode('utf-8')

# We want to replace <w:vAlign w:val="bottom"/> with <w:vAlign w:val="top"/>
# ONLY in cells that contain {% vm %}
def repl(m):
    cell = m.group(0)
    if 'vm' in cell and '<w:vAlign w:val="bottom"/>' in cell:
        return cell.replace('<w:vAlign w:val="bottom"/>', '<w:vAlign w:val="top"/>')
    return cell

new_xml = re.sub(r'<w:tc\b.*?</w:tc>', repl, xml, flags=re.DOTALL)
file_dict['word/document.xml'] = new_xml.encode('utf-8')

with zipfile.ZipFile(out_path, 'w') as z:
    for name, content in file_dict.items():
        z.writestr(name, content)

print('Fixed align in template!')
