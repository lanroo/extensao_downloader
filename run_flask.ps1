# Executa o servidor Flask
flask run

# Remove a pasta __pycache__ após a execução do Flask
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
