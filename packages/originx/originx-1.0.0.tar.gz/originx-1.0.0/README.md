# OriginX - WAF Origin IP Discovery Tool

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/originx.svg)](https://badge.fury.io/py/originx)

**Professional WAF Origin IP Discovery Tool for Bug Bounty & Security Research**

OriginX is a powerful, async-based reconnaissance tool designed to discover origin IP addresses hidden behind WAF/CDN providers using passive, historical, and correlation-based techniques. Built for bug bounty hunters and security researchers.

## [*] Installation

### From PyPI (Recommended)
```bash
pip install originx
```

### From Source
```bash
git clone https://github.com/letchupkt/originx.git
cd originx
pip install -e .
```

## 🔧 API Configuration

OriginX works with free sources out of the box, but API keys unlock its full potential:

```bash
# Shodan (Recommended)
export SHODAN_API_KEY="your_shodan_key"

# Censys
export CENSYS_API_ID="your_censys_id"
export CENSYS_API_SECRET="your_censys_secret"

# VirusTotal
export VIRUSTOTAL_API_KEY="your_vt_key"

# SecurityTrails
export SECURITYTRAILS_API_KEY="your_st_key"
```

Check configuration status:
```bash
originx config
```

## [*] Usage

### Interactive Menu Mode (Recommended)
```bash
originx
```

### Command Line Mode
```bash
# Quick scan
originx scan example.com

# Deep scan with all sources
originx scan example.com --deep --shodan --censys --vt --securitytrails

# Passive reconnaissance only
originx scan example.com --passive-only

# Favicon hash hunt
originx scan example.com --favicon

# Custom confidence threshold
originx scan example.com --confidence-threshold 80

# Export results
originx scan example.com --json results.json
```

### Advanced Examples
```bash
# Fast scan for quick results
originx scan target.com --fast --verify

# Comprehensive deep scan
originx scan target.com \
  --deep \
  --shodan \
  --censys \
  --vt \
  --securitytrails \
  --favicon \
  --confidence-threshold 70 \
  --json detailed_report.json

# Passive recon with custom timeout
originx scan target.com --passive-only --timeout 45
```

## [*] Output Formats

### Table Format (Default)
```
[>>] SCAN RESULTS FOR EXAMPLE.COM
Duration: 12.3s | Sources: dns, shodan, censys, virustotal

🔥 LIKELY ORIGIN SERVERS (80%+ confidence):
  • 1.2.3.4 (Confidence: 95%)
  • 5.6.7.8 (Confidence: 87%)

┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┓
┃ IP Address    ┃ Source        ┃ Confidence ┃ Port   ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━┩
│ 1.2.3.4       │ shodan        │ 95%        │ 443    │
│ 5.6.7.8       │ censys        │ 87%        │ 80     │
└───────────────┴───────────────┴────────────┴────────┘
```

### JSON Format
```bash
originx scan example.com --output json
```

### Text Format
```bash
originx scan example.com --output txt
```

## 🧠 Reconnaissance Modules

| Module | Description | API Required |
|--------|-------------|--------------|
| **DNS** | A records, SPF, subdomains | [-] |
| **Shodan** | Hostname, SSL cert, favicon hash | [+] |
| **Censys** | Certificate transparency, hostname | [+] |
| **VirusTotal** | Passive DNS, domain resolutions | [+] |
| **SecurityTrails** | Historical DNS, subdomains | [+] |
| **ViewDNS** | IP history, reverse IP | [-] |
| **AlienVault OTX** | Passive DNS data | [-] |
| **Favicon Hash** | MurmurHash3 correlation | [-] |

## [*] Verification Engine

OriginX includes a sophisticated verification engine that:

- **Direct IP Testing**: Tests direct connections to candidate IPs
- **Host Header Override**: Bypasses simple WAF configurations
- **SSL Certificate Matching**: Validates certificate subject/SAN fields
- **Content Similarity**: Compares response content with original
- **WAF Detection**: Identifies WAF responses in verification
- **Confidence Scoring**: Provides 0-100 confidence scores

## [*] Interactive Menu

Launch the interactive menu for guided scanning:

```
[*] ORIGINX MAIN MENU

[1] Quick Scan (Fast reconnaissance)
[2] Deep Scan (Comprehensive analysis)
[3] Passive Recon Only
[4] Favicon Hash Hunt
[5] Verify Candidate IPs
[6] View Last Scan Results
[7] Export Report
[8] API Status
[0] Exit
```

## 📋 Example Workflow

1. **Start with Quick Scan**: Get rapid results for immediate analysis
2. **Deep Scan for Comprehensive Data**: Use all available sources
3. **Favicon Hash Hunt**: Find servers with identical favicons
4. **Manual Verification**: Test specific IP candidates
5. **Export Results**: Save findings in preferred format

## [!] Ethical Use

**[!] IMPORTANT: This tool is for authorized security research only**

- [+] Bug bounty programs with proper scope
- [+] Authorized penetration testing
- [+] Your own infrastructure assessment
- [+] Educational and research purposes

- [-] Unauthorized scanning
- [-] Malicious activities
- [-] Violating terms of service
- [-] Illegal reconnaissance

## 🔒 Rate Limiting & Safety

OriginX implements responsible scanning practices:

- **Automatic rate limiting** for all API sources
- **Configurable timeouts** and concurrency limits
- **Graceful error handling** for API failures
- **Respect for robots.txt** and terms of service

## 🐛 Troubleshooting

### Common Issues

**No results found:**
- Check API key configuration with `originx config`
- Verify domain is accessible and not typo'd
- Try different confidence thresholds

**API rate limits:**
- Reduce `--max-concurrent` parameter
- Increase `--timeout` for slower responses
- Use `--fast` mode for fewer API calls

**SSL/TLS errors:**
- Some verification may fail on misconfigured SSL
- This is expected behavior for origin discovery

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests, report bugs, or suggest features.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**LAKSHMIKANTHAN K (letchupkt)**
- Bug Bounty Hunter & Security Researcher
- Specialized in Web Application Security

## 🙏 Acknowledgments

- Thanks to all the API providers (Shodan, Censys, VirusTotal, SecurityTrails)
- Inspired by the bug bounty and security research community
- Built with love for ethical hackers worldwide

## ⭐ Star History

If you find OriginX useful, please consider giving it a star on GitHub!

---

**Happy Hunting! [*]**