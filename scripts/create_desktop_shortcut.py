import os
import subprocess

script_content = '''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "C:\\Users\\safak\\Desktop\\LogicDesign Studio.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "C:\\Windows\\System32\\wscript.exe"
oLink.Arguments = "\"C:\\Users\\safak\\Desktop\\Logic Design Studio\\Hızlı Başlat.vbs\""
oLink.WorkingDirectory = "C:\\Users\\safak\\Desktop\\Logic Design Studio"
oLink.Description = "LogicDesign Studio - Dijital Devre CAD & EDA Simülatörü"
oLink.IconLocation = "C:\\Windows\\System32\\shell32.dll,220"
oLink.Save
'''

vbs_path = r"C:\Users\safak\Desktop\Logic Design Studio\scripts\make_shortcut.vbs"
with open(vbs_path, "w", encoding="utf-8") as f:
    f.write(script_content)

subprocess.run(["cscript", "//nologo", vbs_path], check=True)
print("Windows Desktop Shortcut updated to Hızlı Başlat.vbs!")
