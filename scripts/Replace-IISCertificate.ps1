Import-Module webadministration
$binds = Get-WebBinding -Protocol 'https' | where {$_.certificateHash -like 'E99DB6FF17F725FAC35DE1BD2C0DB770171462C3'}
$Cert= Get-ChildItem -Path Cert:\LocalMachine\My | where-Object {$_.Thumbprint -like "1E53E2E566237439E9488ABA8770431C9F8C4F09"}
if ($Cert) {
	$CertThumbprint = $Cert | Select-Object -ExpandProperty Thumbprint
	foreach ($b in $binds)
		{
			$b.AddSslCertificate($CertThumbprint, "my")
		}
}

