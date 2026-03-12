
# -*- coding: utf-8 -*-
import zipfile
import re
with zipfile.ZipFile('templ/urist3/Опись имущества.docx') as z:
    for name in z.namelist():
        if 'document.xml' in name:
            xml = z.read(name).decode('utf-8')
            for m in re.finditer(r'<w:tc\b.*?</w:tc>', xml, re.DOTALL):
                if 'vm' in m.group(0):
                    valign = re.search(r'<w:vAlign w:val=\x22([^\x22]+)\x22', m.group(0))
                    text = re.sub(r'<[^>]+>', '', m.group(0))
                    print(repr(text), valign.group(1) if valign else 'None')

