Set oShell = CreateObject ("Wscript.Shell")
Dim StrArgs
StrArgs = "cmd /c launch.bat"
oShell.Run strArgs, 0, True