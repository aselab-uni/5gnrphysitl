param(
    [string]$InputFile = "docs\REAL_5G_SYSTEM_VS_PROJECT.md",
    [string]$OutputTex = "docs\REAL_5G_SYSTEM_VS_PROJECT.tex",
    [string]$OutputPdf = "docs\REAL_5G_SYSTEM_VS_PROJECT.pdf"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pandoc = "C:\Users\tuan.dotrong\AppData\Local\Pandoc\pandoc.exe"
$xelatex = "C:\Users\tuan.dotrong\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe"
$metadata = Join-Path $repoRoot "docs\latex\real_5g_report_metadata.yaml"
$filter = Join-Path $repoRoot "docs\latex\mermaid_placeholder.lua"
$inputPath = Join-Path $repoRoot $InputFile
$texPath = Join-Path $repoRoot $OutputTex
$pdfPath = Join-Path $repoRoot $OutputPdf

if (-not (Test-Path $pandoc)) {
    throw "pandoc.exe not found at $pandoc"
}

if (-not (Test-Path $xelatex)) {
    throw "xelatex.exe not found at $xelatex"
}

if (-not (Test-Path $inputPath)) {
    throw "Input Markdown file not found: $inputPath"
}

& $pandoc `
    $inputPath `
    "--from=markdown+pipe_tables+grid_tables+fenced_divs+fenced_code_blocks+backtick_code_blocks" `
    "--standalone" `
    "--metadata-file=$metadata" `
    "--lua-filter=$filter" `
    "--resource-path=$repoRoot" `
    "--output=$texPath"

& $pandoc `
    $inputPath `
    "--from=markdown+pipe_tables+grid_tables+fenced_divs+fenced_code_blocks+backtick_code_blocks" `
    "--standalone" `
    "--metadata-file=$metadata" `
    "--lua-filter=$filter" `
    "--resource-path=$repoRoot" `
    "--pdf-engine=$xelatex" `
    "--output=$pdfPath"

Write-Host "Generated:"
Write-Host " - $texPath"
Write-Host " - $pdfPath"
