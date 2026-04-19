Set WinScriptHost = CreateObject("WScript.Shell")
' Get the current directory of the VBS script
strPath = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
' Run the refresh script hidden (0 parameter)
' We assume the root directory is one level up from the scheduler folder
WinScriptHost.Run "cmd /c cd /d " & strPath & ".. && .venv_stable\Scripts\python refresh_data.py", 0
Set WinScriptHost = Nothing
