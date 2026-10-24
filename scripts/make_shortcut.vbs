Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "C:\Users\safak\Desktop\LogicDesign Studio.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "C:\Windows\System32\wscript.exe"
oLink.Arguments = Chr(34) & "C:\Users\safak\Desktop\Logic Design Studio\Hızlı Başlat.vbs" & Chr(34)
oLink.WorkingDirectory = "C:\Users\safak\Desktop\Logic Design Studio"
oLink.Description = "LogicDesign Studio - Dijital Devre CAD & EDA Simülatörü"
oLink.IconLocation = "C:\Windows\System32\shell32.dll,220"
oLink.Save
