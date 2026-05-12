from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from functools import wraps
from PIL import Image
import random
import base64
from io import BytesIO

app = Flask(__name__)

# Secret Key
app.secret_key = "your-secret-key"

# Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Max Upload Size = 500 MB
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Initialize DB + Bcrypt
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# =========================
# DATABASE MODEL
# =========================

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

# Create DB Tables
with app.app_context():
    db.create_all()

# =========================
# ANIMAL DATA
# =========================

class_names = [
    'Bear',
    'Bird',
    'Cat',
    'Cow',
    'Deer',
    'Dog',
    'Dolphin',
    'Elephant',
    'Giraffe',
    'Horse',
    'Kangaroo',
    'Lion',
    'Panda',
    'Tiger',
    'Zebra'
]

animal_facts = {

    'Bear':
    'Bears are excellent swimmers and can run up to 35 mph!',

    'Bird':
    'Birds are the only animals with feathers!',

    'Cat':
    'Cats sleep for 70% of their lives!',

    'Cow':
    'Cows have best friends and get stressed when separated!',

    'Deer':
    'Deer can run up to 30 mph and jump 8 feet high!',

    'Dog':
    'Dogs noses are wet to help absorb scent chemicals!',

    'Dolphin':
    'Dolphins sleep with one eye open!',

    'Elephant':
    'Elephants are the only mammals that cannot jump!',

    'Giraffe':
    'Giraffes have the same number of neck vertebrae as humans!',

    'Horse':
    'Horses can sleep both standing up and lying down!',

    'Kangaroo':
    'Kangaroos can jump 30 feet in one leap!',

    'Lion':
    'Lions are the only cats that live in groups!',

    'Panda':
    'Pandas spend 12 hours a day eating bamboo!',

    'Tiger':
    'Tiger stripes are unique like human fingerprints!',

    'Zebra':
    'Zebras are black with white stripes, not white with black!'
}

# Allowed Extensions
ALLOWED_EXTENSIONS = {
    'png',
    'jpg',
    'jpeg',
    'gif',
    'bmp',
    'webp'
}

def allowed_file(filename):

    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )

# =========================
# LOGIN DECORATOR
# =========================

def login_required(f):

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if 'user_id' not in session:

            flash('Please login first!')
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function

# =========================
# HOME
# =========================

@app.route('/')
def home():

    return redirect(url_for('login'))

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:

            flash('Username already exists!')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode('utf-8')

        new_user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful!')
        return redirect(url_for('login'))

    return render_template('register.html')

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username
        ).first()

        if user and bcrypt.check_password_hash(
            user.password,
            password
        ):

            session['user_id'] = user.id
            session['username'] = user.username

            flash(f'Welcome back, {username}!')

            return redirect(url_for('dashboard'))

        else:

            flash('Invalid username or password!')

    return render_template('login.html')

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
@login_required
def dashboard():

    return render_template(
        'dashboard.html',
        username=session.get('username')
    )

# =========================
# SINGLE IMAGE PREDICTION
# =========================

@app.route('/predict', methods=['POST'])
@login_required
def predict():

    try:

        if 'image' not in request.files:

            flash('No image uploaded!')
            return redirect(url_for('dashboard'))

        file = request.files['image']

        if file.filename == '':

            flash('No file selected!')
            return redirect(url_for('dashboard'))

        if not allowed_file(file.filename):

            flash('Invalid image format!')
            return redirect(url_for('dashboard'))

        # Open Image
        img = Image.open(file).convert('RGB')

        # Resize
        img.thumbnail((300, 300))

        # Convert to Base64
        buffer = BytesIO()

        img.save(
            buffer,
            format='JPEG'
        )

        img_base64 = base64.b64encode(
            buffer.getvalue()
        ).decode()

        # Fake Prediction
        prediction = random.choice(class_names)

        confidence = round(
            random.uniform(70, 98),
            1
        )

        fact = animal_facts.get(
            prediction,
            'Amazing animal!'
        )

        return render_template(
            'result.html',
            prediction=prediction,
            confidence=confidence,
            image=img_base64,
            fact=fact
        )

    except Exception as e:

        flash(f'Error: {str(e)}')

        return redirect(
            url_for('dashboard')
        )

# =========================
# BATCH PREDICTION
# =========================

@app.route('/predict-batch', methods=['POST'])
@login_required
def predict_batch():

    try:

        files = request.files.getlist('files')

        if not files:

            flash('No files selected!')

            return redirect(
                url_for('dashboard')
            )

        results = []

        for file in files:

            if file.filename == '':
                continue

            if not allowed_file(file.filename):
                continue

            try:

                img = Image.open(file).convert('RGB')

                img.thumbnail((250, 250))

                buffer = BytesIO()

                img.save(
                    buffer,
                    format='JPEG'
                )

                img_base64 = base64.b64encode(
                    buffer.getvalue()
                ).decode()

                prediction = random.choice(
                    class_names
                )

                confidence = round(
                    random.uniform(70, 98),
                    1
                )

                results.append({

                    'filename':
                    file.filename,

                    'prediction':
                    prediction,

                    'confidence':
                    confidence,

                    'image':
                    img_base64,

                    'fact':
                    animal_facts.get(prediction)

                })

            except Exception as e:

                print(e)

        return render_template(

            'batch_result.html',

            results=results,

            total=len(results)

        )

    except Exception as e:

        flash(str(e))

        return redirect(
            url_for('dashboard')
        )

# =========================
# LOGOUT
# =========================

@app.route('/logout')
@login_required
def logout():

    session.clear()

    flash('Logged out successfully!')

    return redirect(
        url_for('login')
    )

# =========================
# RUN FLASK APP
# =========================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
