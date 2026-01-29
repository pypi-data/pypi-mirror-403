#!/usr/bin/env python3
"""
Unphishable - Advanced Phishing Detection Tool 🛡️
Multi-domain scanner with intelligent brand detection
"""

import sys
import os
import subprocess
from datetime import datetime
import time
import argparse
import socket
import ssl
import whois
from urllib.parse import urlparse
import requests

# Auto-install beautifulsoup4 if missing
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing missing dependency: beautifulsoup4")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "beautifulsoup4"])
    from bs4 import BeautifulSoup

# ============================================
# BANNER
# ============================================

def display_minecraft_banner():
    banner = r"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║      ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗███████╗██╗  ██╗ █████╗ ██████╗  ║
║     ██╔════╝██╔═══██╗██╔═══██╗██║  ██║██║██╔════╝██║  ██║██╔══██╗██╔══██╗ ║
║     ██║     ██║   ██║██║   ██║███████║██║█████╗  ███████║███████║██████╔╝ ║
║     ██║     ██║   ██║██║   ██║██╔══██║██║██╔══╝  ╚════██║██╔══██║██╔══██╗ ║
║     ╚██████╗╚██████╔╝╚██████╔╝██║  ██║██║███████╗     ██║██║  ██║██║  ██║ ║
║      ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ║
║                                                                            ║
║                  █████╗ ███╗   ██╗██████╗░██╗  ██╗ █████╗ ██████╗         ║
║                 ██╔══██╗████╗  ██║██╔══██╗██║  ██║██╔══██╗██╔══██╗        ║
║                 ███████║██╔██╗ ██║██████╔╝███████║███████║██████╔╝        ║
║                 ██╔══██║██║╚██╗██║██╔═══╝ ╚════██║██╔══██║██╔══██╗        ║
║                 ██║  ██║██║ ╚████║██║          ██║██║  ██║██║  ██║        ║
║                 ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝          ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝        ║
║                                                                            ║
║                           ** U N P H I S H A B L E **                      ║
║                                                                            ║
║                 🛡️  Advanced Phishing Detection Tool  🛡️                 ║
║           Multi-domain • Brand Impersonation • Homoglyph Scanner            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)

# Spinner
def spinner(duration=1.0, message="Processing"):
    spinners = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r\033[1;36m{message}\033[0m {spinners[i % len(spinners)]} ⏳")
        sys.stdout.flush()
        i += 1
        time.sleep(0.08)
    sys.stdout.write(f"\r\033[1;32m{message} Done ✅\033[0m          \n")
    sys.stdout.flush()

# Install/Help/Uninstall (your original)
def show_install_help():
    display_minecraft_banner()
    print("""
\033[1;33m
═══════════════════════════════════════════════════════════════════════════
                          INSTALLATION & USAGE GUIDE 📖
═══════════════════════════════════════════════════════════════════════════\033[0m

\033[1;33m📦 INSTALLATION\033[0m
───────────────────────────────────────────────────────────────────────────

  Quick Install:   python3 unphishable.py --install 🚀
  System-Wide:     sudo python3 unphishable.py --install 🔧
  Run Direct:      ./unphishable.py google.com ▶️

\033[1;33m🔍 USAGE EXAMPLES\033[0m
───────────────────────────────────────────────────────────────────────────

  Single:     unphishable google.com 🔎
  Multiple:   unphishable paypa1.com g00gle.com ⚡

\033[1;32mStay safe online! 🛡️\033[0m
""")

def install_script():
    print("\n\033[1;36m🔧 Starting installation...\033[0m\n")
    
    is_root = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
    
    if is_root:
        install_dir = "/usr/local/bin"
        print("\033[1;33m⚠️ Running as root - system-wide install\033[0m")
    else:
        install_dir = os.path.expanduser("~/.local/bin")
        print(f"\033[1;32m✓ User install to: {install_dir}\033[0m")
    
    os.makedirs(install_dir, exist_ok=True)
    
    current_script = os.path.abspath(__file__)
    target_path = os.path.join(install_dir, "unphishable")
    
    import shutil
    try:
        shutil.copy2(current_script, target_path)
        os.chmod(target_path, 0o755)
        print(f"\033[1;32m✓ Copied to: {target_path} ✅\033[0m")
    except Exception as e:
        print(f"\033[1;31m✗ Copy failed: {e}\033[0m")
        sys.exit(1)
    
    print("\n\033[1;36m📦 Dependencies...\033[0m")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "requests", "python-whois", "colorama", "beautifulsoup4"], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("\033[1;32m✓ Dependencies ready ✅\033[0m")
    except:
        print("\033[1;33m⚠️ Dependencies may need manual install\033[0m")
    
    path_dirs = os.environ.get('PATH', '').split(':')
    if install_dir not in path_dirs:
        print(f"\n\033[1;33m⚠️ Add to PATH:\033[0m export PATH=\"$PATH:{install_dir}\"")
        print("Then: source ~/.bashrc (or restart terminal) 🔄")
    else:
        print(f"\n\033[1;32m✓ PATH ready ✅\033[0m")
    
    print("\n\033[1;32m✅ Installed! Run: unphishable <domain> 🚀\033[0m\n")

def uninstall_script():
    print("\n\033[1;36m🗑️ Uninstalling Unphishable...\033[0m\n")
    
    paths = ["/usr/local/bin/unphishable", os.path.expanduser("~/.local/bin/unphishable")]
    removed = False
    for path in paths:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"\033[1;32m✓ Removed: {path} ✅\033[0m")
                removed = True
            except Exception as e:
                print(f"\033[1;31m✗ Failed: {e}\033[0m")
    
    if removed:
        print("\n\033[1;32m✅ Uninstalled! 🗑️\033[0m\n")
    else:
        print("\n\033[1;33m⚠️ No install found\033[0m\n")

