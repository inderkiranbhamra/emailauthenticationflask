from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import yagmail
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import secrets
import os

app = Flask(__name__)

# Set the secret key for the session
app.secret_key = 'inderkiran@24'

# Email configuration
sender_email = 'inderkiran20233@gmail.com'  # replace with your email
app_password = 'krhu cexv lyue dmnz'  # replace with your generated app password

# Google Sheets configuration
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('bgmi-registration-e1d0ccd3b338.json', scope)
gc = gspread.authorize(credentials)
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1EcrnzJ5Po5jSnEZTMxOpNNFZX01lkXdR6S1yG-4ownU/edit#gid=0'
sh = gc.open_by_url(spreadsheet_url)
worksheet = sh.sheet1  # Assuming you are working with the first sheet

# Dictionary to store email verification tokens
email_tokens = {}


# Function to generate a random token
def generate_token():
    return secrets.token_hex(16)


# Function to generate an authentication link with token
def generate_auth_link(token):
    link = f'https://emailauthenticationflask.vercel.app/verify/{token}'
    # Replace spaces with underscores
    link = link.replace(' ', '_')
    return link

# Route to handle form submission and send authentication email
@app.route('/send_email', methods=['POST'])
def send_email():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form['email']
        uid = request.form.get('uid')
        team_name = request.form.get('team_name')

        token = generate_token()
        email_tokens[email] = token

        # Construct authentication link with all required parameters
        auth_link = generate_auth_link(token) + f'?username={username}&uid={uid}&team_name={team_name}'

        subject = 'Authentication Link'
        body = f'Click on the following link to authenticate: {auth_link}'

        # Create yagmail SMTP client
        yag = yagmail.SMTP(sender_email, app_password)

        # Send the email
        yag.send(to=email, subject=subject, contents=body)

        return redirect(url_for('email_sent'))


# Route to inform user that email has been sent
@app.route('/email_sent')
def email_sent():
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email_sent.html'))


# Route to handle verification
@app.route('/verify/<token>', methods=['GET'])
def verify(token):
    if token in email_tokens.values():
        # Authentication successful, store data into Google Sheets
        email = [key for key, value in email_tokens.items() if value == token][0]
        del email_tokens[email]  # Remove token from dictionary after verification

        # Retrieve data from the query parameters
        username = request.args.get('username')
        uid = request.args.get('uid')
        team_name = request.args.get('team_name')

        # Check if all required parameters are present
        if username and uid and team_name:
            # Append new data to Google Sheets
            new_row = [username, email, uid, team_name]
            worksheet.append_row(new_row)

            return jsonify({'message': 'Authentication successful. Data stored into Google Sheets.'})
        else:
            return jsonify({'message': 'Missing parameters in the verification link.'}), 400
    else:
        return jsonify({'message': 'Invalid or expired verification link.'}), 400

