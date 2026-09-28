<div align="center">

# 🛡️ SAKK
### Decentralized Cryptographic Document Verification Platform
> **Zero-Retention, Tamper-Proof Document Authentication for Digital Governments.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask-black.svg)](https://flask.palletsprojects.com/)
[![Security](https://img.shields.io/badge/Cryptography-ECDSA_SECP256R1-success.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](#)

*An elite submission for the **Global SAFE Security and Innovation Competition** (Digital Government Solutions Track).*

</div>

---

## 🌟 Overview
**SAKK** is a state-of-the-art cryptographic document verification platform designed for sovereign digital governance. 

In an era where document forgery (land deeds, security clearances, academic certificates) poses severe national security and economic threats, SAKK provides mathematical certainty. Using advanced **ECDSA (SECP256R1)** elliptic-curve cryptography combined with a strict **Zero-Retention architecture**, SAKK guarantees absolute document integrity without ever storing sensitive data on centralized servers.

## 🚀 Why SAKK? (The Competitive Edge)
* 🔐 **Zero-Retention Privacy:** We don't store the documents. We don't store the metadata. The data is cryptographically sealed directly into the physical/digital QR code. Absolute compliance with strict data protection laws (e.g., PDPL, GDPR).
* 🛡️ **Cryptographic Tamper Detection:** If a malicious actor alters a single pixel, date, or character in the document, the cryptographic hash breaks, and the system instantly rejects the document.
* ⚡ **Decentralized Inter-Agency Verification:** A bank or foreign embassy can instantly verify a government-issued document using only the public key. No complex API integrations or access to sensitive internal databases is required.
* 📄 **Multi-Page Intelligent Scanning:** Built-in AI/Computer Vision pipeline using `PyMuPDF` and `OpenCV` to automatically hunt and decode secure QR seals across large, multi-page PDFs.
* 🪄 **Transparent Aesthetic Seals:** Generates transparent, elegant QR codes that blend seamlessly into official documents without ruining their sovereign aesthetic.
* 📱 **Multi-Engine Decoding Pipeline:** Engineered with a highly robust fallback chain (`pyzbar` → `cv2.wechat_qrcode` → `cv2.QRCodeDetector`) ensuring flawless scanning even on low-quality physical prints or dense digital codes.

---

## 🏗️ System Architecture & Workflow

### 1. Issuance (The Cryptographic Binding)
1. **Hash Generation:** The system calculates a mathematically irreversible SHA-256 hash of the raw document.
2. **Dynamic Metadata:** Custom key-value pairs (e.g., `Issuer: Ministry of Interior`, `Clearance Level: Top Secret`) are canonically sorted and appended.
3. **ECDSA Signature:** The server signs the entire payload using its highly secure Elliptic Curve Private Key.
4. **Seal Creation:** A transparent QR code is generated containing the payload, hash, and signature, and is embedded into the document.

### 2. Verification (Zero-Trust Proof)
1. **Upload:** A third party uploads the document to the portal.
2. **Extraction:** The system scans the document, finds the QR code, and extracts the payload and signature.
3. **Re-Hashing:** The system re-hashes the uploaded file (excluding the QR region) and compares it to the payload.
4. **Mathematical Verification:** The system uses the Issuer's Public Key to cryptographically verify that the signature was indeed created by the trusted authority and hasn't been tampered with.

---

## 🛠️ Technology Stack
| Component | Technology |
|---|---|
| **Backend Framework** | Python 3.10+, Flask |
| **Cryptography** | `cryptography` (SECP256R1, SHA-256) |
| **Document Processing** | `PyMuPDF` (fitz), `Pillow` (PIL) |
| **Computer Vision** | `OpenCV` (cv2), `pyzbar` |
| **Frontend UI/UX** | HTML5, CSS3 (Glassmorphism), Vanilla JS |
| **Database** | SQLite (Strictly for Audit Logs & Public Keys) |

---

## ⚙️ Quick Start Guide

### Prerequisites
- Python 3.10+
- Git

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/your-username/sakk.git
cd sakk

# 2. Install required dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py
```

### ⚠️ Critical Security Notice
The system will automatically generate a highly secure `private_key.pem` upon first launch. 
**NEVER commit this file to GitHub!** Make sure your `.gitignore` is properly configured to exclude `*.pem` and `sakk.db` files.

---

## 🏆 Global SAFE Competition Profile
* **Track:** Digital Government Solutions
* **Value Proposition:** 
  * Eradicates physical and digital document forgery.
  * Eliminates centralized "honeypot" data breaches by removing the need to store sensitive document metadata.
  * Rapid deployment for any government entity seeking immediate cryptographic security.

---
<div align="center">
<i>Built with passion for a safer, trustless digital future.</i><br>
<b>Global SAFE Security and Innovation Competition</b>
</div>
