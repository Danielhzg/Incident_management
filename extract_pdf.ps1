$bytes = [System.IO.File]::ReadAllBytes('e:\InaAi Competetion\proposal_incident_management.pdf')
$rawText = [System.Text.Encoding]::UTF8.GetString($bytes)
$lines = $rawText -split "`n"
foreach ($line in $lines) {
    $clean = $line -replace '[^\x20-\x7E]', ''
    if ($clean.Trim().Length -gt 3) {
        Write-Output $clean.Trim()
    }
}