# ConsoleManager (your original)
class ConsoleManager:
    def __init__(self):
        self.has_colorama = False
        self.has_rich = False
        self.setup_consoles()
    
    def setup_consoles(self):
        try:
            from colorama import init, Fore, Style
            init(autoreset=True)
            self.Fore = Fore
            self.Style = Style
            self.has_colorama = True
        except ImportError:
            self.install_package("colorama")
            try:
                from colorama import init, Fore, Style
                init(autoreset=True)
                self.Fore = Fore
                self.Style = Style
                self.has_colorama = True
            except:
                self.Fore = type('obj', (object,), {'RED': '', 'GREEN': '', 'YELLOW': '', 'CYAN': '', 'WHITE': ''})
                self.Style = type('obj', (object,), {'RESET_ALL': ''})
        
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table
            self.console = Console()
            self.Panel = Panel
            self.Table = Table
            self.has_rich = True
        except ImportError:
            self.console = None
            self.Panel = None
            self.Table = None
    
    def install_package(self, package):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
            return True
        except:
            return False
    
    def print_message(self, text, color="white"):
        if self.has_colorama:
            colors = {
                "red": self.Fore.RED,
                "green": self.Fore.GREEN,
                "yellow": self.Fore.YELLOW,
                "cyan": self.Fore.CYAN,
                "white": self.Fore.WHITE
            }
            print(f"{colors.get(color, self.Fore.WHITE)}{text}{self.Style.RESET_ALL}")
        else:
            print(text)
    
    def display_banner(self):
        if self.has_colorama:
            print(f"{self.Fore.YELLOW}{self.Style.BRIGHT}")
        display_minecraft_banner()
        if self.has_colorama:
            print(f"{self.Fore.RESET}{self.Style.RESET_ALL}")
    
    def display_explanation(self, risk_score, factors):
        if self.has_rich and self.console:
            explanation_lines = []
            if risk_score < 10:
                explanation_lines.append("📈 Minimal risk indicators detected.")
            elif risk_score < 20:
                explanation_lines.append("📈 Some low-risk factors present.")
            elif risk_score < 30:
                explanation_lines.append("⚠️ Multiple suspicious factors detected.")
            else:
                explanation_lines.append("🚨 High concentration of risk factors.")
            
            factor_explanations = {
                "redirect": "🔄 Redirects can hide final destination",
                "privacy": "🛡️ WHOIS privacy with suspicious domain patterns",
                "invalid_ssl": "❌ Missing SSL indicates poor security",
                "new_domain": "🆕 New domains are riskier (often <1 year)",
                "unreachable": "📡 Domain may be fake or taken down",
                "brand_impersonation": "🎭 Domain mimics major brand + free SSL = classic phishing",
                "harvest_intent": "💳 Potential credential/payment harvesting detected"
            }
            
            for factor, explanation in factor_explanations.items():
                if factor in str(factors).lower():
                    explanation_lines.append(explanation)
            
            explanation_text = "\n".join(explanation_lines)
            panel = self.Panel(
                explanation_text,
                title="📋 Risk Analysis",
                border_style="cyan",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print(f"\n{'─'*40}")
            print("📋 RISK ANALYSIS:")
            print(f"{'─'*40}")
            
            if risk_score < 10:
                print("• Minimal risk indicators detected.")
            elif risk_score < 20:
                print("• Some low-risk factors present.")
            elif risk_score < 30:
                print("• Multiple suspicious factors detected.")
            else:
                print("• High concentration of risk factors.")
            
            if factors:
                print("\nKey Factors:")
                for factor in str(factors).split(','):
                    if factor.strip():
                        print(f"  • {factor.strip()}")

console_mgr = ConsoleManager()

# Brand list (your full original list)
BIG_BRANDS = [
    "microsoft", "office", "outlook", "onedrive", "teams", "azure", "windows", "bing", "skype", "xbox",
    "google", "gmail", "youtube", "drive", "maps", "chrome", "android", "pixel", "nest", "pay",
    "apple", "icloud", "itunes", "appstore", "iphone", "mac", "ipad", "watch", "airpods", "appleid",
    "amazon", "aws", "prime", "alexa", "kindle", "echo", "firetv", "audible", "twitch", "imdb",
    "paypal", "venmo", "xoom", "braintree", "coinbase", "binance", "kraken", "gemini", "ledger", "trezor",
    "facebook", "meta", "instagram", "whatsapp", "messenger", "oculus", "threads",
    "linkedin", "netflix", "spotify", "discord", "twitter", "x", "tiktok", "snapchat", "pinterest", "reddit",
    "zoom", "slack", "dropbox", "adobe", "photoshop", "acrobat", "creativecloud", "oracle", "cisco", "ibm",
    "chase", "bankofamerica", "wellsfargo", "citibank", "hsbc", "barclays", "americanexpress", "visa", "mastercard",
    "discover", "capitalone", "usbank", "pnc", "tdbank", "ally", "schwab", "fidelity", "vanguard", "etrade",
    "robinhood", "sofi", "cashapp", "zelle", "stripe", "square", "wise", "revolut", "monzo", "n26",
    "dhl", "fedex", "ups", "usps", "royalmail", "postnl", "auspost", "canadapost", "dpd", "tnt",
    "verizon", "att", "tmobile", "sprint", "vodafone", "orange", "telefonica", "telstra", "bt", "sky",
    "ebay", "aliexpress", "walmart", "target", "bestbuy", "costco", "homedepot", "lowes", "etsy", "shopify",
    "nike", "adidas", "puma", "underarmour", "lululemon", "mcdonalds", "starbucks", "subway", "kfc", "dominos",
    "tesla", "ford", "toyota", "honda", "bmw", "mercedes", "audi", "volkswagen", "hyundai", "kia",
    "norton", "mcafee", "avast", "bitdefender", "kaspersky", "eset", "avg", "malwarebytes", "sophos", "trendmicro",
    "uber", "lyft", "doordash", "grubhub", "airbnb", "booking", "expedia", "hotels", "trivago", "agoda",
    "delta", "united", "americanairlines", "southwest", "lufthansa", "britishairways", "emirates", "qatarairways",
    "godaddy", "namecheap", "bluehost", "hostgator", "siteground", "roblox", "steam", "epicgames", "nintendo", "playstation",
    "docusign", "okta", "salesforce", "servicenow", "atlassian", "github", "gitlab", "bitbucket", "canva", "figma",
    "notion", "evernote", "trello", "asana", "monday", "airtable", "zoho", "quickbooks", "xero", "freshbooks",
    "paypal", "squareup", "stripe", "shopify", "bigcommerce", "wix", "squarespace", "wordpress", "joomla", "drupal",
    "yahoo", "aol", "protonmail", "tutanota", "outlook", "hotmail", "live", "msn",
    "wells", "boa", "citi", "usaa", "navyfederal", "regions", "fifththird", "huntington", "keybank", "mtbank",
    "santander", "bbva", "ing", "deutschebank", "creditagricole", "societegenerale", "natwest", "lloyds", "barclaycard",
    "american", "amex", "capone", "chime", "monzo", "n26", "revolut", "starling", "bunq", "wise",
    "kraken", "bybit", "okx", "kucoin", "gateio", "huobi", "bitfinex", "bitstamp", "gemini", "cryptocom",
    "metamask", "trustwallet", "phantom", "coinomi", "exodus", "electrum", "myetherwallet", "binancesmartchain",
    "youtube", "twitch", "disneyplus", "hbo", "hulu", "paramountplus", "peacock", "primevideo",
    "samsung", "lg", "sony", "panasonic", "philips", "dell", "hp", "lenovo", "acer", "asus",
    "logitech", "razer", "corsair", "steelseries", "hyperx", "nvidia", "amd", "intel",
    "uniswap", "opensea", "rarible", "foundation", "superrare", "blur", "looksrare", "magiceden",
    "westernunion", "moneygram", "remitly", "worldremit", "transferwise", "paypal",
    "hsbc", "barclayscard", "lloydsbank", "natwestbank", "rbs", "nationwide", "halifax", "tsb",
    "santanderuk", "monzoapp", "starlingbank", "revolutapp", "wiseapp", "paypalapp",
    "venmoapp", "cashapp", "zellepay", "robinhoodapp", "coinbasewallet", "binanceapp",
    "krakenpro", "geminiwallet", "ledgerlive", "trezorwallet", "metamaskio", "trustwalletapp",
    "phantomwallet", "exoduswallet", "electrumwallet", "myetherwallet", "uniswaporg",
    "openseaio", "rariblecom", "blur_io", "magiceden_io", "foundationapp", "superrare",
    "looksrare", "dhlglobal", "fedexcom", "upscom", "uspscom", "royalmailcom",
    "verizonwireless", "attwireless", "tmobileusa", "sprint", "vodafoneuk", "orange_fr",
    "walmartcom", "targetcom", "bestbuycom", "costcocom", "homedepotcom", "lowescom",
    "ebaycom", "aliexpresscom", "amazonprime", "netflixus", "spotifycom", "youtubepremium",
    "discordapp", "tiktokapp", "snapchat", "instagramapp", "facebookapp", "whatsapp",
    "twitter", "xcom", "reddit", "pinterest", "linkedin", "zoomus", "slackhq",
    "dropbox", "adobecc", "oraclecloud", "ciscocom", "ibmcloud", "salesforce",
    "docusign", "okta", "atlassian", "github", "gitlab", "bitbucket", "canva",
    "figma", "notion", "evernote", "trello", "asana", "mondaydotcom", "airtable",
    "zohocrm", "quickbooks", "xero", "freshbooks", "paypalbusiness",
    "mtn", "mtncameroon", "mtn.cm", "orangecm", "orange.cm", "camtel", "nexttelcameroon", "viettelcameroon", "yoomee", "matrixtelecoms", "ringo.cm", "pastel.cm", "camnet", "cmtelecom",
    "afrilandfirstbank", "afriland", "bicec", "bic ec", "sgcameroun", "societegenerale", "ecobankcameroon", "ubacameroon", "commercialbankcameroon", "cbc", "accessbankcameroon", "africagoldenbank", "banqueatlantique", "nfcbank", "la regionale", "bangebank", "citibankcameroon",
    "1xbet", "1xbet.cm", "paripesa", "paripesa.cm", "melbet", "betwinner", "888starz", "premierbet", "premierbet.cm", "sportybet", "bet9ja", "betking", "betmomo", "roisbet", "roisbet.cm", "trustdice", "stake.cm", "bc.game", "winzio", "cryptoleo",
    "mt nmomo", "mtnmobilemoney", "orangemoney", "orangemoney.cm", "expressunion", "maviance", "paysika", "diool", "fapshi", "waspito", "upowa", "iwomi", "softeller", "m2umoney", "smecreditpro", "sparklinkafrica", "mansagame",
    "eneo", "eneocameroon", "enocameroon", "sabc", "brasseriesducameroun", "guinnesscameroon", "cdc", "cameroondevelopmentcorporation", "sosucam", "cicam", "tradex", "perenco", "sonara", "sodecoton", "olamcam", "congelcam", "sorepco", "camairco", "dangotecameroon", "totalcameroon", "totalenergiescameroon", "axassurance", "activaassurance", "chanasassurances",
]

# Pattern functions (your original)
def has_misleading_numbers(domain):
    suspicious_digits = {'0', '1', '3', '4', '5', '7'}
    found = set()
    lower = domain.lower()
    for d in suspicious_digits:
        if d in lower:
            found.add(d)
    if found:
        return True, f"Detected misleading digits: {', '.join(sorted(found))}"
    return False, "None"

def has_cyclic_characters(domain):
    check_str = domain.lower()
    if check_str.startswith('www.'):
        check_str = check_str[4:]
    if check_str.endswith('/'):
        check_str = check_str[:-1]
    
    s = check_str
    found_patterns = []

    for i in range(len(s) - 2):
        if s[i] == s[i+1] == s[i+2]:
            seq = s[i:i+3]
            if seq not in found_patterns:
                found_patterns.append(seq)

    cyclic_pairs = ['rn', 'vv', 'cl', 'ii', 'mm', 'nn']
    for pat in cyclic_pairs:
        if pat in s and pat not in found_patterns:
            found_patterns.append(pat)

    if found_patterns:
        return True, f"Detected repeating / confusing patterns: {', '.join(found_patterns)}"
    return False, "None"

def normalize_domain(domain):
    notes = []
    normalized = domain.lower().strip()

    digit_map = {
        '0': 'o',
        '1': 'l',
        '3': 'e',
        '5': 's',
        '7': 't',
        '4': 'a',
        '6': 'b',
        '9': 'g'
    }
    digit_normalized = ''.join(digit_map.get(c, c) for c in normalized)
    if digit_normalized != normalized:
        notes.append(f"Digit substitutions applied ({sum(1 for c in normalized if c in digit_map)})")
    normalized = digit_normalized

    homoglyph_map = {
        'а': ('a', "Cyrillic 'а' looks like Latin 'a'"),
        'в': ('b', "Cyrillic 'в' looks like Latin 'b'"),
        'с': ('c', "Cyrillic 'с' looks like Latin 'c'"),
        'е': ('e', "Cyrillic 'е' looks like Latin 'e'"),
        'һ': ('h', "Cyrillic 'һ' looks like Latin 'h'"),
        'і': ('i', "Cyrillic 'і' looks like Latin 'i'"),
        'ј': ('j', "Cyrillic 'ј' looks like Latin 'j'"),
        'к': ('k', "Cyrillic 'к' looks like Latin 'k'"),
        'ӏ': ('l', "Cyrillic 'ӏ' looks like Latin 'l'"),
        'м': ('m', "Cyrillic 'м' looks like Latin 'm'"),
        'ո': ('n', "Cyrillic 'ո' looks like Latin 'n'"),
        'о': ('o', "Cyrillic 'о' looks like Latin 'o'"),
        'р': ('p', "Cyrillic 'р' looks like Latin 'p'"),
        'ѕ': ('s', "Cyrillic 'ѕ' looks like Latin 's'"),
        'у': ('y', "Cyrillic 'у' looks like Latin 'y'"),
        'х': ('x', "Cyrillic 'х' looks like Latin 'x'"),
    }

    for cyr_char, (latin_char, note) in homoglyph_map.items():
        if cyr_char in normalized:
            notes.append(note)
            normalized = normalized.replace(cyr_char, latin_char)

    for zw in ['\u200c', '\u200d', '\ufeff', '\u200b']:
        if zw in normalized:
            notes.append("Zero-width character removed during normalization")
            normalized = normalized.replace(zw, '')

    return normalized, notes

# Brand in content
def detect_brand_in_content(html_content, brands):
    if not html_content:
        return False
    soup = BeautifulSoup(html_content, 'html.parser')
    text = ''
    for tag in soup.find_all(['title', 'h1', 'h2', 'label', 'input', 'button', 'p', 'div']):
        if tag.string:
            text += tag.string + ' '
        if tag.get('placeholder'):
            text += tag['placeholder'] + ' '
    text = text.lower()
    return any(brand.lower() in text for brand in brands)

# Harvest intent
def detect_harvest_intent(html_content):
    if not html_content:
        return False
    soup = BeautifulSoup(html_content, 'html.parser')
    lower = html_content.lower()
    has_login = soup.find('input', {'type': 'password'}) or 'password' in lower or 'login' in lower
    has_payment = 'card number' in lower or 'cvv' in lower or 'expiry' in lower or 'pay now' in lower
    return has_login or has_payment

# Fallback function (fixed and complete)
def apply_fallback_minimal_scoring(score, factors, has_cyrillic, has_misleading_digits, has_redirect, is_free_cert, brand_in_domain, brand_in_content):
    if brand_in_domain or brand_in_content:
        return score
    
    if score != 0:
        return score
    
    if has_redirect:
        score += 3
    if is_free_cert:
        score += 5
    if has_cyrillic:
        score += 10
    if has_misleading_digits:
        score += 7
    
    if score == 0:
        score += 3
    
    return score

# ============================================
# SCANNING FUNCTIONS
# ============================================

def parse_domain(user_input):
    try:
        if not user_input or not user_input.strip():
            return False, "❌ No input provided"
        user_input = user_input.strip()
        parsed = urlparse(user_input)
        if parsed.scheme:
            domain = parsed.netloc
        else:
            parsed = urlparse("http://" + user_input)
            domain = parsed.netloc
        if not domain:
            return False, "❌ invalid url or domain"
        if "." not in domain:
            return False, "❌ invalid domain format"
        if domain.startswith('.') or domain.endswith('.'):
            return False, "❌ invalid url pattern"
        if '..' in domain:
            return False, "❌ wrong domain format"
        return True, domain.lower()
    except Exception as e:
        return False, f"❌ unexpected parsing error: {e}"

def http_status_check(domain, timeout=5):
    if not domain.startswith(("http://", "https://")):
        domain = "https://" + domain
    try:
        response = requests.get(domain, timeout=timeout, allow_redirects=False)
        status_code = response.status_code

        if status_code == 403:
            return "unreachable: request denied by server (403 Forbidden - likely bot/WAF protection)", status_code

        if 200 <= status_code < 300:
            return "reachable", status_code
        elif 300 <= status_code < 400:
            return "redirect", status_code
        else:
            return "unreachable", status_code
    except requests.exceptions.RequestException:
        return "unreachable", None

def ssl_check(domain):
    if not domain.startswith("https://"):
        domain = "https://" + domain
    host = domain.replace("https://", "").split('/')[0]
    
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert['issuer']).get('commonName', 'Unknown')

                le_intermediates = [
                    "E5", "E6", "E7", "E8", "E9",
                    "R3", "R10", "R11", "R12", "R13", "R14",
                    "YE1", "YE2", "YE3", "YR1", "YR2", "YR3",
                    "WE1"
                ]
                is_lets_encrypt = any(inter in issuer.upper() for inter in le_intermediates) or "ISRG" in issuer or "Let's Encrypt" in issuer

                expiry = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                
                free_keywords = ["Let's Encrypt", "R3", "ZeroSSL", "Google Trust Services", 
                                 "Fake LE Intermediate", "Sectigo Free", "ISRG Root X1"]
                is_free = any(kw in issuer for kw in free_keywords) or is_lets_encrypt
                cert_type = "valid (free / Let's Encrypt)" if is_free else "valid (paid)"
                
                return cert_type, issuer, expiry
    except Exception:
        return "invalid", None, None

