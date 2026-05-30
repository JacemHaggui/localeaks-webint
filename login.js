document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const messageDiv = document.getElementById('message');

    fetch('http://localhost:3000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, password: password })
    })
    .then(response => {
        if (!response.ok) throw new Error('Identifiants incorrects');
        return response.json();
    })
    .then(data => {
        messageDiv.textContent = "Connexion réussie ! Redirection...";
        messageDiv.style.color = "green";
        
        localStorage.setItem("token", data.token); 
        
        setTimeout(() => {
            window.location.href = 'index.html'; 
        }, 1000);
    })
    .catch(error => {
        messageDiv.textContent = error.message;
        messageDiv.style.color = "red";
    });
});