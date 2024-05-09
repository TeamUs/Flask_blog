from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
import pandas as pd
import numpy as np
from gradient_boosting import GradientBoostingModel
from polynomial_regression import PolynomialRegressionModel
from rnn import RNNModel

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key_here"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:root@db:3306/blog"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Themes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(45), nullable=False)


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    theme_id = db.Column(db.Integer, db.ForeignKey("themes.id"))
    language = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    author = db.relationship("Users", backref="posts", lazy=True)
    theme = db.relationship("Themes", backref="posts", lazy=True)

@app.before_request
def create_db_schema():
    db.create_all()

@app.before_request
def set_default_language():
    if 'language' not in session:
        session['language'] = 'ru'


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def index():
    language = session.get('language')
    themes = Themes.query.all()
    pagination = Posts.query.filter_by(language=language).paginate(per_page=1)
    posts = pagination.items
    return render_template('index.html', posts=posts, themes=themes, language=language, pagination=pagination)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Users.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({"success": True, "message": "Logged in successfully"}), 200, {"Content-Type": "application/json"}
        return jsonify({"success": False, "message": "Invalid username or password"}), 401, {"Content-Type": "application/json"}
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        if not username or not email or not password:
            return jsonify({"success": False, "message": "Please fill in all fields"}), 400, {"Content-Type": "application/json"}
        user = Users.query.filter_by(username=username).first()
        if user:
            return jsonify({"success": False, "message": "Username already exists"}), 400, {"Content-Type": "application/json"}
        user = Users(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        user = Users.query.filter_by(username=username).first()
        login_user(user)
        return jsonify({"success": True, "message": "Registered successfully"}), 201, {"Content-Type": "application/json"}
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully!")
    return redirect(url_for("index"))

@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    language = session.get('language')
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        theme_id = request.form["theme_id"]
        language = request.form["language"]
        post = Posts(title=title, content=content, author_id=current_user.id, theme_id=theme_id, language=language)
        db.session.add(post)
        db.session.commit()
        flash("Post created successfully!")
        return redirect(url_for("index"))
    themes = Themes.query.all()
    return render_template("create_post.html", themes=themes, language=language)

@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    language = session.get('language')
    post = Posts.query.get_or_404(post_id)
    if post.author_id != current_user.id and current_user.is_admin != True:
        flash("You are not authorized to edit this post")
        return redirect(url_for("index"))
    if request.method == "POST":
        post.title = request.form["title"]
        post.content = request.form["content"]
        post.theme_id = request.form["theme_id"]
        post.language = request.form["language"]
        db.session.commit()
        flash("Post updated successfully!")
        return redirect(url_for("index"))
    themes = Themes.query.all()
    return render_template("edit_post.html", post=post, themes=themes, language=language)

@app.route("/delete_post/<int:post_id>")
@login_required
def delete_post(post_id):
    post = Posts.query.get_or_404(post_id)
    if post.author_id != current_user.id and current_user.is_admin != True:
        flash("You are not authorized to delete this post")
        return redirect(url_for("index"))
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully!")
    return redirect(url_for("index"))

@app.route("/admin_panel")
@login_required
def admin_panel():
    language = session.get('language')
    if not current_user.is_admin:
        flash("You are not authorized to access this page")
        return redirect(url_for("index"))
    posts = Posts.query.all()
    themes = Themes.query.all()
    return render_template("admin_panel.html", posts=posts, themes=themes, language=language)

@app.route("/admin_edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def admin_edit_post(post_id):
    language = session.get('language')
    themes = Themes.query.all()
    if not current_user.is_admin:
        flash("You are not authorized to access this page")
        return redirect(url_for("index"))
    post = Posts.query.get_or_404(post_id)
    if request.method == "POST":
        post.title = request.form["title"]
        post.content = request.form["content"]
        post.theme_id = request.form["theme_id"]
        post.language = request.form["language"]
        db.session.commit()
        flash("Post updated successfully!")
        return redirect(url_for("admin_panel", themes=themes, language=language))
    themes = Themes.query.all()
    return render_template("admin_edit_post.html", post=post, themes=themes, language=language)

@app.route("/admin_delete_post/<int:post_id>")
@login_required
def admin_delete_post(post_id):
    if not current_user.is_admin:
        flash("You are not authorized to access this page")
        return redirect(url_for("index"))
    post = Posts.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully!")
    return redirect(url_for("admin_panel"))

@app.route("/admin_create_theme", methods=["GET", "POST"])
@login_required
def admin_create_theme():
    language = session.get('language')
    if not current_user.is_admin:
        flash("You are not authorized to access this page")
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form["name"]
        name_en = request.form["name_en"]
        theme = Themes(name=name, name_en=name_en)
        db.session.add(theme)
        db.session.commit()
        flash("Theme created successfully!")
        return redirect(url_for("admin_panel"))
    return render_template("admin_create_theme.html", language=language)
@app.route("/admin_edit_theme/<int:theme_id>", methods=["GET", "POST"])
@login_required
def admin_edit_theme(theme_id):
    language = session.get('language')
    if not current_user.is_admin:
        flash("You are not authorized to access this page")
        return redirect(url_for("index"))
    theme = Themes.query.get_or_404(theme_id)
    if request.method == "POST":
        theme.name = request.form["name"]
        theme.name_en = request.form["name_en"]
        db.session.commit()
        flash("Theme updated successfully!")
        return redirect(url_for("admin_panel"))
    return render_template("admin_edit_theme.html", theme=theme, language=language)

@app.route("/admin_delete_theme/<int:theme_id>")
@login_required
def admin_delete_theme(theme_id):
    if not current_user.is_admin:
        flash("You are not authorized to access this page")
        return redirect(url_for("index"))
    theme = Themes.query.get_or_404(theme_id)
    db.session.delete(theme)
    db.session.commit()
    flash("Theme deleted successfully!")
    return redirect(url_for("admin_panel"))

@app.route('/theme/<int:theme_id>')
def theme_posts(theme_id):
    language = session.get('language')
    theme = Themes.query.get_or_404(theme_id)
    themes = Themes.query.all()
    posts = Posts.query.filter_by(theme_id=theme_id).all()
    pagination = Posts.query.filter_by(language=language, theme_id=theme_id).paginate(per_page=2)
    posts = pagination.items
    return render_template('theme_posts.html', theme=theme, posts=posts, themes=themes, language=language, pagination=pagination)

@app.route("/post/<int:post_id>")
def post_detail(post_id):
    language = session.get('language')
    themes = Themes.query.all()
    post = Posts.query.get_or_404(post_id)
    return render_template("post_detail.html", post=post, themes=themes, language=language)

@app.route('/edit_user', methods=['GET', 'POST'])
@login_required
def edit_user():
    language = session.get('language')
    themes = Themes.query.all()
    if request.method == 'POST':
        new_password = request.form['password']
        new_password_r = request.form['confirm_password']
        email = request.form['email']
        new_username = request.form['username']
        if new_password and new_password == new_password_r:
            current_user.set_password(new_password)
        if new_username:
            current_user.username = new_username
        if email:
            current_user.email = email
        db.session.commit()
        flash('User data updated successfully!')
        return redirect(url_for('index'))
    return render_template('edit_user.html', themes=themes, language=language)


@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    language = session.get('language')
    themes = Themes.query.all()
    return render_template('contacts.html', themes=themes, language=language)

@app.route('/model', methods=['GET', 'POST'])
def model():
    language = session.get('language')
    themes = Themes.query.all()
    if request.method == 'POST':
        model_choice = request.form['model']
        # Load training data from a CSV file
        train_data = pd.read_csv('titanic_data.csv')
        train_data = train_data[train_data['is_test'] == 0]
        X_train = train_data.drop(columns=['Survived', 'is_test'])
        y_train = train_data['Survived']
        X_train = X_train.astype('float32')
        if model_choice == 'gradient_boosting':
            model = GradientBoostingModel()
        elif model_choice == 'polynomial_regression':
            model = PolynomialRegressionModel()
        elif model_choice == 'rnn':
            # Normalize continuous features
            X_train['Fare'] = (X_train['Fare'] - X_train['Fare'].mean()) / X_train['Fare'].std()
            X_train['Age'] = (X_train['Age'] - X_train['Age'].mean()) / X_train['Age'].std()
            model = RNNModel(X_train)
        model.train(X_train, y_train)
        # Train the model
        model.train(X_train, y_train)

            # Load test data from a CSV file
        test_data = pd.read_csv('titanic_data.csv')
        test_data = test_data[test_data['is_test'] == 1]
        X_test = test_data.drop(columns=['Survived', 'is_test'])
        X_test = X_test.astype('float32')

        # Get predictions
        predictions = model.predict(X_test)
        if model_choice == 'rnn':
            predictions = np.round(predictions).astype(int).flatten()

        # Combine test data with predictions
        test_data['Predicted'] = predictions.tolist()

        # Prepare data for rendering in template
        context = {
            'test_data': test_data.to_dict('records'),  # Convert DataFrame to list of dictionaries
        }

        return render_template('results.html', **context, language=language)
    return render_template('model.html', themes=themes, language=language) 

@app.route('/results', methods=['GET', 'POST'])
@login_required
def results():
    language = session.get('language')
    themes = Themes.query.all()
    return render_template('results.html', themes=themes, language=language)  

@app.route('/switch_language')
def switch_language():
    if session['language'] == 'ru':
        session['language'] = 'en'
    else:
        session['language'] = 'ru'
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')