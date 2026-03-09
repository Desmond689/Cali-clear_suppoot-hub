Set objShell = CreateObject("WScript.Shell")

' Install dependencies, create tables, seed the database, and start the Flask server in the background
objShell.Run "cmd /c cd /d c:\Users\DESMOND\Desktop\cali clear\ecommerce-site\backend && pip install -r requirements.txt && python -c ""from app import app, db; with app.app_context(): db.create_all(); from database.seed import seed_data; seed_data()"" && python app.py", 0, False

WScript.Sleep 15000 ' Wait 15 seconds for server to start and seed

' Function to run curl and capture output
Function RunCurl(url)
    Set execObj = objShell.Exec("cmd /c curl " & url)
    Do While Not execObj.StdOut.AtEndOfStream
        WScript.Echo execObj.StdOut.ReadLine()
    Loop
    Do While Not execObj.StdErr.AtEndOfStream
        WScript.Echo execObj.StdErr.ReadLine()
    Loop
End Function

' Test API endpoints
WScript.Echo "Testing /api/products:"
RunCurl "http://localhost:5000/api/products"

WScript.Echo "Testing /api/products/1:"
RunCurl "http://localhost:5000/api/products/1"

WScript.Echo "Testing /api/categories:"
RunCurl "http://localhost:5000/api/categories"

WScript.Echo "Testing /api/featured:"
RunCurl "http://localhost:5000/api/featured"

' Note: Server is running in background. Close the CMD window running python app.py to stop it.
