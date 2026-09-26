import os
import sqlite3
import hashlib
import json
import base64
from datetime import datetime
from io import BytesIO

from flask import Flask, request, jsonify, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

import qrcode
import cv2
import numpy as np

app = Flask(__name__)
# In production, use a strong random secret key. Hardcoded here for simplicity across restarts in this demo.
app.secret_key = 'super_secret_cyber_key_sakk'

DB_FILE = 'sakk.db'
KEY_FILE = "private_key.pem"

PRIVATE_KEY = None
PUBLIC_KEY = None

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Audit Logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            file_hash TEXT,
            signature TEXT,
            timestamp TEXT
        )
    ''')
    # System Keys
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_keys (
            id INTEGER PRIMARY KEY,
            public_key TEXT
        )
    ''')
    # Users for Authentication
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')
    
    # Init default admin
    c.execute("SELECT id FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed = generate_password_hash("admin123")
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", hashed))
        
    conn.commit()
    conn.close()

def load_or_generate_keys():
    global PRIVATE_KEY, PUBLIC_KEY
    regenerate = False
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            try:
                PRIVATE_KEY = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                )
                if not isinstance(PRIVATE_KEY, ec.EllipticCurvePrivateKey):
                    regenerate = True
                else:
                    PUBLIC_KEY = PRIVATE_KEY.public_key()
            except Exception:
                regenerate = True
    else:
        regenerate = True
        
    if regenerate:
        # Generate ECDSA key
        PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
        PUBLIC_KEY = PRIVATE_KEY.public_key()
        
        pem = PRIVATE_KEY.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(pem)
            
        pub_pem = PUBLIC_KEY.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO system_keys (id, public_key) VALUES (1, ?)", (pub_pem.decode('utf-8'),))
        conn.commit()
        conn.close()

# Automatically initialize DB and keys on startup (supports WSGI / Gunicorn / Flask dev)
init_db()
load_or_generate_keys()

def is_logged_in():
    return session.get('logged_in', False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row and check_password_hash(row[0], password):
        session['logged_in'] = True
        session['username'] = username
        return jsonify({"success": True})
    
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/api/me', methods=['GET'])
def me():
    if is_logged_in():
        return jsonify({"logged_in": True, "username": session.get('username')})
    return jsonify({"logged_in": False})

@app.route('/api/sign', methods=['POST'])
def sign_file():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized access. Please login first.'}), 401
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename) or file.filename
    file_bytes = file.read()
    
    if not file_bytes:
        return jsonify({'error': 'Empty file'}), 400
        
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    # ECDSA Sign
    signature = PRIVATE_KEY.sign(
        bytes.fromhex(file_hash),
        ec.ECDSA(utils.Prehashed(hashes.SHA256()))
    )
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save to DB
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO audit_logs (filename, file_hash, signature, timestamp) VALUES (?, ?, ?, ?)",
              (filename, file_hash, signature_b64, timestamp))
    conn.commit()
    conn.close()
    
    # Generate QR Payload
    payload = {
        'filename': filename,
        'hash': file_hash,
        'signature': signature_b64,
        'timestamp': timestamp
    }
    payload_json = json.dumps(payload)
    
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payload_json)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white") # Reliable colors for OpenCV
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_bytes = buffered.getvalue()
    qr_b64 = base64.b64encode(qr_bytes).decode('utf-8')
    
    # Check if we should stamp PDF
    is_pdf_stamp = request.form.get('stamp_pdf') == 'true'
    final_file_b64 = None
    
    if is_pdf_stamp and filename.lower().endswith('.pdf'):
        try:
            import fitz  # PyMuPDF
            x_pct = float(request.form.get('x_pct', 0))
            y_pct = float(request.form.get('y_pct', 0))
            size_pct = float(request.form.get('size_pct', 0.2))
            
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page = doc[0]
            
            page_w = page.rect.width
            page_h = page.rect.height
            
            x0 = x_pct * page_w
            y0 = y_pct * page_h
            w = size_pct * page_w
            # Assuming QR code is square
            x1 = x0 + w
            y1 = y0 + w
            
            rect = fitz.Rect(x0, y0, x1, y1)
            page.insert_image(rect, stream=qr_bytes)
            
            out_pdf = BytesIO()
            doc.save(out_pdf)
            doc.close()
            final_file_b64 = base64.b64encode(out_pdf.getvalue()).decode('utf-8')
        except Exception as e:
            print("PDF Stamping Error:", e)
            pass
    
    return jsonify({
        'filename': filename,
        'hash': file_hash,
        'signature': signature_b64,
        'timestamp': timestamp,
        'qr_image': f"data:image/png;base64,{qr_b64}",
        'stamped_pdf': final_file_b64
    })

