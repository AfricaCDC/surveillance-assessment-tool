$ErrorActionPreference = 'Stop'
$bin = 'C:\Program Files\MySQL\MySQL Server 8.0\bin'
$config = 'C:\ProgramData\MySQL\MySQL Server 8.0\my.ini'
$taskDir = Join-Path $env:TEMP ('mysql-reset-' + [guid]::NewGuid().ToString('N'))
$password = 'MySQL!9a' + [guid]::NewGuid().ToString('N')
$process = $null
New-Item -ItemType Directory -Path $taskDir | Out-Null
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $taskDir /inheritance:r /grant:r "${identity}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not protect temporary password files.' }
$init = Join-Path $taskDir 'init.sql'
$client = Join-Path $taskDir 'client.ini'
try {
    Set-Content -LiteralPath $init -Encoding ASCII -Value "ALTER USER 'root'@'localhost' IDENTIFIED BY '$password';"
    Set-Content -LiteralPath $client -Encoding ASCII -Value "[client]`r`nuser=root`r`npassword=$password`r`nhost=127.0.0.1`r`nport=3306"
    Stop-Service MySQL80
    (Get-Service MySQL80).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(30))
    $process = Start-Process -FilePath "$bin\mysqld.exe" -ArgumentList @("--defaults-file=`"$config`"", "--init-file=`"$init`"", '--console') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskDir 'stdout.log') -RedirectStandardError (Join-Path $taskDir 'stderr.log')
    $verified = $false
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Seconds 1
        if ($process.HasExited) { throw 'MySQL reset startup failed.' }
        & "$bin\mysql.exe" "--defaults-extra-file=$client" --connect-timeout=2 --batch --skip-column-names --execute='SELECT CURRENT_USER();' 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $verified=$true; break }
    }
    if (-not $verified) { throw 'Password verification did not succeed.' }
    & "$bin\mysqladmin.exe" "--defaults-extra-file=$client" shutdown
    if ($LASTEXITCODE -ne 0) { throw 'Could not shut down the temporary server.' }
    $process.WaitForExit(30000) | Out-Null
    if (-not $process.HasExited) { throw 'Temporary server is still stopping.' }
    Start-Service MySQL80
    (Get-Service MySQL80).WaitForStatus('Running', [TimeSpan]::FromSeconds(30))
    & "$bin\mysql.exe" "--defaults-extra-file=$client" --connect-timeout=5 --batch --skip-column-names --execute='SELECT CURRENT_USER();'
    if ($LASTEXITCODE -ne 0) { throw 'Login verification after service restart failed.' }
    Write-Output "NEW_ROOT_PASSWORD=$password"
} finally {
    Remove-Item -LiteralPath $init,$client -Force -ErrorAction SilentlyContinue
    if ((-not $process -or $process.HasExited) -and (Get-Service MySQL80).Status -eq 'Stopped') { Start-Service MySQL80 }
}
