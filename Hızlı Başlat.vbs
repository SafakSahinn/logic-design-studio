Set WshShell = CreateObject("WScript.Shell")
strPath = "C:\Users\safak\Desktop\Logic Design Studio"
WshShell.CurrentDirectory = strPath
WshShell.Run Chr(34) & strPath & "\Başlat.bat" & Chr(34), 0, False
Set WshShell = Nothing
