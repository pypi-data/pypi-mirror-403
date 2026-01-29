🛡️ UNPHISHABLE
Advanced Phishing Detection CLI Tool
Unphishable is a professional security tool that detects phishing domains using multi-layer pattern recognition. It analyzes domains through HTTP checks, SSL verification, WHOIS data, brand impersonation detection, and cyclic/misleading number patterns to provide comprehensive security assessments.
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/unphishable?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/unphishable)
✨ Features
🔍 Multi-layer analysis: Domain parsing, HTTP checks, SSL verification, WHOIS lookup
🏢 Brand detection & impersonation: Database of the top 200 most phished brands
🔢 Cyclic & misleading number detection: Identify tricky numeric patterns often used in phishing URLs
📊 Intelligent scoring: Pattern-based risk assessment
🎓 Educational explanations: Understand why a domain is considered risky
🚀 Auto-install: Works immediately, no manual dependencies
🎨 Beautiful CLI: Colored output, progress indicators, clean interface
🚀 Quick Install
Windows (recommended):
Copy code
Bash
py -m pip install unphishable
Linux/macOS:
Copy code
Bash
pip install unphishable
⚡ Tip: For existing users, upgrade to the latest version to get the new features:
Copy code
Bash
py -m pip install --upgrade unphishable   # Windows
pip install --upgrade unphishable         # Linux/macOS
🧪 Usage Example
Copy code
Bash
unphishable scan https://example.com
Output:
Copy code

URL: https://example.com
Risk Score: 75%
Reason: SSL certificate invalid, suspicious domain pattern
💡 How to Contribute
⭐ Star the repo: https://github.com/newtonachonduh
📝 Report issues or suggest features
🖼️ Share screenshots of CLI output if testing new features
🌍 Impact
By using and testing Unphishable, you’re helping make phishing detection smarter, faster, and more reliable for everyone.
👤 About the Creator
Unphishable is maintained by Newton Achonduh, a dedicated security researcher and software developer focused on building real-time phishing detection tools. Contributions, feedback, and community testing help ensure the tool remains reliable, accurate, and educational.