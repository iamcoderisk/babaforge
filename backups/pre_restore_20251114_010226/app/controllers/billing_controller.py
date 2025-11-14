from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.payment import PaymentMethod, Transaction
from app.models.pricing import Subscription, PricingPlan
from app.services.korapay import korapay
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

@billing_bp.route('/')
@login_required
def index():
    """Billing dashboard"""
    org = current_user.organization
    
    if not org:
        flash('Organization not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get current subscription
    subscription = Subscription.query.filter_by(
        organization_id=org.id,
        status='active'
    ).first()
    
    # Get payment methods
    payment_methods = PaymentMethod.query.filter_by(
        organization_id=org.id,
        is_active=True
    ).order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc()).all()
    
    # Get transaction history
    transactions = Transaction.query.filter_by(
        organization_id=org.id
    ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Get available plans
    plans = PricingPlan.query.filter_by(is_active=True).order_by(PricingPlan.display_order).all()
    
    return render_template('billing/index.html',
                         org=org,
                         subscription=subscription,
                         payment_methods=payment_methods,
                         transactions=transactions,
                         plans=plans,
                         korapay_public_key=os.environ.get('KORAPAY_PUBLIC_KEY', ''))

@billing_bp.route('/subscribe/<plan_id>', methods=['POST'])
@login_required
def subscribe(plan_id):
    """Subscribe to a plan"""
    try:
        org = current_user.organization
        plan = PricingPlan.query.get(plan_id)
        
        if not plan:
            return jsonify({'success': False, 'error': 'Plan not found'}), 404
        
        # Check if already subscribed
        existing = Subscription.query.filter_by(
            organization_id=org.id,
            status='active'
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'You already have an active subscription. Please cancel it first.'
            }), 400
        
        # Create transaction
        transaction = Transaction(
            organization_id=org.id,
            amount=plan.price,
            currency='USD'
        )
        db.session.add(transaction)
        db.session.flush()
        
        # Initialize payment with Korapay
        result = korapay.initialize_transaction(
            amount=float(plan.price),
            email=current_user.email,
            reference=transaction.reference,
            metadata={
                'organization_id': org.id,
                'plan_id': plan_id,
                'subscription': True
            }
        )
        
        if result.get('status'):
            transaction.korapay_reference = result.get('data', {}).get('reference')
            transaction.response_data = result
            db.session.commit()
            
            return jsonify({
                'success': True,
                'checkout_url': result.get('data', {}).get('checkout_url'),
                'reference': transaction.reference
            })
        else:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': result.get('message', 'Payment initialization failed')
            }), 400
        
    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@billing_bp.route('/verify')
@login_required
def verify_payment():
    """Verify payment after redirect"""
    reference = request.args.get('reference')
    
    if not reference:
        flash('Invalid payment reference', 'danger')
        return redirect(url_for('billing.index'))
    
    try:
        # Get transaction
        transaction = Transaction.query.filter_by(reference=reference).first()
        
        if not transaction:
            flash('Transaction not found', 'danger')
            return redirect(url_for('billing.index'))
        
        # Verify with Korapay
        result = korapay.verify_transaction(transaction.korapay_reference or reference)
        
        if result.get('status') and result.get('data', {}).get('status') == 'success':
            # Update transaction
            transaction.status = 'success'
            transaction.paid_at = datetime.utcnow()
            transaction.response_data = result
            
            # Create or update subscription
            metadata = result.get('data', {}).get('metadata', {})
            plan_id = metadata.get('plan_id')
            
            if plan_id:
                plan = PricingPlan.query.get(plan_id)
                
                # Create subscription
                subscription = Subscription(
                    organization_id=transaction.organization_id,
                    plan_id=plan_id
                )
                subscription.status = 'active'
                subscription.period_start = datetime.utcnow()
                subscription.period_end = datetime.utcnow() + timedelta(days=30)
                subscription.next_billing_date = subscription.period_end
                subscription.last_payment_date = datetime.utcnow()
                
                db.session.add(subscription)
                transaction.subscription_id = subscription.id
            
            # Save authorization if available
            auth_code = result.get('data', {}).get('authorization', {}).get('authorization_code')
            if auth_code:
                payment_method = PaymentMethod(organization_id=transaction.organization_id)
                payment_method.authorization_code = auth_code
                payment_method.card_type = result.get('data', {}).get('authorization', {}).get('card_type')
                payment_method.last4 = result.get('data', {}).get('authorization', {}).get('last4')
                payment_method.exp_month = result.get('data', {}).get('authorization', {}).get('exp_month')
                payment_method.exp_year = result.get('data', {}).get('authorization', {}).get('exp_year')
                payment_method.bank = result.get('data', {}).get('authorization', {}).get('bank')
                payment_method.is_default = True
                
                db.session.add(payment_method)
            
            db.session.commit()
            
            flash('Payment successful! Your subscription is now active.', 'success')
        else:
            transaction.status = 'failed'
            transaction.response_data = result
            db.session.commit()
            
            flash('Payment verification failed. Please try again.', 'danger')
        
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        flash(f'Error verifying payment: {e}', 'danger')
    
    return redirect(url_for('billing.index'))

@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Korapay webhook"""
    try:
        data = request.get_json()
        
        # Verify webhook signature (implement based on Korapay docs)
        # signature = request.headers.get('X-Korapay-Signature')
        
        event = data.get('event')
        reference = data.get('data', {}).get('reference')
        
        if event == 'charge.success':
            transaction = Transaction.query.filter_by(korapay_reference=reference).first()
            
            if transaction and transaction.status == 'pending':
                transaction.status = 'success'
                transaction.paid_at = datetime.utcnow()
                transaction.response_data = data
                db.session.commit()
                
                logger.info(f"Webhook: Transaction {reference} marked as success")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@billing_bp.route('/payment-method/<method_id>/set-default', methods=['POST'])
@login_required
def set_default_payment_method(method_id):
    """Set default payment method"""
    try:
        org = current_user.organization
        
        # Unset all defaults
        PaymentMethod.query.filter_by(organization_id=org.id).update({'is_default': False})
        
        # Set new default
        method = PaymentMethod.query.filter_by(id=method_id, organization_id=org.id).first()
        if method:
            method.is_default = True
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Default payment method updated'})
        
        return jsonify({'success': False, 'error': 'Payment method not found'}), 404
        
    except Exception as e:
        logger.error(f"Set default payment method error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@billing_bp.route('/payment-method/<method_id>/remove', methods=['POST'])
@login_required
def remove_payment_method(method_id):
    """Remove payment method"""
    try:
        org = current_user.organization
        
        method = PaymentMethod.query.filter_by(id=method_id, organization_id=org.id).first()
        if method:
            method.is_active = False
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Payment method removed'})
        
        return jsonify({'success': False, 'error': 'Payment method not found'}), 404
        
    except Exception as e:
        logger.error(f"Remove payment method error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@billing_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel active subscription"""
    try:
        org = current_user.organization
        
        subscription = Subscription.query.filter_by(
            organization_id=org.id,
            status='active'
        ).first()
        
        if subscription:
            subscription.status = 'cancelled'
            db.session.commit()
            
            flash('Subscription cancelled successfully', 'success')
            return jsonify({'success': True, 'message': 'Subscription cancelled'})
        
        return jsonify({'success': False, 'error': 'No active subscription found'}), 404
        
    except Exception as e:
        logger.error(f"Cancel subscription error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
