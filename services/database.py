from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client[os.getenv('DB_NAME', 'smartcart')]

# Collections (like tables)
products_col    = db['products']
price_hist_col  = db['price_history']
alerts_col      = db['alerts']
users_col       = db['users']


def save_product(name, category, image_url):
    """Save or update a product in the database."""
    existing = products_col.find_one({'name': name})
    if existing:
        return str(existing['_id'])
    
    result = products_col.insert_one({
        'name': name,
        'category': category,
        'image': image_url,
        'created_at': datetime.now(),
        'last_updated': datetime.now()
    })
    return str(result.inserted_id)


def save_price(product_name, platform, price, rating=None, url=None):
    """Save a price snapshot to history."""
    if not price:
        return
    
    price_hist_col.insert_one({
        'product_name': product_name,
        'platform': platform,
        'price': price,
        'rating': rating,
        'url': url,
        'timestamp': datetime.now(),
        'date': datetime.now().strftime('%Y-%m-%d')
    })
    
    # Update last_updated on product
    products_col.update_one(
        {'name': product_name},
        {'$set': {'last_updated': datetime.now()}}
    )


def get_price_history(product_name, platform=None, days=30):
    """Get price history for a product."""
    query = {'product_name': product_name}
    if platform:
        query['platform'] = platform
    
    from datetime import timedelta
    since = datetime.now() - timedelta(days=days)
    query['timestamp'] = {'$gte': since}
    
    records = list(price_hist_col.find(
        query,
        {'_id': 0, 'platform': 1, 'price': 1, 'date': 1, 'timestamp': 1}
    ).sort('timestamp', 1))
    
    return records


def set_alert(product_name, platform, threshold_price, user_email=None, user_id=None):
    """Set a price alert."""
    query = {
        'product_name': product_name,
        'platform': platform
    }
    if user_id:
        query['user_id'] = user_id
    elif user_email:
        query['user_email'] = user_email
        
    if user_id or user_email:
        alerts_col.delete_many(query)
    
    alerts_col.insert_one({
        'product_name': product_name,
        'platform': platform,
        'threshold': threshold_price,
        'user_email': user_email,
        'user_id': user_id,
        'triggered': False,
        'created_at': datetime.now()
    })

def create_user(email, password, name):
    existing = users_col.find_one({'email': email})
    if existing:
        return None
    result = users_col.insert_one({
        'email': email,
        'password': generate_password_hash(password),
        'name': name,
        'created_at': datetime.now()
    })
    return str(result.inserted_id)

def verify_user(email, password):
    user = users_col.find_one({'email': email})
    if user and check_password_hash(user['password'], password):
        return {'id': str(user['_id']), 'email': user['email'], 'name': user.get('name', 'User')}
    return None

def get_user_by_id(user_id):
    from bson.objectid import ObjectId
    try:
        user = users_col.find_one({'_id': ObjectId(user_id)})
        if user:
            return {'id': str(user['_id']), 'email': user['email'], 'name': user.get('name', 'User')}
    except:
        pass
    return None

def get_user_alerts(user_id):
    """Get all alerts for a specific user"""
    return list(alerts_col.find(
        {'user_id': user_id},
        {'_id': 0}
    ).sort('created_at', -1))

def get_product_fallback(query):
    """Fallback to retrieve latest known prices if live scraping fails."""
    # Try to find a product matching the query
    import re
    # Escape query for regex
    safe_query = re.escape(query)
    product = products_col.find_one({'name': {'$regex': safe_query, '$options': 'i'}})
    
    if not product:
        return None
        
    product_name = product['name']
    
    # Get the latest price for each platform using MongoDB aggregation
    pipeline = [
        {'$match': {'product_name': product_name}},
        {'$sort': {'timestamp': -1}},
        {'$group': {
            '_id': '$platform',
            'price': {'$first': '$price'},
            'rating': {'$first': '$rating'},
            'url': {'$first': '$url'}
        }}
    ]
    
    historical = list(price_hist_col.aggregate(pipeline))
    if not historical:
        return None
        
    platforms = []
    for h in historical:
        platforms.append({
            'platform': h['_id'],
            'name': product_name,
            'price': h['price'],
            'rating': h.get('rating'),
            'url': h.get('url'),
            'source': 'database'
        })
        
    return {
        'name': product_name,
        'image': product.get('image'),
        'platforms': platforms
    }


def check_alerts(product_name, platform, current_price):
    """Check if any alerts should be triggered."""
    from .mailer import send_alert_email
    
    alerts = list(alerts_col.find({
        'product_name': product_name,
        'platform': platform,
        'triggered': False
    }))
    
    triggered = []
    for alert in alerts:
        if current_price <= alert['threshold']:
            alerts_col.update_one(
                {'_id': alert['_id']},
                {'$set': {'triggered': True, 'triggered_at': datetime.now()}}
            )
            
            email_target = alert.get('user_email')
            if not email_target and alert.get('user_id'):
                user = get_user_by_id(alert.get('user_id'))
                if user:
                    email_target = user['email']
                    
            if email_target:
                send_alert_email(email_target, product_name, platform, current_price, alert['threshold'])
                
            triggered.append(alert)
    
    return triggered


def get_all_tracked_products():
    """Get all products being tracked."""
    return list(products_col.find({}, {'_id': 0}))