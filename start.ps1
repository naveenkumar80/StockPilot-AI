<#
.SYNOPSIS
    Starts both StockPilot AI FastAPI backend and Next.js frontend in one command.
.EXAMPLE
    .\start.ps1
    .\start.ps1 --open
#>
param (
    [switch]$Open,
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$arguments = @()
if ($Open) { $arguments += "--open" }
if ($BackendPort -ne 8000) { $arguments += "--backend-port", $BackendPort }
if ($FrontendPort -ne 3000) { $arguments += "--frontend-port", $FrontendPort }

python "$scriptDir\start.py" @arguments

