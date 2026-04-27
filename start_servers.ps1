Write-Host "Starting ClinicVoice AI Full Stack..." -ForegroundColor Green

# Start the Python Backend
Write-Host "Starting Python Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\backend'; py -m uvicorn main:app --reload --port 8000"

# Start the Node.js API Gateway
Write-Host "Starting API Gateway..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\api-gateway'; node index.js"

# Start the React Frontend
Write-Host "Starting React Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\frontend'; npm run dev"

Write-Host "All services are starting up!" -ForegroundColor Green
Write-Host "Frontend:    http://localhost:5173"
Write-Host "API Gateway: http://localhost:3001"
Write-Host "Python AI:   ws://localhost:8000/ws"

