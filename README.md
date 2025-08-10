# Long-Running Query Manager

A simple web application for managing and monitoring long-running database queries.

## 🚀 Features

- Execute long-running SQL queries against PostgreSQL
- Monitor active database sessions
- Create support tickets for problematic queries
- Simple web interface for query management

## 📁 Project Structure

```
tejas_ele/
├── backend/                    # FastAPI backend
│   ├── main.py                # Main API server
│   ├── database.py            # Database connection management
│   ├── setup_db.py            # Database initialization
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Static web files
│   ├── pages/                 # HTML pages
│   │   ├── index.html         # Main dashboard
│   │   └── ticket.html        # Ticket management
│   └── static/                # CSS, JavaScript, images
│       ├── script.js          # Main dashboard logic
│       ├── ticket.js          # Ticket page logic
│       └── style.css          # Styling
├── scripts/                    # Deployment scripts
└── start.py                   # Simple startup script
```

## 🏗️ Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL
- Virtual environment (.tejas)

### 1. Setup Database
```bash
# Make sure PostgreSQL is running
brew services start postgresql@14
createdb longquery_demo
```

### 2. Initialize Database with Sample Data
```bash
source .tejas/bin/activate
cd backend
python setup_db.py
```

### 3. Start the Application
```bash
# Option 1: Use the simple startup script
python start.py

# Option 2: Start manually
source .tejas/bin/activate
cd backend
python main.py
```

### 4. Access the Application
- **Main Dashboard**: http://localhost:8000
- **Ticket Management**: http://localhost:8000/tickets
- **API Documentation**: http://localhost:8000/docs

## 🎮 Usage

### Execute Long-Running Queries
1. Visit http://localhost:8000
2. Select from predefined slow queries or enter custom SQL
3. Monitor execution in real-time

### Create Support Tickets
1. Go to http://localhost:8000/tickets
2. Link tickets to specific queries
3. Describe performance issues

## 🗄️ Database Schema

### PostgreSQL (Main Data)
- **customers**: Customer records
- **products**: Product catalog  
- **orders**: Order data (no indexes for demonstration)

### SQLite (Metadata)
- **queries**: Query execution tracking
- **tickets**: Support tickets linked to queries

## 🔧 Configuration

### Environment Variables
```bash
# Database
PG_HOST=localhost
PG_DATABASE=longquery_demo
PG_USER=postgres
PG_PASSWORD=postgres

# Application
DEBUG=true
PORT=8000
```

## 🚀 Development

```bash
# Install dependencies
source .tejas/bin/activate
cd backend
pip install -r requirements.txt

# Start development server
python main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

**Simple and effective database query management**