# register_task.ps1 - Register Daily Mutual Fund Refresh Task
$TaskName = "MutualFundChatbotRefresh"
$ProjectDir = "D:\PROJ 4 MUTUAL FUNDS CHATBOT"
$ScriptPath = Join-Path $ProjectDir "scheduler\silent_refresh.vbs"

# Check if task already exists and remove it to update
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the Trigger: Daily at 9:15 AM
$Trigger = New-ScheduledTaskTrigger -Daily -At 9:15AM

# Create the Action: Run the VBS script via wscript.exe
$Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$ScriptPath`""

# Register the Task
Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Description "Automated daily refresh for Mutual Fund FAQ Chatbot data."

Write-Host "SUCCESS: Task '$TaskName' registered for 9:15 AM daily."
