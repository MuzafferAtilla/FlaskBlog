from flask import Flask,render_template, request, url_for, redirect, flash, session
from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, validators, TextAreaField
from passlib.hash import sha256_crypt
from functools import wraps
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min = 4,max = 25),validators.optional()])
    username = StringField("User Name",validators=[validators.Length(min = 4,max = 35)])
    email = StringField("E-Posta",validators=[validators.Email(message="Düzgün e-mail giriniz")])
    password = PasswordField("Parola",validators=[
        validators.DataRequired(message="Parola belirleyiniz"),
        validators.EqualTo(fieldname = "confirm",message="Parolalar uyuşmuyor")
    ])
    confirm = PasswordField("Parola Doğrula")
class LoginForm(Form):
    username = StringField("User Name", validators=[validators.DataRequired()])
    password = PasswordField("Password")

class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min = 5,max = 25),validators.DataRequired()])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min = 10),validators.DataRequired()])


app = Flask(__name__)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)
app.secret_key = "Muzaffer Atilla"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntüleyebilmek için giriş yapın","danger")
            return redirect(url_for("login"))
    return decorated_function


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/article/<string:id>")
def detail(id):
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM articles WHERE id = %s",(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article = article)
    return render_template("article.html")

@app.route("/register", methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if(request.method == "POST" and form.validate()):

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users(name,username,email,password) VALUES(%s,%s,%s,%s)",(name,username,email,password))
        mysql.connection.commit()
        cursor.close()  

        flash("Başarıyla Kayıt Oldunuz","success")  

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)
@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if(request.method == "POST" and form.validate()):

        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM users WHERE username = %s"
        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):

                session["logged_in"] = True
                session["username"] = username

                flash("Başarılı bir şekilde giriş yaptınız","success")
                return redirect(url_for("index"))
            else:
                flash("Parola yanlış","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı yoktur","danger")
            return redirect(url_for("login"))


        flash("Başarıyla giriş yaptınız","success")
    else:
        return render_template("login.html", form = form)

@app.route("/logout")
def logout():
    session.clear()
    flash("Başarılı bir şekilde çıkış yaptınız","success")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM articles WHERE author = %s",(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)
    else:
        return render_template("dashboard.html")

@app.route("/addarticle", methods=["POST","GET"])
def addarticle():
    form = ArticleForm(request.form)
    if(request.method == "POST" and form.validate()):
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)",(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarıyla eklendi","success")
        return redirect(url_for("dashboard"))


    return render_template("addarticle.html",form = form)

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM articles")
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM articles WHERE author = %s AND id = %s",(session["username"],id))
    if result > 0:
        cursor.execute("DELETE FROM articles WHERE id = %s",(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Yetki yok veya böyle bir makale yok","danger")
        return redirect(url_for("index"))


@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def edit(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        result = cursor.execute("SELECT * FROM articles WHERE author = %s AND id = %s",(session["username"],id))
        if result > 0:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form = form)
        else:
            flash("Böyle bir makale yok yada yetkiniz yok","success")
            return redirect(url_for("index"))
    else:
        form = ArticleForm(request.form)
        cursor = mysql.connection.cursor()

        newtitle = form.title.data
        newcontent = form.content.data

        cursor.execute("UPDATE articles SET title = %s, content = %s WHERE id = %s",(newtitle,newcontent,id))
        mysql.connection.commit()

        flash("Makale başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))
@app.route("/search", methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = str(request.form.get("keyword"))
        cursor = mysql.connection.cursor()
        result = cursor.execute("SELECT * FROM articles WHERE title LIKE '%"+keyword+"%'")
        
        if result > 0:
            articles = cursor.fetchall()
            return render_template("articles.html", articles = articles)
        else:
            flash("Aradığınız kriterlere uygun makale yoktur","warning")
            return redirect(url_for("articles"))
if __name__ == "__main__":
    app.run(debug = True)


