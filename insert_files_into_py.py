import os
import base64
import traceback

py_script = ""
with open('patch_killcount_mod_template.py', 'r') as py_script_file:
    py_script = py_script_file.read()

for item in os.listdir('.'):
    try:
        print(item)
        if os.path.splitext(item)[1] == ".py":
            continue
        filename = os.path.basename(item)
        filedata = ""
        with open(item, 'rb') as item_file:
            filedata = item_file.read()
        filedata = base64.b64encode(filedata).decode('utf-8')
        py_script = py_script.replace('$' + filename, filedata)
    except Exception:
        print(traceback.format_exc())

with open('patch_killcount_mod.py', 'w') as py_script_file:
    py_script_file.write(py_script)