def domain_age_whois(domain: str):
    try:
        w = whois.whois(domain)
        creation = w.creation_date
        expiry = w.expiration_date
        
        if isinstance(creation, list):
            creation = creation[0]
        if isinstance(expiry, list):
            expiry = expiry[0]
        
        if not isinstance(creation, datetime) or not isinstance(expiry, datetime):
            return None
        
        if creation.tzinfo:
            creation = creation.replace(tzinfo=None)
        if expiry.tzinfo:
            expiry = expiry.replace(tzinfo=None)
        
        now = datetime.utcnow()
        delta = now - creation
        age_months = delta.days // 30
        age_years = age_months // 12
        
        risk = "🟢 Low: domain is old enough and safe ✅"
        if age_months < 6:
            risk = "🔴 Very young: <6 months ❗"
        elif age_months < 12:
            risk = "🟠 Young: <12 months ⚠️"
        elif age_months < 36:
            risk = "🟡 Medium: <3 years"
        else:
            risk = "🟢 Low: domain is old enough and safe ✅"
        
        return {
            "creation_date": creation,
            "expiry_date": expiry,
            "age_months": age_months,
            "age_years": age_years,
            "risk_level": risk
        }
    except Exception:
        return None

def calculate_risk_score(brand_detected, factors, age_months=None, redirect_code=None):
    score = 0

    if brand_detected:
        if "invalid_ssl" in factors:
            score += 25
        if "free_ssl" in factors:
            score += 20
        if "unreachable" in factors:
            score += 22
        if "suspicious_patterns" in factors:
            score += 25
        if age_months is not None and age_months < 36:
            score += 28

        if redirect_code in (305, 307):
            score += 12

    else:
        if "invalid_ssl" in factors:
            score += 12
        if "free_ssl" in factors:
            score += 8
        if "unreachable" in factors:
            score += 15
        if "redirect" in factors:
            score += 6
        if "privacy_protected" in factors:
            score += 7
        if "suspicious_patterns" in factors:
            score += 12
        if age_months is not None:
            if age_months < 6:
                score += 18
            elif age_months < 12:
                score += 10
            elif age_months < 24:
                score += 5

    if not any(f in factors for f in ["invalid_ssl", "free_ssl", "unreachable", "suspicious_patterns"]):
        score = max(0, score - 15)

    return max(0, min(score, 100))

