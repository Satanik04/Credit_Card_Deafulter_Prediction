from flask import Flask, render_template, request, url_for, redirect, session
from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.urls import url_encode
from reportlab.platypus import SimpleDocTemplate,Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
import pickle


app = Flask(__name__)
app.secret_key = "my-secret-key"

model = pickle.load(open("DecisionTreeClassifier.pkl", "rb"))

# Simple memory storage
users = {}

# flaskform
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

#home
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

#login
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # normal password
        if username in users and users[username] == password:
            session['user'] = username
            flash(f"Welcome {username}")
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"

    return render_template('login.html', form=form)

#register
@app.route("/register", methods=["GET", "POST"])
def register():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # store normal password
        users[username] = password
        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

#logout
@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

feature_names = [
    "LIMIT_BAL", "SEX", "PAY_0", "PAY_2", "PAY_3", "PAY_4",
    "PAY_5", "PAY_6", "BILL_AMT1", "BILL_AMT2", "BILL_AMT3",
    "BILL_AMT4", "BILL_AMT5", "BILL_AMT6", "PAY_AMT1",
    "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5",
    "PAY_AMT6", "EDU_GRAD", "EDU_HIGH", "EDU_OTHER",
    "EDU_UNI", "MARRIED", "SINGLE"
]

#download pdf
def create_pdf(data,result,probability):
    file_path=f"report_{session['user']}.pdf"

    doc=SimpleDocTemplate(file_path)
    styles=getSampleStyleSheet()

    content=[]
    content.append(Paragraph("credit card Report",styles['Title']))
    content.append(Paragraph(f"Result:{result}",styles['Normal']))
    content.append(Paragraph(f"Risk:{probability}%",styles['Normal']))
    content.append(Paragraph("User Input:",styles['Heading2']))

    for name,value in zip(feature_names, data):
        content.append(Paragraph(f"{name}:{value}",styles['Normal']))
    doc.build(content)
    return file_path

@app.route("/download")
def download():
    if 'user' not in session:
        return redirect(url_for("login"))
    data=session.get('data')
    result=session.get('result')
    probability=session.get('prob')

    file_path=create_pdf(data,result,probability)
    return send_file(file_path,as_attachment=True)



#predict result
@app.route("/predict", methods=["POST"])
def predict():
    if 'user' not in session:
        return redirect(url_for("login"))

    education = request.form.get('education')

    edu_grad = 1 if education == "EDUCATION_Graduate school" else 0
    edu_high = 1 if education == "EDUCATION_High School" else 0
    edu_other = 1 if education == "EDUCATION_Others" else 0
    edu_uni  = 1 if education == "EDUCATION_University" else 0

    marriage = request.form.get('marriage')
    married = 1 if marriage == "Married" else 0
    single  = 1 if marriage == "Single" else 0

    data = [
        int(request.form['LIMIT_BAL']),
        int(request.form['SEX']),
        int(request.form['PAY_0']),
        int(request.form['PAY_2']),
        int(request.form['PAY_3']),
        int(request.form['PAY_4']),
        int(request.form['PAY_5']),
        int(request.form['PAY_6']),
        int(request.form['BILL_AMT1']),
        int(request.form['BILL_AMT2']),
        int(request.form['BILL_AMT3']),
        int(request.form['BILL_AMT4']),
        int(request.form['BILL_AMT5']),
        int(request.form['BILL_AMT6']),
        int(request.form['PAY_AMT1']),
        int(request.form['PAY_AMT2']),
        int(request.form['PAY_AMT3']),
        int(request.form['PAY_AMT4']),
        int(request.form['PAY_AMT5']),
        int(request.form['PAY_AMT6']),
        edu_grad, edu_high, edu_other, edu_uni,
        married, single
    ]

    prediction = model.predict([data])
    prob=model.predict_proba([data])
    probability=prob[0][1]*100
    probability=round(probability,2)

    result = "Oops! you may default on credit card payment" if prediction[0] == 1 else "No Default Risk Detected"

    session['data']=data
    session['result']=result
    session['prob']=probability

    return render_template('result.html', result=result,prob=probability)


if __name__ == "__main__":
    app.run(debug=True)