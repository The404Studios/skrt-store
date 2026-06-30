"""
SKRT Digital Store - Payment Server
Flask + Stripe Checkout integration
"""
import os
import json
import stripe
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/api/options', methods=['OPTIONS'])
@app.route('/api/create-checkout-session', methods=['OPTIONS'])
def handle_options():
    return '', 204

# Products catalog
PRODUCTS = {
    'prod_1': {'name': 'Social Media Growth Kit', 'price': 2900, 'desc': '30+ templates & growth strategies'},
    'prod_2': {'name': 'E-Commerce Starter Pack', 'price': 4900, 'desc': 'Shopify theme + product research guide'},
    'prod_3': {'name': 'AI Prompt Master Collection', 'price': 1900, 'desc': '500+ tested ChatGPT prompts'},
    'prod_4': {'name': 'Faceless YouTube Empire', 'price': 3900, 'desc': 'Script templates & niche ideas'},
    'prod_5': {'name': 'Notion Life OS Template', 'price': 2400, 'desc': 'All-in-one productivity dashboard'},
    'prod_6': {'name': 'Resume & Portfolio Bundle', 'price': 1500, 'desc': '5 premium resume templates'},
    'prod_7': {'name': 'TikTok Shop Blueprint', 'price': 3400, 'desc': 'Scale your TikTok Shop guide'},
    'prod_8': {'name': 'Digital Marketing Vault', 'price': 2700, 'desc': '200+ ad copies & funnel templates'},
}

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_placeholder')
YOUR_DOMAIN = os.environ.get('DOMAIN', 'http://localhost:5000')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/products')
def get_products():
    return jsonify(PRODUCTS)

@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        line_items = []
        for item_id in items:
            if item_id in PRODUCTS:
                p = PRODUCTS[item_id]
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': p['name'], 'description': p['desc']},
                        'unit_amount': p['price'],
                    },
                    'quantity': 1,
                })
        
        if not line_items:
            return jsonify({'error': 'No valid items'}), 400
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/index.html',
            shipping_address_collection={'allowed_countries': ['US', 'CA', 'GB', 'AU', 'DE', 'FR']},
        )
        return jsonify({'url': session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        )
    except Exception:
        return 'Invalid signature', 400
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        items = stripe.checkout.Session.list_line_items(session['id'], limit=100)
        product_names = [item.description for item in items.data]
        print(f"ORDER COMPLETE: {product_names} - ${session['amount_total']/100:.2f} - {session['customer_details']['email']}")
    
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