# ============================================
# MAIN SCAN FUNCTION
# ============================================

def scan_single_domain(domain_input):
    start_time = time.time()
    
    print(f"\n\033[1;36m🔍 Starting scan for:\033[0m {domain_input}")
    
    spinner(0.8, "Parsing domain")
    valid, domain_or_error = parse_domain(domain_input)
    if not valid:
        print(f"\033[1;31m❌ {domain_input}: {domain_or_error}\033[0m")
        return
    domain = domain_or_error
    print(f"  → Parsed: \033[1;32m{domain} ✅\033[0m")

    spinner(1.0, "Checking HTTP status & redirects")
    status, code = http_status_check(domain)

    page_content = None
    if status == "reachable" and code and 200 <= code < 300:
        try:
            resp = requests.get(f"https://{domain}", timeout=8, allow_redirects=True)
            if resp.status_code == 200:
                page_content = resp.text
        except:
            pass

    if status == "redirect":
        print(f"  → \033[1;33mRedirect detected\033[0m (code: {code}) 🔄")
    else:
        print(f"  → Status: \033[1;33m{status}\033[0m (code: {code if code else 'N/A'})")

    spinner(1.2, "Checking SSL certificate")
    ssl_status, issuer, expiry = ssl_check(domain)
    if "valid" in ssl_status:
        print(f"  → SSL: \033[1;32m{ssl_status}\033[0m 🔒")
        print(f"  → Issuer: {issuer}")
        if expiry:
            print(f"  → Expires: {expiry.strftime('%Y-%m-%d')} 📅")
    else:
        print("  → SSL invalid or missing ❌")

    spinner(1.4, "Checking domain age (WHOIS)")
    whois_info = domain_age_whois(domain)
    privacy_protected = whois_info is None
    age_months = whois_info["age_months"] if whois_info else None
    if whois_info:
        print(f"  → Age ≈ {whois_info['age_years']} years ⏳")
    else:
        print("  → WHOIS info unavailable (privacy protected?) 🕵️")

    spinner(0.7, "Checking leetspeak / misleading numbers")
    misleading_found, misleading_msg = has_misleading_numbers(domain)
    print(f"  → {misleading_msg}")

    spinner(0.7, "Checking cyclic / repeating patterns")
    cyclic_found, cyclic_msg = has_cyclic_characters(domain)
    print(f"  → {cyclic_msg}")

    spinner(0.9, "Normalizing domain & detecting homoglyphs")
    normalized_domain, homoglyph_notes = normalize_domain(domain)
    print(f"  → Normalized: {normalized_domain}")

    brand_check_input = normalized_domain
    brand_in_domain = any(brand in brand_check_input for brand in BIG_BRANDS)

    brand_in_content = False
    if page_content:
        brand_in_content = detect_brand_in_content(page_content, BIG_BRANDS)

    if brand_in_domain:
        print("  → Brand pattern matched in domain 🎭")
    if brand_in_content:
        print("  → Brand pattern matched in page content/login form 🎭")

    harvest_intent = False
    if page_content:
        harvest_intent = detect_harvest_intent(page_content)

    factors = set()
    if status == "redirect":        factors.add("redirect")
    if status == "unreachable":     factors.add("unreachable")
    if "valid (free)" in ssl_status: factors.add("free_ssl")
    if "invalid" in ssl_status:     factors.add("invalid_ssl")
    if privacy_protected:           factors.add("privacy_protected")
    if misleading_found or cyclic_found or homoglyph_notes:
                                    factors.add("suspicious_patterns")
    if harvest_intent:
                                    factors.add("harvest_intent")

    if code == 403:
        factors.discard("unreachable")

    score = calculate_risk_score(
        brand_detected=brand_in_domain,
        factors=factors,
        age_months=age_months,
        redirect_code=code if status == "redirect" else None
    )

    is_free_cert = "valid (free" in ssl_status
    if brand_in_domain and is_free_cert:
        score += 15
        print("  → +15 : Brand in domain + free certificate")

    if brand_in_content and not brand_in_domain:
        score += 20
        print("  → +20 : Brand impersonation in login form/page but not in domain")

    has_cyrillic = any(0x0400 <= ord(c) <= 0x04FF or 0x0500 <= ord(c) <= 0x052F for c in normalized_domain)
    if page_content:
        has_cyrillic = has_cyrillic or any(0x0400 <= ord(c) <= 0x04FF or 0x0500 <= ord(c) <= 0x052F for c in page_content[:5000])

    has_misleading = misleading_found
    has_redirect = "redirect" in factors

    score = apply_fallback_minimal_scoring(
        score,
        factors,
        has_cyrillic,
        has_misleading,
        has_redirect,
        is_free_cert,
        brand_in_domain,
        brand_in_content   # Fixed: now passing the 8th argument
    )

    elapsed = time.time() - start_time

    print("\n" + "═"*60)
    print("  🛡️ SCAN RESULT 🛡️".center(60))
    print("═"*60)
    print(f"  Original    : {domain}")
    print(f"  Normalized  : {normalized_domain}")
    print(f"  ⏱️ Scan time : {elapsed:.2f} seconds")
    if score <= 12:
        print(f"  Verdict     : ✅ SAFE")
    elif score <= 28:
        print(f"  Verdict     : ⚠️ WARNING")
    else:
        print(f"  Verdict     : 🚨 SUSPICIOUS")
    print(f"  Score       : {score}")
    print("═"*60 + "\n")

    if harvest_intent and score > 12:
        print("  → Login/payment form detected (potential credential or card harvesting) 💳")

    if homoglyph_notes:
        print("Homoglyph / normalization notes:")
        for note in homoglyph_notes:
            print(f"  - {note}")

    console_mgr.display_explanation(score, factors)

# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("domains", nargs="*", help="Domains/URLs to scan")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--help", action="store_true")

    args, unknown = parser.parse_known_args()

    if args.install:
        install_script()
        return
    if args.uninstall:
        uninstall_script()
        return
    if args.help or (not args.domains and not unknown):
        show_install_help()
        return

    domains = args.domains
    if not domains and not sys.stdin.isatty():
        domains = [line.strip() for line in sys.stdin if line.strip()]

    if not domains:
        console_mgr.print_message("No domains provided. Use --help for usage.", "red")
        return

    display_minecraft_banner()

    for domain_input in domains:
        scan_single_domain(domain_input)

if __name__ == "__main__":
    main()