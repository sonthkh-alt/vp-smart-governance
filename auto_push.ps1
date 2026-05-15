$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = Get-Location
$watcher.IncludeSubdirectories = $true
$watcher.Filter = "*.*"
$watcher.EnableRaisingEvents = $true

Write-Host "🚀 Dang giam sat thay doi trong thu muc... (Nhan Ctrl+C de dung)" -ForegroundColor Cyan

while($true) {
    # Doi 10 giay de gom cac thay doi neu co nhieu file luu cung luc
    $change = $watcher.WaitForChanged([System.IO.WatcherChangeTypes]::All, 10000)
    if ($change.TimedOut -eq $false) {
        Write-Host "📝 Phat hien thay doi tai: $($change.Name). Dang chuan bi day len GitHub..." -ForegroundColor Yellow
        git add .
        # Kiem tra xem co gi de commit khong
        $status = git status --porcelain
        if ($status) {
            git commit -m "Auto-update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            git push origin main
            Write-Host "✅ Da cap nhat thanh cong len GitHub!" -ForegroundColor Green
        } else {
            Write-Host "ℹ️ Khong co thay doi thuc su de commit." -ForegroundColor Gray
        }
    }
}
