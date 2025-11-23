from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///phishing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'))
    target_emails = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    results = db.relationship('Result', backref='campaign', lazy=True)

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(300), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    campaigns = db.relationship('Campaign', backref='template', lazy=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    user_email = db.Column(db.String(200), nullable=False)
    clicked = db.Column(db.Boolean, default=False)
    submitted_data = db.Column(db.Boolean, default=False)
    reported = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    if Template.query.count() == 0:
        templates = [
            Template(name='Banking Alert', subject='Urgent: Verify Your Account',
                   body='Your account has been locked. Click here to verify.', category='finance'),
            Template(name='IT Security', subject='Password Reset Required',
                   body='System upgrade requires password reset.', category='security'),
            Template(name='HR Notice', subject='Updated Company Policy',
                   body='Review and acknowledge new policies.', category='hr'),
            Template(name='Shipping Notification', subject='Package Delivery Failed',
                   body='Update delivery address to receive package.', category='logistics'),
            Template(name='Payroll Update', subject='Action Required: Tax Forms',
                   body='Submit W-2 forms by end of month.', category='finance')
        ]
        db.session.add_all(templates)
        db.session.commit()

@app.route('/')
def index():
    total_campaigns = Campaign.query.count()
    total_clicks = Result.query.filter_by(clicked=True).count()
    total_reported = Result.query.filter_by(reported=True).count()
    return render_template('index.html', 
                         total_campaigns=total_campaigns,
                         total_clicks=total_clicks,
                         total_reported=total_reported)

@app.route('/campaigns')
def campaigns():
    all_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    templates = Template.query.all()
    return render_template('campaigns.html', campaigns=all_campaigns, templates=templates)

@app.route('/api/create_campaign', methods=['POST'])
def create_campaign():
    data = request.json
    campaign = Campaign(
        name=data['name'],
        template_id=data['template_id'],
        target_emails=data['target_emails'],
        status='active'
    )
    db.session.add(campaign)
    db.session.commit()
    return jsonify({'success': True, 'campaign_id': campaign.id})

@app.route('/results')
def results():
    all_results = Result.query.order_by(Result.timestamp.desc()).all()
    campaigns = Campaign.query.all()
    return render_template('results.html', results=all_results, campaigns=campaigns)

@app.route('/education')
def education():
    return render_template('education.html')

@app.route('/landing/<campaign_id>')
def landing(campaign_id):
    email = request.args.get('email', '')
    result = Result(campaign_id=campaign_id, user_email=email, clicked=True, timestamp=datetime.utcnow())
    db.session.add(result)
    db.session.commit()
    return render_template('landing.html', campaign_id=campaign_id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