@app.route('/api/verify', methods=['POST'])
def verify_file():
    if 'file' not in request.files or 'signature' not in request.form:
        return jsonify({'error': 'File and signature are required'}), 400
    
    file = request.files['file']
    signature_b64 = request.form['signature']
    tamper = request.form.get('tamper', 'false').lower() == 'true'
    
    file_bytes = file.read()
    if not file_bytes:
        return jsonify({'error': 'Empty file'}), 400
        
    if tamper:
        file_bytes += b"tampered_malicious_payload_x09283"
        
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    is_valid = False
    try:
        signature = base64.b64decode(signature_b64)
        PUBLIC_KEY.verify(
            signature,
            bytes.fromhex(file_hash),
            ec.ECDSA(utils.Prehashed(hashes.SHA256()))
        )
        is_valid = True
    except InvalidSignature:
        is_valid = False
    except Exception as e:
        is_valid = False
        
    return jsonify({
        'valid': is_valid,
        'hash': file_hash,
        'filename': file.filename
    })

@app.route('/api/verify-qr', methods=['POST'])
def verify_qr():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    filename = secure_filename(file.filename) or file.filename
    file_bytes = file.read()
    
    if not file_bytes:
        return jsonify({'error': 'Empty file'}), 400
        
    img = None
    
    if filename.lower().endswith('.pdf'):
        try:
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page = doc[0]
            # Render the first page to a high-res image
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            doc.close()
        except Exception as e:
            return jsonify({'error': f'Failed to parse PDF for QR extraction: {str(e)}'}), 400
    else:
        # Read image from bytes directly
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return jsonify({'error': 'Invalid format. Must be an image or PDF.'}), 400
        
    detector = cv2.QRCodeDetector()
    data, bbox, straight_qrcode = detector.detectAndDecode(img)
    
    if not data:
        return jsonify({'error': 'No QR code found in the file or could not decode it. Ensure the image/document is clear.'}), 400
        
    try:
        payload = json.loads(data)
        file_hash = payload['hash']
        signature_b64 = payload['signature']
        
        signature = base64.b64decode(signature_b64)
        PUBLIC_KEY.verify(
            signature,
            bytes.fromhex(file_hash),
            ec.ECDSA(utils.Prehashed(hashes.SHA256()))
        )
        is_valid = True
    except InvalidSignature:
        is_valid = False
    except Exception as e:
        return jsonify({'error': f'Invalid QR data structure or corrupted cryptographic signature. Details: {str(e)}'}), 400
        
    return jsonify({
        'valid': is_valid,
        'payload': payload
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, filename, file_hash, signature, timestamp FROM audit_logs ORDER BY id DESC LIMIT 15")
    rows = c.fetchall()
    conn.close()
    
    logs = []
    for r in rows:
        logs.append({
            'id': r[0],
            'filename': r[1],
            'hash': r[2],
            'signature': r[3][:25] + "...",
            'timestamp': r[4]
        })
    return jsonify(logs)

if __name__ == '__main__':
    init_db()
    load_or_generate_keys()
    app.run(debug=True, port=5000)
