# InstaGuard

**InstaGuard** is an intelligent web application designed to detect fake or bot profiles on Instagram.  
It leverages a **machine learning model** (AdaBoost Classifier) to analyze various Instagram profile features and classify accounts as **Real** or **Fake**.

---

## 🚀 Features
- Detects **fake/bot profiles** on Instagram with high accuracy.
- Built with **Python** and **Flask** for the backend.
- Uses **AdaBoost Classifier** for machine learning prediction.
- Web scraping to collect key Instagram profile data.
- Elegant and **user-friendly interface** for smooth interaction.
- Displays results in a clean, classic design.

---

## 🛠️ How It Works
1. **User Input** – Enter an Instagram username in the search box.
2. **Data Scraping** – The app collects:
   - Profile picture availability
   - Username characteristics
   - Follower-to-following ratio
   - Post count and metadata
3. **Prediction** – The pre-trained AdaBoost model processes the data.
4. **Output** – The account is classified as **Real** or **Fake**.

---

## 🖥️ Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS (Classic & Elegant Design)
- **Machine Learning:** AdaBoost Classifier (Scikit-learn)
- **Data Collection:** Web scraping (e.g., Selenium, Requests, BeautifulSoup)
- **Deployment:** Flask server

---

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/haripriyaguru/Fake-profile-Identification.git
   cd InstaGuard
