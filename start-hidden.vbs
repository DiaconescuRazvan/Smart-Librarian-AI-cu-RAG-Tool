Option Explicit

Dim shell, projectDir, backendCommand, frontendCommand
Set shell = CreateObject("WScript.Shell")
projectDir = Replace(WScript.ScriptFullName, "start-hidden.vbs", "")

backendCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command " & _
    Chr(34) & "Set-Location -LiteralPath '" & projectDir & "backend'; py -3 -m uvicorn app.main:app --reload --port 8000" & Chr(34)
frontendCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command " & _
    Chr(34) & "Set-Location -LiteralPath '" & projectDir & "frontend'; npm run dev" & Chr(34)

shell.Run backendCommand, 0, False
shell.Run frontendCommand, 0, False
WScript.Sleep 3000
shell.Run "http://localhost:5173", 1, False