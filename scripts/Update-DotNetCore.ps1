[CmdletBinding()]
Param(
    [Parameter()]
    [switch]$removeOld,
    [Parameter()]
    [switch]$update
)
<# Example of links
$dotnetLinks  = @(
	@{version = "2.1"; link = "https://download.visualstudio.microsoft.com/download/pr/633b17e5-a489-4da4-9713-5ddedf17a5f0/5c18f4203e837dd90ba3da59eee92b01/dotnet-hosting-2.1.15-win.exe"};
	@{version = "3.0"; link = "https://download.visualstudio.microsoft.com/download/pr/7333c58c-6aa8-4dc2-9c1c-8116f18298ee/4e987f142794d8949e79344f42e253e6/dotnet-hosting-3.0.2-win.exe"};
	@{version = "3.1"; link = "https://download.visualstudio.microsoft.com/download/pr/c9206d6d-a11a-4b0b-834b-6320c44d0a2d/993571f75a96b6a64f8bca001797c4f0/dotnet-hosting-3.1.1-win.exe"};
)
#>

$dotnetLinks  = @(
	#{links}
)

function update-dotnetCore($link){
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
	$ErrorActionPreference = "SilentlyContinue"
	$info = (dotnet --list-runtimes)
	$ErrorActionPreference = "Stop"
    $vers = [RegEx]::Matches($info, '\d+\.\d+\.\d+').value | Sort-Object | Get-Unique
    $verUrl = [RegEx]::Matches($link.link, '\d+\.\d+\.\d+').value
    $verUrl = [system.version]::Parse($verUrl)
    foreach($ver in $vers){
        $ver = [system.version]::Parse($ver)
        if($verUrl.major -eq $ver.major -and $verUrl.Minor -eq $ver.Minor -and $verUrl.Build -eq $ver.Build){
            Write-Host "Version of .netCore $verUrl already installed"
        }
        else{
            if((($ver.major).ToString() + '.' + ($ver.Minor).ToString()) -match $link.version){
                Write-Host "Updating .netCore $ver"
                $vr = $link.version -replace '[.]',''
                $outFile = "dotnetcore-$vr.exe"
                Push-Location -Path 'C:\Windows\Temp'
                try{
                    Invoke-WebRequest -Uri $link.link -UseBasicParsing -OutFile $outFile
                    Start-Process -FilePath ".\$outFile" -ArgumentList "OPT_NO_SHARED_CONFIG_CHECK=1 /install /quiet /norestart /log $($outFile).log" -Wait
                    Get-Content -Path ".\$($outFile).log"
                }
                catch{
                    Write-Host $_
                    exit 1
                }
            }
        }
    }
}
function remove-oldVersions($verToDel){
    $products = Get-WmiObject -Class win32_product | Where-Object { $_.name -match '.Net Core' -and $_.Caption -match '\d+\.\d+\.\d' -and $_.name -notmatch 'SDK' }
    $versions = [RegEx]::Matches($products.Caption, '\d+\.\d+\.\d+').value
    $versions = $versions | Sort-Object -Unique
    $matchedVersions = @()
    foreach($version in $versions){
        $version = [system.version]::Parse($version)
        if((($version.major).ToString() + '.' + ($version.Minor).ToString()) -match $verToDel){            
            $matchedVersions = $matchedVersions + $version
        }
    }
    if($matchedVersions.count -eq 1){
        Write-Host "Count of matched versions < 2 for version $verToDel"
		Write-Host "Installed version: $matchedVersions"
    }
    elseif($matchedVersions.count -eq 0){
        Write-Host "Version $verToDel is not installed"
    }
    else{
        $matchedVersions = $matchedVersions | Sort-Object -desc | Select-Object -skip 1
        $matchedVersionsToDel = @()
        foreach($product in  $products){
            $ver = [RegEx]::Matches($product.Caption, '\d+\.\d+\.\d+').value
            $ver = [system.version]::Parse($ver)
            foreach($matchedVersion in $matchedVersions){
                if($matchedVersion -match $ver){
                    $matchedVersionsToDel = $matchedVersionsToDel + $product
                }
            }
		}
    Write-Host("Next products will be deleted: ")
    $matchedVersionsToDel.name
    Push-Location $env:SYSTEMROOT\System32
    $matchedVersionsToDel.IdentifyingNumber | ForEach-Object { Start-Process msiexec -wait -ArgumentList "IGNOREDEPENDENCIES=ALL /q /x $_" }
    }
}
if(Get-Command dotnet -errorAction SilentlyContinue){
	if($update){
		foreach($link in $dotnetLinks){
			update-dotnetCore($link)
		}
	}
	if($removeOld){
		foreach($version in $dotnetLinks.version){
			remove-oldVersions($version)
		}
	}
}
else{
	"dotnet core is not installed"
}