from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import string
import random
import os
import logging

app = Flask(__name__)

# Set up logging to see any errors
logging.basicConfig(level=logging.DEBUG)

# Path to store the SQLite database in a writable directory for Vercel
DATABASE = '/tmp/database.db'

# Function to generate a random short URL
def generate_short_url():
    characters = string.ascii_letters + string.digits
    short_url = ''.join(random.choice(characters) for _ in range(6))
    return short_url

# Function to initialize the database if it doesn't exist
def init_db():
    try:
        if not os.path.exists(DATABASE):
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            # Create the URLs table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_url TEXT NOT NULL,
                    short_url TEXT NOT NULL
                )
            ''')
            conn.commit()
            conn.close()
            app.logger.debug("Database initialized")
        else:
            app.logger.debug("Database already exists")
    except Exception as e:
        app.logger.error(f"Error initializing the database: {e}")

# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def home():
    try:
        if request.method == 'POST':
            original_url = request.form.get('url')

            if not original_url:
                return "Please provide a valid URL", 400

            # Generate a short URL
            short_url = generate_short_url()

            # Save original and short URL in the database
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO urls (original_url, short_url) VALUES (?, ?)", (original_url, short_url))
            conn.commit()
            conn.close()

            # Render the short URL
            return render_template('index.html', short_url=request.host_url + short_url)
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error in home route: {e}")
        return "Internal Server Error", 500

# Route to redirect the short URL to the original URL
@app.route('/<short_url>')
def redirect_url(short_url):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT original_url FROM urls WHERE short_url = ?", (short_url,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return redirect(result[0])
        else:
            return "URL not found!", 404
    except Exception as e:
        app.logger.error(f"Error in redirect route: {e}")
        return "Internal Server Error", 500

# Main entry point for the app
if __name__ == '__main__':
    # Initialize the database when the app starts
    init_db()
    # Run the app with debug mode
    app.run(debug=True)
