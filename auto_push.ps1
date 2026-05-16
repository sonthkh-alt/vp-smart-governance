$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = Get-Location
$watcher.IncludeSubdirectories = $true
$watcher.Filter = "*.*"
$watcher.EnableRaisingEvents = $true

Write-Host "Monitoring changes... (Press Ctrl+C to stop)"

while($true) {
    $change = $watcher.WaitForChanged([System.IO.WatcherChangeTypes]::All, 10000)
    if ($change.TimedOut -eq $false) {
        Write-Host "Detected change at: $($change.Name). Pushing to GitHub..."
        git add .
        $status = git status --porcelain
        if ($status) {
            git commit -m "Auto-update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            git push origin main
            Write-Host "Successfully pushed to GitHub!"
        } else {
            Write-Host "No changes to commit."
        }
    }
}
