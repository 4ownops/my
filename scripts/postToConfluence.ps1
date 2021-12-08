[CmdletBinding()]
Param (
    [Parameter(Mandatory=$True)]
    [ValidateNotNullOrEmpty()]
	[string]$securePairConfluence,
	[Parameter(Mandatory=$True)]
    [ValidateNotNullOrEmpty()]
	[string]$octopusApiKey,
	[Parameter()]
	[string]$confluenceUriApi = 'https://#{company_name}.atlassian.net/wiki/rest/api/',
    [Parameter()]
	[string]$octopusUriApi = "https://#{octopus_domain_name}/api/"
)
$bytes = [System.Text.Encoding]::ASCII.GetBytes($securePairConfluence) #for example "example@mysale.com:supErSecretp4$$w0rD"
$base64 = [System.Convert]::ToBase64String($bytes)
$basicAuthValue = "Basic $base64"
$confluenceHeaders = @{ Authorization = $basicAuthValue }
$octopusHeaders =  @{ "X-Octopus-ApiKey" = $octopusApiKey }
$deploymentId = $OctopusParameters['Octopus.Deployment.Id']
$envName = $OctopusParameters['Octopus.Deployment.Id']
$octopusUriDeployments = $octopusUriApi + "deployments/" + $deploymentId
$taskId = $(Invoke-RestMethod -uri $octopusUriDeployments -Method GET -Headers $octopusHeaders -ContentType "application/json").TaskId
$octopusUriTaskDetail = $octopusUriApi + "tasks/" + $taskId + "/details?verbose"
$getTaskIdDetail = Invoke-RestMethod -uri $octopusUriTaskDetail -Method GET -Headers $octopusHeaders -ContentType "application/json" 
$instanceArray = $getTaskIdDetail.ActivityLogs.Children.Children.Name | Sort-Object -Unique

$key = 'DOT' 
$title = (Get-Date).ToString('yyyy.MM.dd-hh.mm') + " " + $envName
$parentId = "577339796"
$pageContent = @"
<h1>$envName : </h1>
<h1>Next instances were successfully updated:</h1>
<p>$instanceArray</p>
"@

$post = @{
 type = 'page'
 "ancestors" = @(
   @{"id" = $parentId}
 )
 title = $title
 space = @{ key = $key}
 body = @{
 storage = @{
 value = $pageContent
 representation = 'storage'
 }
 }
}
$json = ConvertTo-Json $post
$confluenceUriApi += "content/"
try { 
  Invoke-RestMethod -Uri $confluenceUriApi -Method POST -Headers $confluenceHeaders -ContentType "application/json" -Body $json
} catch {$_.Exception.Response }
