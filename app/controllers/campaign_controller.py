from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.campaign import Campaign

campaign_bp = Blueprint('campaigns', __name__)

@campaign_bp.route('/campaigns')
@campaign_bp.route('/dashboard/campaigns')
@login_required
def list_campaigns():
    campaigns = Campaign.query.filter_by(organization_id=current_user.organization_id).all()
    return render_template('dashboard/campaigns.html', campaigns=campaigns)

@campaign_bp.route('/campaigns/create')
@campaign_bp.route('/dashboard/campaigns/create')
@login_required
def create_campaign():
    return render_template('dashboard/campaigns/create.html')

@campaign_bp.route('/campaigns/<campaign_id>')
@campaign_bp.route('/dashboard/campaigns/<campaign_id>')
@login_required
def view_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('dashboard/campaigns/view.html', campaign=campaign)
