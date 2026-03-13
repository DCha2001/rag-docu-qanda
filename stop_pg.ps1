$svc = Get-Service | Where-Object { $_.DisplayName -like '*postgres*' }
if ($svc) {
    Write-Host "Found: $($svc.Name) — Status: $($svc.Status)"
    Stop-Service -Name $svc.Name -Force
    Set-Service -Name $svc.Name -StartupType Disabled
    Write-Host "Stopped and disabled."
} else {
    Write-Host "No postgres service found."
}
