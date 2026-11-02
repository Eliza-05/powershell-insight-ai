"""Text only. No real credentials, payloads or host modifications are used."""

RUN = r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
PRIMARY = [
    ("B01", "Invoke-WebRequest -Uri 'https://example.com/lab.csv'"),
    ("B02", "Invoke-Expression -Command 'Write-Output 17'"),
    ("B03", f"New-ItemProperty -Path '{RUN}' -Name 'TrainingOnly' -Value 'C:\\MissingLab\\tool.exe' -PropertyType String"),
    ("B04", "Set-MpPreference -DisableRealtimeMonitoring $true"),
    ("B05", "Get-Process -Name 'lab-missing-process'"),
    ("B06", "Test-NetConnection -ComputerName 'example.invalid' -Port 443"),
    ("B07", "Get-StoredCredential -Target 'missing-training-entry'"),
]
AMBIGUOUS = [
    ("B01", "Invoke-WebRequest -Uri $unknown"),
    ("B02", "IEX $unknown"),
    ("B03", "Set-ItemProperty -Path $unknown -Name 'TrainingOnly' -Value 'data'"),
    ("B04", "Set-MpPreference -DisableRealtimeMonitoring $unknown"),
    ("B05", "& $unknown"),
    ("B06", "Test-NetConnection -ComputerName $unknown"),
    ("B07", "Get-StoredCredential -Target $unknown"),
]
