from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import jwt
from functools import wraps

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from services.scraper import scrape_all

app = Flask(__name__, static_folder='frontend-react/dist', static_url_path='')
CORS(app)

app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'super-secret-key-12345')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2:
                token = parts[1]
        
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
            
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            from services.database import get_user_by_id
            current_user = get_user_by_id(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found!'}), 401
        except Exception as e:
            return jsonify({'error': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

# ── Auth endpoints ─────────────────────────
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', 'User')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
        
    from services.database import create_user
    user_id = create_user(email, password, name)
    if not user_id:
        return jsonify({'error': 'User already exists'}), 400
        
    return jsonify({'status': 'ok', 'message': 'User created successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
        
    from services.database import verify_user
    user = verify_user(email, password)
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
        
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.utcnow() + timedelta(days=7)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    return jsonify({
        'status': 'ok',
        'token': token,
        'user': user
    })

@app.route('/api/user/profile', methods=['GET'])
@token_required
def profile(current_user):
    from services.database import get_user_alerts
    alerts = get_user_alerts(current_user['id'])
    return jsonify({'user': current_user, 'alerts': alerts})

# ── Frontend pages ─────────────────────────
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    dist_dir = os.path.join(app.root_path, 'frontend-react', 'dist')
    index_file = os.path.join(dist_dir, 'index.html')

    if os.path.exists(index_file):
        if path and os.path.exists(os.path.join(dist_dir, path)):
            return send_from_directory(dist_dir, path)
        return send_from_directory(dist_dir, 'index.html')

    return jsonify({
        'status': 'running',
        'message': 'Backend is running, but frontend build not found. Please build your React app or serve the frontend separately.'
    })

# ── Compare prices ─────────────────────────
@app.route('/api/compare')
def compare():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Query required'}), 400

    print(f'\n/api/compare?q={query}')
    results = scrape_all(query)

    if not results:
        from services.database import get_product_fallback
        fallback_data = get_product_fallback(query)
        
        if fallback_data:
            print(f"  [FALLBACK] Retrieved {fallback_data['name']} from database.")
            results = fallback_data['platforms']
            return jsonify({
                'query': query,
                'name': fallback_data['name'],
                'image': fallback_data.get('image'),
                'mrp': int(max([r['price'] for r in results]) * 1.25) if results else 0,
                'platforms': results,
                'scraped_at': datetime.now().isoformat(),
                'source': 'database_cache'
            })
            
        else:
            # COMPLETELY MOCK SIMULATION ENGINE
            import random
            print(f"  [MOCK ENGINE] Simulating data for '{query}'...")
            
            base_price = random.randint(1500, 35000)
            platforms_to_mock = [
                {'id': 'amazon', 'name': 'Amazon'},
                {'id': 'flipkart', 'name': 'Flipkart'},
                {'id': 'croma', 'name': 'Croma'},
                {'id': 'nykaa', 'name': 'Nykaa'}
            ]
            
            results = []
            for plat in platforms_to_mock:
                variance = random.uniform(0.9, 1.1) 
                results.append({
                    'platform': plat['id'],
                    'name': query,
                    'price': int(base_price * variance),
                    'rating': round(random.uniform(3.8, 4.9), 1),
                    'discount': random.randint(5, 30),
                    'url': '#',
                    'image': 'https://via.placeholder.com/200/0d0d0d/ffffff?text=SmartCart'
                })
                
            mrp = int(max([r['price'] for r in results]) * 1.25)
            for r in results:
                r['mrp'] = mrp
                
            best_name = query
            best_image = results[0]['image']
            
            # Save the fake data so the database respects it!
            from services.database import save_product, save_price
            save_product(best_name, 'Mock Product', best_image)
            for r in results:
                save_price(best_name, r['platform'], r['price'], r['rating'], r['url'])

            return jsonify({
                'query': query,
                'name': best_name,
                'image': best_image,
                'mrp': mrp,
                'platforms': results,
                'scraped_at': datetime.now().isoformat(),
                'source': 'mock_simulation'
            })

    prices = [r['price'] for r in results if r.get('price')]
    mrp = int(max(prices) * 1.25) if prices else 0

    for r in results:
        if r.get('price') and mrp > 0:
            r['discount'] = max(0, round((1 - r['price'] / mrp) * 100))
        if not r.get('mrp') or r['mrp'] == r.get('price'):
            r['mrp'] = mrp

    best_image = next((r['image'] for r in results if r.get('image')), None)
    best_name  = next((r['name'] for r in results if r.get('name') and r['name'] != query), query)

    try:
        from services.database import save_product, save_price, check_alerts
        save_product(best_name, 'Product', best_image)
        for r in results:
            save_price(best_name, r['platform'], r['price'], r.get('rating'), r.get('url'))
            
            # PASSIVE EVALUATION: Check if this live price hits anyone's alert
            if r.get('price'):
                check_alerts(best_name, r['platform'], r['price'])
                
    except Exception as e:
        print(f'DB save error (non-fatal): {e}')

    return jsonify({
        'query':      query,
        'name':       best_name,
        'image':      best_image,
        'mrp':        mrp,
        'platforms':  results,
        'scraped_at': datetime.now().isoformat()
    })

# ── Price history ───────────────────────────
@app.route('/api/history')
def history():
    product  = request.args.get('product', '').strip()
    platform = request.args.get('platform')
    days     = int(request.args.get('days', 30))
    if not product:
        return jsonify({'error': 'product param required'}), 400
    try:
        from services.database import get_price_history
        records = get_price_history(product, platform, days)
        return jsonify({'product': product, 'history': records})
    except Exception as e:
        return jsonify({'product': product, 'history': []})

# ── AI Prediction ─────────────────────────
@app.route('/api/predict', methods=['GET'])
def get_prediction():
    product = request.args.get('product', '').strip()
    if not product:
        return jsonify({'error': 'product required'}), 400
        
    try:
        from services.database import get_price_history
        from services.ai_engine import predict_insights
        
        # Pull history from MongoDB
        history = get_price_history(product, days=30)
        
        # Run ML inference
        insights = predict_insights(history)
        
        if not insights:
            return jsonify({'error': 'Prediction engine failed to return insights'}), 500

        if "error" in insights:
            return jsonify({
                'error': 'Insufficient Data', 
                'details': insights['error'],
                'message': f"We need at least a few days of price history for '{product}' to generate AI insights."
            }), 400
            
        return jsonify(insights)
    except Exception as e:
        print(f"ML Error: {e}")
        return jsonify({'error': f'Machine Learning error: {str(e)}'}), 500

# ── Set alert ───────────────────────────────
@app.route('/api/alert', methods=['POST'])
def create_alert():
    data      = request.json or {}
    product   = data.get('product')
    platform  = data.get('platform')
    threshold = data.get('threshold')
    
    if not all([product, platform, threshold]):
        return jsonify({'error': 'product, platform, threshold required'}), 400
        
    # Optional auth check
    user_id = None
    if 'Authorization' in request.headers:
        parts = request.headers['Authorization'].split()
        if len(parts) == 2:
            try:
                decoded = jwt.decode(parts[1], app.config['SECRET_KEY'], algorithms=['HS256'])
                user_id = decoded['user_id']
            except:
                pass
                
    try:
        from services.database import set_alert
        set_alert(product, platform, threshold, data.get('email'), user_id)
    except Exception as e:
        print(f'Alert save error: {e}')
    return jsonify({'status': 'ok'})

# ── Tracked products ────────────────────────
@app.route('/api/products')
def products():
    try:
        from services.database import get_all_tracked_products
        return jsonify(get_all_tracked_products())
    except Exception as e:
        return jsonify([])

# ── Reviews GET ─────────────────────────────
@app.route('/api/reviews', methods=['GET'])
def get_reviews_api():
    product = request.args.get('product', '').strip()
    if not product:
        return jsonify({'error': 'product required'}), 400
    try:
        from services.database import get_reviews
        reviews = get_reviews(product)
        return jsonify({'product': product, 'reviews': reviews})
    except Exception as e:
        return jsonify({'product': product, 'reviews': []})

# ── Reviews POST ────────────────────────────
@app.route('/api/reviews', methods=['POST'])
def post_review():
    data = request.json or {}
    product  = data.get('product', '').strip()
    name     = data.get('name', '').strip()
    rating   = data.get('rating')
    title    = data.get('title', '').strip()
    body     = data.get('body', '').strip()
    platform = data.get('platform', '')
    verified = data.get('verified', False)
    tags     = data.get('tags', [])

    if not all([product, name, rating, title, body]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        from services.database import save_review
        review_id = save_review(product, name, rating, title, body, platform, verified, tags)
        return jsonify({'status': 'ok', 'id': review_id})
    except Exception as e:
        print(f'Review save error: {e}')
        return jsonify({'status': 'ok', 'id': str(datetime.now().timestamp())})

# ── Helpful vote ────────────────────────────
@app.route('/api/reviews/helpful', methods=['POST'])
def helpful():
    data = request.json or {}
    try:
        from services.database import mark_helpful
        mark_helpful(data.get('product'), data.get('id'))
    except Exception as e:
        pass
    return jsonify({'status': 'ok'})

# ── Health check ────────────────────────────
@app.route('/api/health')
def health():
    return jsonify({'status': 'running', 'time': datetime.now().isoformat()})

@app.errorhandler(404)
def handle_404(error):
    return jsonify({'error': 'Not found', 'path': request.path}), 404

@app.errorhandler(500)
def handle_500(error):
    return jsonify({'error': 'Server error', 'message': str(error)}), 500

if __name__ == '__main__':
    port  = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True') == 'True'
    print(f'\nSmartCart running at http://0.0.0.0:{port}\n')
    app.run(host='0.0.0.0', debug=debug, port=port)