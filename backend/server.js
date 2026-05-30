const express = require('express');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = 3000;
const JWT_SECRET = 'localeaks_super_secret_key_12345';

app.use(cors());
app.use(express.json());

// Simulation de base de données en mémoire (un simple tableau)
const usersDatabase = [];



// INSCRIPTION (register)

app.post('/register', async (req, res) => {
    try {
        const { username, email, password } = req.body;

        if (!username || !email || !password) {
            return res.status(400).json({ error: 'Tous les champs sont requis.' });
        }

        // Vérifier si l'email existe déjà dans le tableau
        const userExists = usersDatabase.find(user => user.email.toLowerCase() === email.toLowerCase());
        if (userExists) {
            return res.status(400).json({ error: 'Cet email est déjà enregistré.' });
        }

        // Hachage du mot de passe
        const hashedPassword = await bcrypt.hash(password, 10);

        // Ajout dans notre tableau
        usersDatabase.push({
            username: username,
            email: email.toLowerCase(),
            passwordHash: hashedPassword
        });

        return res.status(201).json({ message: 'Compte créé avec succès !' });

    } catch (error) {
        return res.status(500).json({ error: 'Erreur interne du serveur.' });
    }
});



// CONNEXION (login)



app.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        if (!email || !password) {
            return res.status(400).json({ error: 'Email et mot de passe requis.' });
        }

        // Chercher l'utilisateur dans le tableau
        const user = usersDatabase.find(user => user.email === email.toLowerCase());
        if (!user) {
            return res.status(401).json({ error: 'Identifiants incorrects.' });
        }

        // Vérifier le mot de passe
        const isPasswordValid = await bcrypt.compare(password, user.passwordHash);
        if (!isPasswordValid) {
            return res.status(401).json({ error: 'Identifiants incorrects.' });
        }

        // Générer le token
        const token = jwt.sign(
            { username: user.username },
            JWT_SECRET,
            { expiresIn: '24h' }
        );

        return res.status(200).json({
            message: 'Connexion réussie',
            token: token
        });

    } catch (error) {
        return res.status(500).json({ error: 'Erreur interne du serveur.' });
    }
});

app.listen(PORT, () => {
    console.log(` Serveur LocaLeaks actif sur : http://localhost:${PORT}`);
});