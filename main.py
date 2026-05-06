import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import threading
import json
import csv
import os
from datetime import datetime
from collections import Counter
from typing import List, Dict, Tuple
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
import ssl
import webbrowser
import pickle
from pathlib import Path


# ===========================
# CONFIGURATION
# ===========================

class Config:
    NEWS_API_KEY = "YOUR_NEWS_API_KEY_HERE"
    EMAIL_CONFIG_FILE = "email_config.pkl"

    RSS_FEEDS = {
        "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "CNN": "http://rss.cnn.com/rss/cnn_topstories.rss",
        "Reuters": "http://feeds.reuters.com/reuters/topNews",
        "TechCrunch": "http://feeds.feedburner.com/TechCrunch",
        "ESPN": "http://www.espn.com/espn/rss/news",
        "BBC Technology": "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "BBC Business": "http://feeds.bbci.co.uk/news/business/rss.xml",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    }

    CATEGORIES = {
        "Technology": ["tech", "technology", "software", "ai", "code", "app", "digital", "computer", "internet"],
        "Business": ["business", "economy", "market", "stock", "finance", "trade", "invest", "bank"],
        "Sports": ["sport", "football", "basketball", "tennis", "cricket", "olympic", "soccer", "baseball"],
        "Entertainment": ["movie", "film", "music", "celebrity", "hollywood", "tv", "series", "artist"],
        "General": []
    }

    COLORS = {
        "primary": "#2c3e50",
        "secondary": "#3498db",
        "accent": "#e74c3c",
        "success": "#27ae60",
        "warning": "#f39c12",
        "background": "#f5f6fa",
        "surface": "#ffffff",
        "text": "#2c3e50",
        "text_light": "#7f8c8d",
        "border": "#dcdde1",
    }

    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


# ====================================
# EMAIL CONFIGURATION MANAGER
# ====================================

class EmailConfigManager:

    @staticmethod
    def save_config(email_data: Dict) -> bool:
        try:
            with open(Config.EMAIL_CONFIG_FILE, 'wb') as f:
                pickle.dump(email_data, f)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    @staticmethod
    def load_config() -> Dict:
        try:
            if Path(Config.EMAIL_CONFIG_FILE).exists():
                with open(Config.EMAIL_CONFIG_FILE, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Load error: {e}")
        return {}

    @staticmethod
    def delete_config() -> bool:
        try:
            if Path(Config.EMAIL_CONFIG_FILE).exists():
                os.remove(Config.EMAIL_CONFIG_FILE)
                return True
        except:
            pass
        return False


# =============================
# EMAIL DIGEST MODULE
# =============================

class EmailDigest:

    @staticmethod
    def test_connection(email: str, password: str, smtp_server: str = "smtp.gmail.com", port: int = 587) -> Tuple[
        bool, str]:
        try:
            server = smtplib.SMTP(smtp_server, port)
            server.starttls()
            server.login(email, password)
            server.quit()
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    @staticmethod
    def send_digest(articles: List[Dict], subject_prefix: str = "Daily News Digest",
                    recipient_email: str = None, sender_email: str = None,
                    sender_password: str = None) -> bool:

        config = EmailConfigManager.load_config()
        if not sender_email and config:
            sender_email = config.get('email')
            sender_password = config.get('password')
            recipient_email = recipient_email or config.get('recipient_email', sender_email)

        if not sender_email or not sender_password:
            return False

        if not recipient_email:
            recipient_email = sender_email

        subject = f"{subject_prefix} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        html_content = EmailDigest._build_html_content(articles)

        if not html_content:
            return False

        try:
            smtp_configs = [
                ("smtp.gmail.com", 587),
                ("smtp-mail.outlook.com", 587),
                ("smtp.office365.com", 587),
            ]

            for smtp_server, port in smtp_configs:
                try:
                    server = smtplib.SMTP(smtp_server, port)
                    server.starttls()
                    server.login(sender_email, sender_password)

                    msg = MIMEMultipart('alternative')
                    msg['From'] = sender_email
                    msg['To'] = recipient_email
                    msg['Subject'] = subject
                    msg.attach(MIMEText(html_content, 'html'))

                    server.send_message(msg)
                    server.quit()
                    return True
                except:
                    continue
            return False
        except Exception as e:
            print(f"Email error: {e}")
            return False

    @staticmethod
    def _build_html_content(articles: List[Dict]) -> str:
        if not articles:
            return ""

        articles_list = articles[:25]

        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .container { max-width: 800px; margin: auto; }
                .header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
                .news-item { margin: 20px 0; padding: 15px; border-bottom: 1px solid #ddd; }
                .title { font-size: 18px; font-weight: bold; }
                .title a { color: #3498db; text-decoration: none; }
                .meta { color: #666; font-size: 12px; margin: 10px 0; }
                .description { margin-top: 10px; }
                .footer { background: #2c3e50; color: white; padding: 15px; text-align: center; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Daily News Digest</h2>
                    <p>""" + datetime.now().strftime('%B %d, %Y') + """</p>
                </div>
        """

        for idx, article in enumerate(articles_list, 1):
            title = article.get('title', 'No title')
            url = article.get('url', '#')
            source = article.get('source', 'Unknown')
            category = article.get('category', 'General')
            description = article.get('description', 'No description')[:300]

            html += f"""
                <div class="news-item">
                    <div class="title">
                        <a href="{url}">{idx}. {title}</a>
                    </div>
                    <div class="meta">
                        Source: {source} | Category: {category}
                    </div>
                    <div class="description">
                        {description}...
                    </div>
                </div>
            """

        html += f"""
                <div class="footer">
                    Generated by Multi-Source News Aggregator
                    <br>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """

        return html


# ============================
# HTTP REQUEST HANDLER
# =============================

class HTTPClient:

    @staticmethod
    def get(url: str, timeout: int = 15, headers: Dict = None) -> str:
        try:
            req_headers = {'User-Agent': Config.USER_AGENT}
            if headers:
                req_headers.update(headers)

            request = urllib.request.Request(url, headers=req_headers)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
                data = response.read()
                try:
                    return data.decode('utf-8')
                except:
                    return data.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"HTTP Error: {e}")
            return ""

    @staticmethod
    def get_json(url: str, timeout: int = 15) -> Dict:
        response_text = HTTPClient.get(url, timeout)
        if response_text:
            try:
                return json.loads(response_text)
            except:
                return {}
        return {}


# =============================
# =============================
class RSSParser:

    @staticmethod
    def parse_rss(xml_content: str) -> List[Dict]:
        articles = []
        if not xml_content:
            return articles

        try:
            root = ET.fromstring(xml_content)
            channel = root.find('channel')
            if channel is None:
                for child in root:
                    if 'channel' in child.tag:
                        channel = child
                        break

            if channel is not None:
                for item in channel.findall('.//item'):
                    article_data = {}
                    for field in ['title', 'description', 'link', 'pubDate']:
                        elem = item.find(field)
                        if elem is None:
                            for child in item:
                                if field in child.tag:
                                    elem = child
                                    break
                        article_data[field] = elem.text.strip() if elem is not None and elem.text else ""

                    for child in item:
                        if 'encoded' in child.tag and child.text:
                            article_data['description'] = child.text.strip()
                            break

                    if article_data.get('title'):
                        articles.append({
                            "title": article_data.get('title', 'No title'),
                            "description": article_data.get('description', 'No description')[:500],
                            "link": article_data.get('link', ''),
                            "publish_date": article_data.get('pubDate', ''),
                        })
        except Exception as e:
            print(f"RSS Parse Error: {e}")

        return articles


# ===============================
# NEWS FETCHER
# ================================

class NewsFetcher:

    def __init__(self):
        self.http_client = HTTPClient()
        self.rss_parser = RSSParser()

    def fetch_from_newsapi(self, category: str = "general", page: int = 1) -> List[Dict]:
        articles = []
        if Config.NEWS_API_KEY == "YOUR_NEWS_API_KEY_HERE":
            return articles

        categories = {
            "Technology": "technology",
            "Business": "business",
            "Sports": "sports",
            "Entertainment": "entertainment",
            "General": "general"
        }

        api_category = categories.get(category, "general")
        url = f"https://newsapi.org/v2/top-headlines?country=us&category={api_category}&apiKey={Config.NEWS_API_KEY}&pageSize=100&page={page}"

        data = self.http_client.get_json(url)

        if data and data.get("status") == "ok":
            for item in data.get("articles", []):
                articles.append({
                    "title": item.get("title", "No title"),
                    "description": item.get("description", "No description"),
                    "source": item.get("source", {}).get("name", "Unknown"),
                    "publish_date": item.get("publishedAt", ""),
                    "url": item.get("url", ""),
                    "category": category,
                })

        return articles

    def fetch_from_rss(self, feed_name: str, feed_url: str) -> List[Dict]:
        articles = []
        xml_content = self.http_client.get(feed_url)

        if xml_content:
            parsed_articles = self.rss_parser.parse_rss(xml_content)

            for item in parsed_articles[:30]:
                category = self._auto_categorize(item.get("title", "") + " " + item.get("description", ""))
                articles.append({
                    "title": item.get("title", "No title"),
                    "description": item.get("description", "No description"),
                    "source": feed_name,
                    "publish_date": item.get("publish_date", ""),
                    "url": item.get("link", ""),
                    "category": category,
                })

        return articles

    def fetch_all_news(self, categories: List[str] = None, page: int = 1) -> List[Dict]:
        all_articles = []

        if categories is None:
            categories = list(Config.CATEGORIES.keys())

        for feed_name, feed_url in Config.RSS_FEEDS.items():
            all_articles.extend(self.fetch_from_rss(feed_name, feed_url))

        for category in categories:
            all_articles.extend(self.fetch_from_newsapi(category, page))

        unique_articles = {}
        for article in all_articles:
            title = article["title"].lower().strip()
            if title not in unique_articles:
                unique_articles[title] = article

        articles_list = list(unique_articles.values())
        articles_list.sort(key=lambda x: x["publish_date"], reverse=True)

        return articles_list

    def _auto_categorize(self, text: str) -> str:
        text = text.lower()
        for category, keywords in Config.CATEGORIES.items():
            if category != "General":
                for keyword in keywords:
                    if keyword in text:
                        return category
        return "General"

    def search_news(self, articles: List[Dict], keyword: str) -> List[Dict]:
        keyword = keyword.lower()
        return [a for a in articles if (
                keyword in a["title"].lower() or
                keyword in a["description"].lower() or
                keyword in a["source"].lower()
        )]

    def filter_by_category(self, articles: List[Dict], category: str) -> List[Dict]:
        return [a for a in articles if a["category"] == category]

    def filter_by_source(self, articles: List[Dict], source: str) -> List[Dict]:
        return [a for a in articles if a["source"] == source]


# ============================
# ===========================

class NewsStorage:

    @staticmethod
    def save_to_json(articles: List[Dict], filename: str = "saved_news.json") -> bool:
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "count": len(articles),
                "articles": articles
            }
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"JSON save error: {e}")
            return False

    @staticmethod
    def load_from_json(filename: str = "saved_news.json") -> List[Dict]:
        try:
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("articles", [])
        except Exception as e:
            print(f"JSON load error: {e}")
        return []

    @staticmethod
    def save_to_csv(articles: List[Dict], filename: str = "saved_news.csv") -> bool:
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                if articles:
                    fieldnames = ["title", "description", "source", "publish_date", "url", "category"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for article in articles:
                        row = {key: article.get(key, "") for key in fieldnames}
                        writer.writerow(row)
            return True
        except Exception as e:
            print(f"CSV save error: {e}")
            return False


# ==============================
# SENTIMENT ANALYZER
# =============================

class SentimentAnalyzer:
    POSITIVE_WORDS = {
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'brilliant', 'positive', 'success', 'win', 'winner', 'profit',
        'growth', 'breakthrough', 'innovation', 'hope', 'happy'
    }

    NEGATIVE_WORDS = {
        'bad', 'terrible', 'awful', 'horrible', 'disaster', 'crisis',
        'loss', 'fail', 'failure', 'drop', 'decline', 'risk', 'warning',
        'attack', 'war', 'conflict', 'death', 'damage', 'problem'
    }

    @staticmethod
    def analyze_sentiment(text: str) -> Dict:
        if not text:
            return {"score": 0, "sentiment": "Neutral"}

        text_lower = text.lower()
        words = set(re.findall(r'\b[a-z]+\b', text_lower))

        positive_count = len(words & SentimentAnalyzer.POSITIVE_WORDS)
        negative_count = len(words & SentimentAnalyzer.NEGATIVE_WORDS)

        score = positive_count - negative_count
        normalized_score = max(-1, min(1, score / 5))

        if normalized_score > 0.2:
            sentiment = "Positive"
        elif normalized_score < -0.2:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        return {
            "score": round(normalized_score, 2),
            "sentiment": sentiment
        }

    @staticmethod
    def get_trending_keywords(articles: List[Dict], top_n: int = 10) -> List[Tuple[str, int]]:
        all_text = " ".join([a["title"] + " " + a["description"] for a in articles])
        words = re.findall(r'\b[a-zA-Z]{4,}\b', all_text.lower())

        stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'are', 'was', 'were',
                      'will', 'would', 'could', 'should', 'what', 'when', 'where', 'which', 'their',
                      'there', 'they', 'been', 'has', 'had', 'can', 'may', 'very', 'just', 'but', 'not'}

        words = [w for w in words if w not in stop_words and len(w) > 3]
        word_counts = Counter(words)

        return word_counts.most_common(top_n)


# ==============================
# EMAIL CONFIGURATION DIALOG
# ==============================

class EmailConfigDialog:

    def __init__(self, parent):
        self.parent = parent

        dialog = tk.Toplevel(parent)
        dialog.title("Email Configuration")
        dialog.geometry("500x450")
        dialog.configure(bg=Config.COLORS["background"])
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()

        header = tk.Frame(dialog, bg=Config.COLORS["primary"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="Email Configuration", font=("Segoe UI", 14, "bold"),
                 bg=Config.COLORS["primary"], fg="white").pack(pady=12)

        content = tk.Frame(dialog, bg=Config.COLORS["background"], padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)

        info_text = """Instructions:
- For Gmail, use an App Password (not regular password)
- Go to Google Account -> Security -> 2-Step Verification -> App Passwords
- Generate a password for "Mail" and use it below"""

        info_label = tk.Label(content, text=info_text, font=("Segoe UI", 9),
                              bg=Config.COLORS["background"], fg=Config.COLORS["text_light"],
                              justify=tk.LEFT, wraplength=440)
        info_label.pack(fill=tk.X, pady=(0, 15))

        tk.Label(content, text="Email Address:", font=("Segoe UI", 10, "bold"),
                 bg=Config.COLORS["background"], fg=Config.COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        self.email_entry = tk.Entry(content, font=("Segoe UI", 10), bg="white",
                                    relief=tk.SOLID, bd=1)
        self.email_entry.pack(fill=tk.X, pady=(0, 15))

        tk.Label(content, text="Password / App Password:", font=("Segoe UI", 10, "bold"),
                 bg=Config.COLORS["background"], fg=Config.COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        self.password_entry = tk.Entry(content, font=("Segoe UI", 10), bg="white",
                                       relief=tk.SOLID, bd=1, show="*")
        self.password_entry.pack(fill=tk.X, pady=(0, 15))

        tk.Label(content, text="Recipient Email (optional):", font=("Segoe UI", 10, "bold"),
                 bg=Config.COLORS["background"], fg=Config.COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        self.recipient_entry = tk.Entry(content, font=("Segoe UI", 10), bg="white",
                                        relief=tk.SOLID, bd=1)
        self.recipient_entry.pack(fill=tk.X, pady=(0, 20))

        config = EmailConfigManager.load_config()
        if config:
            self.email_entry.insert(0, config.get('email', ''))
            self.recipient_entry.insert(0, config.get('recipient_email', ''))

        btn_frame = tk.Frame(content, bg=Config.COLORS["background"])
        btn_frame.pack(fill=tk.X, pady=10)

        test_btn = tk.Button(btn_frame, text="Test Connection", command=self.test_connection,
                             font=("Segoe UI", 10), bg=Config.COLORS["secondary"], fg="white",
                             padx=15, pady=5, cursor="hand2", relief=tk.FLAT)
        test_btn.pack(side=tk.LEFT, padx=5)

        save_btn = tk.Button(btn_frame, text="Save Configuration", command=self.save_config,
                             font=("Segoe UI", 10), bg=Config.COLORS["success"], fg="white",
                             padx=15, pady=5, cursor="hand2", relief=tk.FLAT)
        save_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(btn_frame, text="Clear", command=self.clear_config,
                              font=("Segoe UI", 10), bg=Config.COLORS["warning"], fg="white",
                              padx=15, pady=5, cursor="hand2", relief=tk.FLAT)
        clear_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                               font=("Segoe UI", 10), bg=Config.COLORS["text_light"], fg="white",
                               padx=15, pady=5, cursor="hand2", relief=tk.FLAT)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        if config and config.get('password'):
            note_label = tk.Label(content, text="Note: Password already configured (leave blank to keep existing)",
                                  font=("Segoe UI", 9), bg=Config.COLORS["background"],
                                  fg=Config.COLORS["success"])
            note_label.pack(pady=(10, 0))

        self.dialog = dialog

    def test_connection(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            messagebox.showwarning("Missing Info", "Please enter both email and password")
            return

        self.parent.config(cursor="watch")
        success, msg = EmailDigest.test_connection(email, password)
        self.parent.config(cursor="")

        if success:
            messagebox.showinfo("Success", "Connection successful!")
        else:
            messagebox.showerror("Error", msg)

    def save_config(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        recipient = self.recipient_entry.get().strip()

        if not email or not password:
            messagebox.showwarning("Missing Info", "Please enter both email and password")
            return

        config_data = {
            'email': email,
            'password': password,
            'recipient_email': recipient if recipient else email
        }

        if EmailConfigManager.save_config(config_data):
            messagebox.showinfo("Success", "Configuration saved successfully!")
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to save configuration")

    def clear_config(self):
        if messagebox.askyesno("Confirm", "Clear saved email configuration?"):
            EmailConfigManager.delete_config()
            self.email_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.recipient_entry.delete(0, tk.END)
            messagebox.showinfo("Success", "Configuration cleared!")


# ==============================
# MAIN APPLICATION
# ==============================

class NewsAggregatorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Source News Aggregator")
        self.root.geometry("1400x900")
        self.root.configure(bg=Config.COLORS["background"])

        self.current_articles = []
        self.filtered_articles = []
        self.current_page = 1
        self.page_size = 20
        self.current_selected_article = None

        self.fetcher = NewsFetcher()
        self.storage = NewsStorage()
        self.sentiment = SentimentAnalyzer()

        self.setup_ui()
        self.refresh_news()
        self.update_email_status()

    def setup_ui(self):
        self.setup_styles()
        self.create_header()
        self.setup_main_layout()
        self.create_footer()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        bg = Config.COLORS["background"]
        fg = Config.COLORS["text"]

        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("TLabelframe", background=bg, foreground=fg)
        style.configure("TEntry", fieldbackground="white", foreground=fg)

        for name, color in [("Primary", Config.COLORS["secondary"]),
                            ("Success", Config.COLORS["success"]),
                            ("Warning", Config.COLORS["warning"])]:
            style.configure(f"{name}.TButton", background=color, foreground="white",
                            borderwidth=0, font=("Segoe UI", 10))

    def create_header(self):
        header_frame = tk.Frame(self.root, bg=Config.COLORS["primary"], height=70)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="Multi-Source News Aggregator",
                               font=("Segoe UI", 18, "bold"),
                               bg=Config.COLORS["primary"], fg="white")
        title_label.pack(side=tk.LEFT, padx=30, pady=18)

        subtitle_label = tk.Label(header_frame, text="Powered by RSS Feeds",
                                  font=("Segoe UI", 10),
                                  bg=Config.COLORS["primary"], fg="#ecf0f1")
        subtitle_label.pack(side=tk.LEFT, padx=10, pady=22)

        self.header_stats = tk.Label(header_frame, text="", font=("Segoe UI", 11),
                                     bg=Config.COLORS["primary"], fg="#ecf0f1")
        self.header_stats.pack(side=tk.RIGHT, padx=30, pady=22)

    def create_footer(self):
        footer_frame = tk.Frame(self.root, bg=Config.COLORS["surface"], height=35)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        footer_frame.pack_propagate(False)

        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Press F5 to fetch news")

        status_label = tk.Label(footer_frame, textvariable=self.status_var, font=("Segoe UI", 9),
                                bg=Config.COLORS["surface"], fg=Config.COLORS["text_light"])
        status_label.pack(side=tk.LEFT, padx=20, pady=8)

        self.email_status_label = tk.Label(footer_frame, text="", font=("Segoe UI", 9),
                                           bg=Config.COLORS["surface"])
        self.email_status_label.pack(side=tk.RIGHT, padx=20, pady=8)

        self.time_label = tk.Label(footer_frame, text="", font=("Segoe UI", 9),
                                   bg=Config.COLORS["surface"], fg=Config.COLORS["text_light"])
        self.time_label.pack(side=tk.RIGHT, padx=20, pady=8)
        self.update_time()

    def update_time(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    def update_email_status(self):
        config = EmailConfigManager.load_config()
        if config and config.get('email'):
            email = config['email']
            masked = email[:3] + "..." + email[email.index('@'):] if '@' in email else "configured"
            self.email_status_label.config(text=f"Email: {masked}", fg=Config.COLORS["success"])
        else:
            self.email_status_label.config(text="Email: Not configured", fg=Config.COLORS["warning"])

    def setup_main_layout(self):
        control_panel = tk.Frame(self.root, bg=Config.COLORS["surface"], height=65, relief=tk.RAISED, bd=1)
        control_panel.pack(fill=tk.X, padx=10, pady=10)
        control_panel.pack_propagate(False)
        self.create_control_panel(control_panel)

        main_pane = tk.PanedWindow(self.root, bg=Config.COLORS["background"], sashwidth=5)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_panel = tk.Frame(main_pane, bg=Config.COLORS["background"])
        main_pane.add(left_panel, width=800)

        self.create_search_frame(left_panel).pack(fill=tk.X, pady=(0, 10))
        self.create_treeview(left_panel)
        self.create_pagination(left_panel)

        right_panel = tk.Frame(main_pane, bg=Config.COLORS["background"])
        main_pane.add(right_panel)
        self.create_details_panel(right_panel)
        self.create_trending_section()

    def create_control_panel(self, parent):
        btn_frame = tk.Frame(parent, bg=Config.COLORS["surface"])
        btn_frame.pack(side=tk.LEFT, padx=20, pady=12)

        buttons = [
            ("Fetch News", self.refresh_news, "Primary.TButton"),
            ("Save as JSON", lambda: self.save_news("json"), "Success.TButton"),
            ("Save as CSV", lambda: self.save_news("csv"), "Success.TButton"),
            ("Load Saved", self.load_saved_news, "Success.TButton"),
            ("Send Digest", self.send_digest_with_check, "Warning.TButton"),
            ("Email Settings", self.open_email_settings, "Primary.TButton"),
        ]

        for text, cmd, style in buttons:
            btn = ttk.Button(btn_frame, text=text, command=cmd, style=style)
            btn.pack(side=tk.LEFT, padx=3)

        filter_frame = tk.Frame(parent, bg=Config.COLORS["surface"])
        filter_frame.pack(side=tk.RIGHT, padx=20, pady=12)

        tk.Label(filter_frame, text="Quick Filter:", font=("Segoe UI", 10, "bold"),
                 bg=Config.COLORS["surface"], fg=Config.COLORS["text"]).pack(side=tk.LEFT, padx=5)

        for cat in ["All", "Technology", "Business", "Sports", "Entertainment"]:
            btn = tk.Button(filter_frame, text=cat, font=("Segoe UI", 9),
                            bg=Config.COLORS["background"], fg=Config.COLORS["text"],
                            relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                            command=lambda c=cat: self.filter_by_category_ui(c))
            btn.pack(side=tk.LEFT, padx=2)

    def create_search_frame(self, parent):
        frame = tk.Frame(parent, bg=Config.COLORS["surface"], relief=tk.RAISED, bd=1)

        tk.Label(frame, text="Search:", font=("Segoe UI", 10, "bold"),
                 bg=Config.COLORS["surface"], fg=Config.COLORS["text"]).pack(side=tk.LEFT, padx=(15, 5), pady=10)

        self.search_entry = tk.Entry(frame, font=("Segoe UI", 10), width=30,
                                     bg="white", relief=tk.SOLID, bd=1)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=10)
        self.search_entry.bind('<Return>', lambda e: self.search_news())

        search_btn = tk.Button(frame, text="Search", command=self.search_news,
                               font=("Segoe UI", 9), bg=Config.COLORS["secondary"], fg="white",
                               padx=15, pady=3, cursor="hand2", relief=tk.FLAT)
        search_btn.pack(side=tk.LEFT, padx=2)

        clear_btn = tk.Button(frame, text="Clear", command=self.clear_search,
                              font=("Segoe UI", 9), bg=Config.COLORS["text_light"], fg="white",
                              padx=15, pady=3, cursor="hand2", relief=tk.FLAT)
        clear_btn.pack(side=tk.LEFT, padx=2)

        separator = tk.Frame(frame, width=1, bg=Config.COLORS["border"])
        separator.pack(side=tk.LEFT, padx=15, fill=tk.Y, pady=8)

        tk.Label(frame, text="Category:", font=("Segoe UI", 10, "bold"),
                 bg=Config.COLORS["surface"], fg=Config.COLORS["text"]).pack(side=tk.LEFT, padx=(0, 5), pady=10)

        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(frame, textvariable=self.category_var,
                                           values=["All"] + list(Config.CATEGORIES.keys()),
                                           width=15, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_by_category_ui(self.category_var.get()))

        tk.Label(frame, text="Source:", font=("Segoe UI", 10, "bold"),
                 bg=Config.COLORS["surface"], fg=Config.COLORS["text"]).pack(side=tk.LEFT, padx=(15, 5), pady=10)

        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(frame, textvariable=self.source_var, width=20, state="readonly")
        self.source_combo.pack(side=tk.LEFT, padx=5)
        self.source_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_by_source_ui())

        return frame

    def create_treeview(self, parent):
        tree_container = tk.Frame(parent, bg=Config.COLORS["background"])
        tree_container.pack(fill=tk.BOTH, expand=True)

        scroll_y = tk.Scrollbar(tree_container, orient=tk.VERTICAL)
        scroll_x = tk.Scrollbar(tree_container, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(tree_container,
                                 columns=("Title", "Source", "Category", "Date", "Sentiment"),
                                 show="tree headings",
                                 yscrollcommand=scroll_y.set,
                                 xscrollcommand=scroll_x.set)

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        columns_config = [
            ("#0", "#", 50, tk.CENTER),
            ("Title", "Title", 550, tk.W),
            ("Source", "Source", 150, tk.W),
            ("Category", "Category", 100, tk.CENTER),
            ("Date", "Date", 160, tk.CENTER),
            ("Sentiment", "Sentiment", 80, tk.CENTER)
        ]

        for col, heading, width, anchor in columns_config:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        self.tree.bind('<<TreeviewSelect>>', self.on_article_select)

    def create_pagination(self, parent):
        frame = tk.Frame(parent, bg=Config.COLORS["background"], pady=10)
        frame.pack(fill=tk.X)

        self.prev_btn = tk.Button(frame, text="Previous", command=self.prev_page,
                                  font=("Segoe UI", 9), bg=Config.COLORS["secondary"], fg="white",
                                  padx=20, pady=5, cursor="hand2", relief=tk.FLAT)
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.page_label = tk.Label(frame, text="Page 1 of 1", font=("Segoe UI", 10, "bold"),
                                   bg=Config.COLORS["background"], fg=Config.COLORS["text"])
        self.page_label.pack(side=tk.LEFT, padx=15)

        self.next_btn = tk.Button(frame, text="Next", command=self.next_page,
                                  font=("Segoe UI", 9), bg=Config.COLORS["secondary"], fg="white",
                                  padx=20, pady=5, cursor="hand2", relief=tk.FLAT)
        self.next_btn.pack(side=tk.LEFT, padx=5)

        self.stats_label = tk.Label(frame, text="", font=("Segoe UI", 9),
                                    bg=Config.COLORS["background"], fg=Config.COLORS["text_light"])
        self.stats_label.pack(side=tk.RIGHT, padx=10)

    def create_details_panel(self, parent):
        header_frame = tk.Frame(parent, bg=Config.COLORS["primary"], height=45)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="Article Details", font=("Segoe UI", 14, "bold"),
                 bg=Config.COLORS["primary"], fg="white").pack(side=tk.LEFT, padx=15, pady=10)

        self.details_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, font=("Segoe UI", 10),
                                                      bg="white", fg=Config.COLORS["text"],
                                                      padx=15, pady=15, relief=tk.FLAT)
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(parent, bg=Config.COLORS["background"])
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        open_btn = tk.Button(btn_frame, text="Open in Browser", command=self.open_url,
                             font=("Segoe UI", 9), bg=Config.COLORS["secondary"], fg="white",
                             padx=15, pady=5, cursor="hand2", relief=tk.FLAT)
        open_btn.pack(side=tk.LEFT, padx=5)

        save_btn = tk.Button(btn_frame, text="Save Article", command=self.save_selected,
                             font=("Segoe UI", 9), bg=Config.COLORS["success"], fg="white",
                             padx=15, pady=5, cursor="hand2", relief=tk.FLAT)
        save_btn.pack(side=tk.LEFT, padx=5)

        analyze_btn = tk.Button(btn_frame, text="Analyze Sentiment", command=self.analyze_selected_sentiment,
                                font=("Segoe UI", 9), bg=Config.COLORS["warning"], fg="white",
                                padx=15, pady=5, cursor="hand2", relief=tk.FLAT)
        analyze_btn.pack(side=tk.LEFT, padx=5)

    def create_trending_section(self):
        trending_frame = tk.Frame(self.root, bg=Config.COLORS["surface"], relief=tk.RAISED, bd=1, height=45)
        trending_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        trending_frame.pack_propagate(False)

        tk.Label(trending_frame, text="Trending Keywords:", font=("Segoe UI", 10, "bold"),
                 bg=Config.COLORS["surface"], fg=Config.COLORS["text"]).pack(side=tk.LEFT, padx=15, pady=12)

        self.trending_label = tk.Label(trending_frame, text="Fetch news to see trending topics",
                                       font=("Segoe UI", 10), bg=Config.COLORS["surface"],
                                       fg=Config.COLORS["secondary"])
        self.trending_label.pack(side=tk.LEFT, padx=10, pady=12)

    def update_status(self, message: str):
        self.status_var.set(message)
        self.root.update_idletasks()

    def open_email_settings(self):
        EmailConfigDialog(self.root)
        self.update_email_status()

    def send_digest_with_check(self):
        config = EmailConfigManager.load_config()

        if not config or not config.get('email'):
            response = messagebox.askyesno("Email Not Configured",
                                           "Email not configured. Configure it now?")
            if response:
                self.open_email_settings()
            return

        if not self.current_articles:
            messagebox.showwarning("No Data", "No articles to send")
            return

        recipient = simpledialog.askstring("Recipient Email",
                                           "Enter recipient email (leave blank for default):",
                                           parent=self.root)

        if recipient == "":
            recipient = None

        def send_thread():
            self.update_status("Sending email digest...")
            self.root.config(cursor="watch")

            success = EmailDigest.send_digest(self.filtered_articles[:25],
                                              recipient_email=recipient)

            self.root.config(cursor="")

            if success:
                self.root.after(0, lambda: messagebox.showinfo("Success", "Email sent successfully!"))
                self.root.after(0, self.update_status, "Email sent successfully")
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to send email"))
                self.root.after(0, self.update_status, "Email sending failed")

        threading.Thread(target=send_thread, daemon=True).start()

    def refresh_news(self):
        def fetch_thread():
            self.update_status("Fetching news from multiple sources...")
            self.root.config(cursor="watch")

            articles = self.fetcher.fetch_all_news(page=self.current_page)
            self.current_articles = articles
            self.filtered_articles = articles

            self.root.after(0, self.update_display)
            self.root.after(0, self.update_trending)
            self.root.after(0, self.update_status, f"Loaded {len(articles)} articles")
            self.root.after(0, lambda: self.header_stats.config(text=f"{len(articles)} Articles"))
            self.root.config(cursor="")

        threading.Thread(target=fetch_thread, daemon=True).start()

    def update_display(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        start_idx = (self.current_page - 1) * self.page_size
        page_articles = self.filtered_articles[start_idx:start_idx + self.page_size]

        for idx, article in enumerate(page_articles, 1):
            pub_date = article.get("publish_date", "")
            if pub_date:
                pub_date = pub_date[:19].replace('T', ' ') if len(pub_date) > 19 else pub_date
            else:
                pub_date = "Unknown"

            sentiment = self.sentiment.analyze_sentiment(article["title"])

            self.tree.insert("", tk.END, values=(
                article["title"][:120],
                article["source"][:35],
                article["category"],
                pub_date,
                sentiment["sentiment"]
            ))

        total_pages = max(1, (len(self.filtered_articles) + self.page_size - 1) // self.page_size)
        self.page_label.config(text=f"Page {self.current_page} of {total_pages}")

        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for article in self.filtered_articles[:50]:
            sent = self.sentiment.analyze_sentiment(article["title"])
            sentiment_counts[sent["sentiment"]] += 1

        self.stats_label.config(
            text=f"Pos: {sentiment_counts['Positive']}  Neg: {sentiment_counts['Negative']}  Neu: {sentiment_counts['Neutral']}")
        self.update_sources_menu()

    def update_sources_menu(self):
        sources = sorted(set(a["source"] for a in self.current_articles))
        self.source_combo['values'] = ["All"] + sources

    def show_details(self, article: Dict):
        self.details_text.delete(1.0, tk.END)
        sentiment = self.sentiment.analyze_sentiment(article["title"])

        details = f"""
ARTICLE DETAILS
{'=' * 60}

TITLE:
{article['title']}

{'=' * 60}

DESCRIPTION:
{article['description']}

{'=' * 60}

INFORMATION:
  Source:      {article['source']}
  Category:    {article['category']}
  Published:   {article['publish_date']}
  Sentiment:   {sentiment['sentiment']} (Score: {sentiment['score']})

{'=' * 60}

URL:
{article['url']}

{'=' * 60}
Tip: Click 'Open in Browser' to read the full article.
"""
        self.details_text.insert(1.0, details)
        self.current_selected_article = article

    def on_article_select(self, event):
        selection = self.tree.selection()
        if selection:
            idx = self.tree.index(selection[0])
            actual_idx = (self.current_page - 1) * self.page_size + idx
            if actual_idx < len(self.filtered_articles):
                self.show_details(self.filtered_articles[actual_idx])

    def open_url(self):
        if hasattr(self, 'current_selected_article') and self.current_selected_article:
            webbrowser.open(self.current_selected_article['url'])
        else:
            messagebox.showwarning("No Selection", "Please select an article first")

    def search_news(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("Empty Search", "Enter a keyword to search")
            return

        self.update_status(f"Searching for: {keyword}")
        self.filtered_articles = self.fetcher.search_news(self.current_articles, keyword)
        self.current_page = 1
        self.update_display()
        self.update_status(f"Found {len(self.filtered_articles)} articles matching '{keyword}'")

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.filtered_articles = self.current_articles
        self.current_page = 1
        self.update_display()
        self.update_status("Search cleared")

    def filter_by_category_ui(self, category: str):
        if category == "All":
            self.filtered_articles = self.current_articles
        else:
            self.filtered_articles = self.fetcher.filter_by_category(self.current_articles, category)

        self.current_page = 1
        self.update_display()
        self.category_var.set(category)
        self.update_status(f"Showing {len(self.filtered_articles)} articles in {category}")

    def filter_by_source_ui(self, source: str = None):
        if source is None:
            source = self.source_var.get()

        if source == "All" or not source:
            self.filtered_articles = self.current_articles
        else:
            self.filtered_articles = self.fetcher.filter_by_source(self.current_articles, source)

        self.current_page = 1
        self.update_display()
        self.update_status(f"Showing {len(self.filtered_articles)} articles from {source}")

    def clear_filters(self):
        self.category_var.set("All")
        self.source_var.set("")
        self.search_entry.delete(0, tk.END)
        self.filtered_articles = self.current_articles
        self.current_page = 1
        self.update_display()
        self.update_status("All filters cleared")

    def save_news(self, format_type: str):
        if not self.filtered_articles:
            messagebox.showwarning("No Data", "No articles to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_{timestamp}.{format_type}"

        if format_type == "json":
            success = self.storage.save_to_json(self.filtered_articles, filename)
        else:
            success = self.storage.save_to_csv(self.filtered_articles, filename)

        if success:
            messagebox.showinfo("Success", f"Saved {len(self.filtered_articles)} articles to {filename}")
            self.update_status(f"Saved to {filename}")
        else:
            messagebox.showerror("Error", f"Failed to save to {filename}")

    def save_selected(self):
        if hasattr(self, 'current_selected_article') and self.current_selected_article:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"saved_article_{timestamp}.json"

            if self.storage.save_to_json([self.current_selected_article], filename):
                messagebox.showinfo("Success", f"Article saved to {filename}")
                self.update_status(f"Saved to {filename}")
            else:
                messagebox.showerror("Error", "Failed to save article")
        else:
            messagebox.showwarning("No Selection", "Please select an article first")

    def load_saved_news(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])

        if filename:
            articles = self.storage.load_from_json(filename)
            if articles:
                self.current_articles = articles
                self.filtered_articles = articles
                self.current_page = 1
                self.update_display()
                self.update_trending()
                self.update_status(f"Loaded {len(articles)} articles from {os.path.basename(filename)}")
                self.header_stats.config(text=f"{len(articles)} Articles")
            else:
                messagebox.showerror("Error", "Failed to load file or file is empty")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_display()

    def next_page(self):
        total_pages = max(1, (len(self.filtered_articles) + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_display()

    def update_trending(self):
        if self.current_articles:
            trending = self.sentiment.get_trending_keywords(self.current_articles, 8)
            if trending:
                text = "  |  ".join([f"{word} ({count})" for word, count in trending])
                self.trending_label.config(text=text)
            else:
                self.trending_label.config(text="Fetch news to see trending topics")

    def analyze_selected_sentiment(self):
        if hasattr(self, 'current_selected_article') and self.current_selected_article:
            article = self.current_selected_article
            title_sent = self.sentiment.analyze_sentiment(article["title"])
            desc_sent = self.sentiment.analyze_sentiment(article["description"])

            result = f"""
SENTIMENT ANALYSIS REPORT
{'=' * 40}

TITLE SENTIMENT:
  Sentiment: {title_sent['sentiment']}
  Score: {title_sent['score']}

DESCRIPTION SENTIMENT:
  Sentiment: {desc_sent['sentiment']}
  Score: {desc_sent['score']}

{'=' * 40}
INTERPRETATION:
"""
            if title_sent['sentiment'] == "Positive":
                result += "  This article has an optimistic/positive tone."
            elif title_sent['sentiment'] == "Negative":
                result += "  This article has a concerning/negative tone."
            else:
                result += "  This article maintains a neutral/factual tone."

            messagebox.showinfo("Sentiment Analysis", result)
        else:
            messagebox.showwarning("No Selection", "Please select an article first")


# ======================
# MAIN ENTRY POINT
# =====================
def main():
    root = tk.Tk()

    window_width, window_height = 1400, 900
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    if Config.NEWS_API_KEY == "YOUR_NEWS_API_KEY_HERE":
        print("\n" + "=" * 60)
        print("WARNING: NewsAPI key not configured!")
        print("The app will still work using RSS feeds only (8+ sources).")
        print("Get a free API key from: https://newsapi.org/")
        print("=" * 60 + "\n")

    app = NewsAggregatorApp(root)
    root.bind('<F5>', lambda e: app.refresh_news())
    root.mainloop()


if __name__ == "__main__":
    main()