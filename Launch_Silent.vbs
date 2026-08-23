' Silent Launcher for Shohoj Macro (No console window)
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
exePath = currentDir & "\dist\ShohojMacro\ShohojMacro.exe"

If fso.FileExists(exePath) Then
    WshShell.Run Chr(34) & exePath & Chr(34), 1, False
Else
    WshShell.Run "python " & Chr(34) & currentDir & "\main.py" & Chr(34), 0, False
End If
