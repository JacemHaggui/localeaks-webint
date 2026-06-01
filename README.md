# localeaks-webint


Required librairies and packages :  

install Node js latest version on https://nodejs.org/en/download  

If you don't have the permissions to execute local scripts in windows, run in a administrator powershell terminal :  
Set-ExecutionPolicy Restricted -Scope CurrentUser  

Then execute :  
npm init -y  
npm install express cors  
npm install bcrypt (for the hashing function to handle passwords. By precaution, enter a dummy password)  
npm install express cors jsonwebtoken (express : creates the server, cors : security module enabling the browser to send fetch request to our local server, jsonwebtoken : generates the token to tell our server that the connexion is safe)  

launch the server with :  
python -m http.server  

in backend/, launch the node server with :  
node server.js  

As long as server.js is running, you can create accounts, connect, disconnect...  
emails, usernames and passwords are stored by the server.js in a temporary list to simulate a real database  
When server.js is closed, everything is erased  

