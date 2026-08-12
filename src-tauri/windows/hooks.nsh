!macro StopGameDeckProcesses
  DetailPrint "Stopping GameDeck before updating..."
  nsExec::ExecToLog '"$SYSDIR\taskkill.exe" /F /T /IM gamedeck-desktop.exe'
  nsExec::ExecToLog '"$SYSDIR\taskkill.exe" /F /T /IM gamedeck-api.exe'
  nsExec::ExecToLog '"$SYSDIR\taskkill.exe" /F /T /IM gamedeck-api-x86_64-pc-windows-msvc.exe'
  Sleep 500
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro StopGameDeckProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro StopGameDeckProcesses
!macroend
