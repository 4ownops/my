[CmdletBinding()]
Param(
	[Parameter(Mandatory = $true)]
	[string]$site_name,

	[Parameter(Mandatory = $true)]
	[string]$action
)

# Load IIS module:
Import-Module WebAdministration

function stop-AppPool ($appPoolName){
# Check if exists
if (Test-Path IIS:\AppPools\$appPoolName){
		# Stop App Pool if started
if ((Get-WebAppPoolState($appPoolName)).Value -eq "Started"){
    Write-host "Stopping IIS app pool $appPoolName"
    Stop-WebAppPool -Name $appPoolName
}
do
{
    Write-Host (Get-WebAppPoolState $appPoolName).Value
    Start-Sleep -Seconds 1
}
until ( (Get-WebAppPoolState -Name $appPoolName).Value -eq "Stopped" )
}
}


function start-AppPool ($appPoolName){
if (Test-Path IIS:\AppPools\$appPoolName){
	# Start App Pool
do {
    $get_apppool_state = Get-WebAppPoolState $appPoolName
    Write-Output "Starting IIS app pool $appPoolName"
    Start-WebAppPool $appPoolName
}
  while ($get_apppool_state.value -eq "Stopped")
}
Start-Sleep 2
}

switch ($action) {
    start {start-AppPool -appPoolName $site_name}
    stop {stop-AppPool -appPoolName $site_name}
}