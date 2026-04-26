$body = @{
    email = "newtest3@test.com"
    password = "New12345!"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Method Post -Uri "https://34-96-107-81.nip.io/api/v1/auth/register" -ContentType "application/json" -Body $body
    Write-Output "STATUS: 200 OK"
    Write-Output ($response | ConvertTo-Json)
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
    if ($_.ErrorDetails) {
        Write-Output $_.ErrorDetails.Message
    }
}
