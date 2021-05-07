from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.handlers.sha2_crypt import sha256_crypt
from functools import wraps
import os
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

UPLOAD_FOLDER = '/static'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

#Kullanıcı Giriş Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın","danger")
            return redirect(url_for("login"))

    return decorated_function

#Kullanıcı kayıt formu
class RegisterForm(Form):
    name = StringField("İsim ve soyisim:",validators=[validators.length(min = 4,max = 20)])
    nickname = StringField("Kullanıcı Adı:",validators=[validators.length(min = 4,max = 10)])
    email = StringField("Email:",validators=[(validators.Email(message= "Lütfen geçerli bir email adresi giriniz."))])
    password = PasswordField("Parola:",validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin."),
        validators.EqualTo(fieldname = "confirm",message= "Parolanız Uyuşmuyor...")
    ])
    confirm = PasswordField("Parola Doğrula")

class LoginForm(Form):
    nickname = StringField("Kullanıcı Adı:")
    password = PasswordField("Şifre:")

app = Flask(__name__)
app.config["DEBUG"] = True

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="emreris",
    password="suleymanemreeris.2001",
    hostname="emreris.mysql.pythonanywhere-services.com",
    databasename="emreris$erisblog",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

app.secret_key = "erisblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "erisblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)
@app.route("/")
def emre():

    return render_template("index.html")
@app.route("/about")
def about():
    return render_template("about.html")

#Makale Sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    
    sorgu = "SELECT * FROM articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)

    else:
        return render_template("articles.html")


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM articles where author = %s"

    result = cursor.execute(sorgu,(session["nickname"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)

    else:
        return render_template("dashboard.html")


@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        nickname = form.nickname.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        
        sorgu = "INSERT INTO users(name,email,nickname,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,nickname,password))
        mysql.connection.commit()

        cursor.close()

        flash("Başarıyla kayıt oldunuz...","success")


        return redirect(url_for("login"))

    else:
        return render_template("register.html",form = form)

        
# Login işlemi
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        nickname = form.nickname.data 
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where nickname = %s"

        result = cursor.execute(sorgu,(nickname,))
        

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yapıldı. Hoşgeldiniz...","success")

                session["logged_in"] = True
                session["nickname"] = nickname


                return redirect(url_for("emre"))
            else:
                flash("Parola hatalı!","danger")
                return redirect(url_for("login"))
            
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))
    else:
        pass

    return render_template("login.html",form = form)

#Makale Detay Sayfası

@app.route("/article/<string:id>")

def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)

    else:
        return render_template("article.html")



#Logout işlemi

@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış yapıldı.","warning")
    return redirect(url_for("emre"))

#Makale Ekleme
@app.route("/addarticle",methods = {"GET","POST"})
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "INSERT INTO  articles(title,author,content) VALUES (%s,%s,%s)"

        cursor.execute(sorgu,(title,session["nickname"],content))

        mysql.connection.commit()
        
        cursor.close()

        flash("Makale başarıyla eklendi.","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form = form)
#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["nickname"],id))

    if result > 0:
        sorgu2 = "DELETE FROM articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        cursor.close()

        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu makaleyi silme yetkiniz yok!!!","warning")

        return redirect(url_for("emre"))
        
#Makale Güncelleme
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM articles WHERE id = %s and author = %s"

        result = cursor.execute(sorgu,(id,session["nickname"]))

        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok.","danger")
            return redirect(url_for("emre"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
            
    else:
        #POST REQUEST
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "UPDATE articles SET title = %s, content = %s WHERE id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Makale başarıyla güncellendi. ","success")

        return redirect(url_for("dashboard"))


#Makale Form
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min = 5,max = 100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min = 10)])

#Arama URL
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("emre"))

    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM articles WHERE title like '%" + keyword + "%'"

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı...","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()

            return render_template("articles.html",articles = articles)
if __name__ == "__main__":
    app.run(debug=True)
