from flask import render_template, request, jsonify
from app import app, db
from models import Subscriber
import re

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400

    existing_subscriber = Subscriber.query.filter_by(email=email).first()
    if existing_subscriber:
        return jsonify({'success': False, 'message': 'Email already subscribed'}), 400

    new_subscriber = Subscriber(email=email)
    db.session.add(new_subscriber)
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Successfully subscribed!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500
