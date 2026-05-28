// header.js
document.addEventListener("DOMContentLoaded", () => {
    const header = document.getElementById("site-header");

    // Navbar HTML with clickable title
    header.innerHTML = `
        <div class="header-content">
            <img src="LocaLeaksLogo.jpg" alt="LocaLeaks Logo" class="site-logo">
            <h1>
                <a href="index.html" style="color: inherit; text-decoration: none;">LocaLeaks</a>
            </h1>
            <p>Donner du pouvoir aux étudiants. Responsabiliser les propriétaires.</p>
            <div class="nav-buttons"></div>
        </div>
    `;

    const navButtons = header.querySelector(".nav-buttons");

    const token = localStorage.getItem("token");

    if (token) {
        navButtons.innerHTML = `
            <button onclick="window.location.href='profile.html'">Profil</button>
            <button onclick="logout()">Déconnexion</button>
        `;
    } else {
        navButtons.innerHTML = `
            <button onclick="window.location.href='login.html'">Connexion</button>
            <button onclick="window.location.href='register.html'">Inscription</button>
        `;
    }
});

function logout() {
    localStorage.removeItem("token");
    window.location.reload();
}