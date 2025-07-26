$uri = "ws://localhost:8001/ws/jwt-token"

$client = [System.Net.WebSockets.ClientWebSocket]::new()

# These were generated using Github Copilot
try {
    Write-Host "Connecting to $uri ..."
    $client.ConnectAsync([Uri]$uri, [Threading.CancellationToken]::None).Wait()

    if ($client.State -eq [System.Net.WebSockets.WebSocketState]::Open) {
        Write-Host "WebSocket connected successfully."

        # Buffer to receive messages
        $buffer = New-Object byte[] 1024
        $segment = New-Object System.ArraySegment[byte] $buffer

        # Wait to receive data or server close message
        while ($client.State -eq [System.Net.WebSockets.WebSocketState]::Open) {
            $result = $client.ReceiveAsync($segment, [Threading.CancellationToken]::None).Result

            if ($result.MessageType -eq [System.Net.WebSockets.WebSocketMessageType]::Close) {
                Write-Host "Server requested close: Status=$($result.CloseStatus), Description=$($result.CloseStatusDescription)"
                break
            }

            if ($result.Count -gt 0) {
                $msg = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $result.Count)
                Write-Host "Received message from server: $msg"
            } else {
                Write-Host "Received empty message or ping."
            }
        }

        Write-Host "Closing connection..."
        $client.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "Closing", [Threading.CancellationToken]::None).Wait()
    } else {
        Write-Host "Failed to connect. WebSocket State: $($client.State)"
    }
}
catch {
    Write-Host "Exception occurred while connecting or during communication:"
    Write-Host $_.Exception.Message
    if ($_.Exception.InnerException) {
        Write-Host "Inner Exception:"
        Write-Host $_.Exception.InnerException.Message
    }
}
finally {
    $client.Dispose()
}
