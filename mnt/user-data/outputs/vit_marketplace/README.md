# 🛒 VIT Marketplace

A full-stack web app where students can **buy and sell** second-hand items like books, electronics, cycles and more — with real-time chat!

---

## ✨ Features
- 🔐 User registration & login
- 📦 Post items with photos, price & category
- 🔍 Search & filter by category
- 💬 Real-time chat between buyer and seller
- ✅ Mark items as sold
- 🗑 Delete your own listings

## 🛠 Tech Stack
- **Backend:** Python, Flask, Flask-SocketIO
- **Database:** SQLite + SQLAlchemy
- **Frontend:** HTML, CSS, JavaScript
- **Auth:** Flask-Login + Werkzeug password hashing

## ⚙️ How to Run

```bash
git clone https://github.com/AbhimanyuSingh-beep/vit_marketplace.git
cd vit_marketplace
pip install -r requirements.txt
python app.py
```
Open browser at: **http://127.0.0.1:5000**

## 📂 Project Structure
```
vit_marketplace/
├── app.py                  # Main Flask application
├── templates/              # HTML pages
│   ├── base.html           # Common navbar/layout
│   ├── home.html           # Browse items
│   ├── login.html          # Login page
│   ├── register.html       # Register page
│   ├── sell.html           # Post item
│   ├── item_detail.html    # Single item view
│   ├── profile.html        # My listings
│   └── chat.html           # Real-time chat
├── static/uploads/         # Uploaded item images
├── requirements.txt        # Python dependencies
└── README.md
```

## 👨‍🎓 Built by
Abhimanyu Singh — VIT Bhopal
