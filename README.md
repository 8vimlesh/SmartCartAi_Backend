# SmartCart.AI - Backend

**SmartCart.AI** is an intelligent e-commerce backend that powers personalized product recommendations, smart search, and real-time price monitoring.

## 🚀 Features

- **AI-Powered Recommendations**: Machine learning models provide personalized product suggestions
- **Smart Search**: Advanced search with semantic understanding and filtering
- **Price Monitoring**: Track price history and get notified of price drops
- **Web Scraping**: Real-time data extraction from e-commerce websites
- **User Authentication**: Secure JWT-based authentication
- **RESTful API**: Clean and organized API endpoints

## 🛠️ Tech Stack

- **Language**: Python 3.13
- **Framework**: Flask
- **Database**: SQLite (development), PostgreSQL (production)
- **AI/ML**: Scikit-learn, Pandas, NumPy
- **Web Scraping**: BeautifulSoup4, Requests
- **Authentication**: Flask-JWT-Extended
- **Environment**: Python Virtual Environment

## 📂 Project Structure

```
backend/
├── app/
│   ├── routes/            # API endpoints
│   │   ├── auth.py
│   │   ├── products.py
│   │   ├── search.py
│   │   └── recommendations.py
│   ├── services/          # Business logic
│   │   ├── ai_engine.py
│   │   ├── scraper.py
│   │   └── database.py
│   ├── models/            # Database models
│   ├── utils/             # Utility functions
│   ├── app.py             # Application entry point
│   └── config.py          # Configuration
├── data/                  # Data files
├── models/                # Trained ML models
├── .env                   # Environment variables
├── requirements.txt       # Dependencies
└── README.md              # Project documentation
```

## ⚙️ Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   ```bash
   python app/database.py
   ```

5. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=sqlite:///smartcart.db
   JWT_SECRET_KEY=your-secret-key
   ```

6. **Run the development server**
   ```bash
   python app/app.py
   ```

## 🏃 Usage

- **Start development server**: `python app/app.py`
- **API Base URL**: `http://localhost:5000/api`
- **Documentation**: Access Swagger UI at `http://localhost:5000/apidocs`

## 🧪 Testing

Run the test suite to ensure application stability:

```bash
python -m unittest discover tests
```

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user profile

### Products
- `GET /api/products` - Get all products
- `GET /api/products/:id` - Get product by ID

### Search
- `GET /api/search` - Search products with filters

### Recommendations
- `GET /api/recommendations` - Get personalized recommendations

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For issues or questions, please open an issue on the GitHub repository.

---

**SmartCart.AI** - Intelligent Shopping, Simplified
