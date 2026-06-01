document.getElementById('registerForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const messageDiv = document.getElementById('registerMessage');

    const sex = document.getElementById('sex').value;
    const age = document.getElementById('age').value;
    const INE = document.getElementById('INE').value;



    fetch('http://localhost:3000/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username, email: email, password: password, sex: sex, age: age, INE: INE })
    })
    .then(response => {
        if (!response.ok) throw new Error("Erreur lors de l'inscription");
        return response.json();
    })
    .then(data => {
        messageDiv.textContent = "Compte créé ! Redirection vers la page de connexion...";
        messageDiv.style.color = "green";
        
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
    })
    .catch(error => {
        console.error("Erreur détaillée :", error);
        messageDiv.textContent = "Impossible de contacter le serveur ou erreur technique.";
        messageDiv.style.color = "red";
    });
});
