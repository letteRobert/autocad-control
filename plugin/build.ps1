param(
    [string]$AutoCADDirectory = 'C:\Program Files\Autodesk\AutoCAD 2024'
)

$ErrorActionPreference = 'Stop'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$output = Join-Path $PSScriptRoot '..\assets\autocad2024'
$assemblies = foreach ($name in 'acmgd.dll', 'acdbmgd.dll', 'accoremgd.dll') {
    (Get-Item -LiteralPath (Join-Path $AutoCADDirectory $name)).FullName
}
$wpf = Join-Path (Split-Path -Parent $compiler) 'WPF'
$wpfAssemblies = foreach ($name in 'WindowsBase.dll', 'PresentationCore.dll', 'PresentationFramework.dll') {
    (Get-Item -LiteralPath (Join-Path $wpf $name)).FullName
}
$references = @('System.dll', 'System.Drawing.dll', 'System.Windows.Forms.dll') + $wpfAssemblies + $assemblies
New-Item -ItemType Directory -Path $output -Force | Out-Null
$dll = Join-Path $output 'CodexAutoCAD.dll'
$compilerArgs = @('/nologo', '/target:library', '/platform:x64', '/optimize+', '/codepage:65001', "/out:$dll")
$compilerArgs += $references | ForEach-Object { "/reference:$_" }
$compilerArgs += Join-Path $PSScriptRoot 'CodexAutoCAD.cs'
& $compiler @compilerArgs
if ($LASTEXITCODE -ne 0) { throw 'AutoCAD plug-in compilation failed.' }
Get-FileHash -LiteralPath $dll -Algorithm SHA256
