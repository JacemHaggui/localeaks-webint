
# LocaLeaks-webint

  

## Description

  

LocaLeaks is a web application for students looking for information about apartments and landlords.

## Online website

You can find the website at https://localeaks.org/

  

## Project Structure

```text
localeaks-webint/
|-- DataBase/                         SQL files used to create and maintain the database.
|   |-- AutoUpdates.sql               SQL automation/update script.
|   |-- CreateLocaLeaksDatabase.sql   Main database creation script.
|   `-- auto_update_deletion.sql      SQL script for automatic deletion/update behavior.
|-- frontend/                         Static website files shown to users in the browser.
|   |-- LocaLeaksFavicon.png          Browser tab icon.
|   |-- LocaLeaksLogo.jpg             LocaLeaks logo image.
|   |-- add_apartment.html            Page for adding a new apartment.
|   |-- address.html                  Address search page.
|   |-- apartment.html                Apartment detail page.
|   |-- config.js                     Stores the backend API URL used by the frontend.
|   |-- header.js                     Shared navigation/header behavior.
|   |-- index.html                    Homepage.
|   |-- landlord.html                 Landlord detail page.
|   |-- leave_review.html             Page for leaving an apartment review.
|   |-- leave_review_landlord.html    Page for leaving a landlord review.
|   |-- login.html                    Login page.
|   |-- profile.html                  User profile/account page.
|   |-- register.html                 Account creation page.
|   |-- results.html                  Search results page.
|   |-- script.js                     Main frontend JavaScript logic.
|   |-- style.css                     Main website styling.
|   `-- verify.html                   Email verification page.
|-- localeaks-backend/                FastAPI backend and database access code.
|   |-- app.py                        Main API server with routes and authentication.
|   |-- db.py                         Database connection setup.
|   |-- email_utils.py                Email sending helper for verification codes.
|   |-- queries.py                    SQL query helper functions used by the API.
|   `-- requirements.txt              Python dependencies for the backend.
|-- README.md                         Main project documentation.
```
  

## Usage

  

Users can:

  

- Create an account (use a real email and a password you will remember as you will need to verify your email and use the password to log in after creating an account)

- Log in

- Search for apartments by address

- View apartment and landlord information

- Add reviews

- Delete their account

 

