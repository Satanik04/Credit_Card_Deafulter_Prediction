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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime


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
            flash(f"WELCOME {username}".upper())
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
    "LIMIT_BAL", "BILL_AMT1", "BILL_AMT2", "BILL_AMT3",
    "BILL_AMT4", "BILL_AMT5", "BILL_AMT6", "PAY_AMT1",
    "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5",
    "PAY_AMT6","PAY_0", "PAY_2", "PAY_3", "PAY_4",
    "PAY_5", "PAY_6", "EDU_GRAD", "EDU_HIGH", "EDU_OTHER",
    "EDU_UNI", "SEX", "MARRIED", "SINGLE"
]

#download pdf
def create_pdf(data,result,probability):
    file_path=f"report_{session['user']}.pdf"

    doc=SimpleDocTemplate(file_path)
    styles=getSampleStyleSheet()

    content=[]
    content.append(Paragraph("Credit Card Report",styles['Title']))
    content.append(Spacer(1, 15))
    content.append(Paragraph(f"Result:{result}",styles['Normal']))
    content.append(Paragraph(f"Risk:{probability}%",styles['Normal']))
    content.append(Spacer(1,15))
    content.append(Paragraph("Input Data:",styles['Heading2']))

    #for name,value in zip(feature_names, data):
    #     if name=="SEX":
    #         value = "Male" if value == 1 else "Female"
    #     if name.startswith("EDU_"):
    #         if value==1:
    #             if name == "EDU_GRAD":
    #                 value = "Graduate School"
    #             elif name == "EDU_HIGH":
    #                 value = "High School"
    #             elif name == "EDU_OTHER":
    #                 value = "Others"
    #             elif name == "EDU_UNI":
    #                 value = "University"
    #     if name=="MARRIED" and value==1:
    #         value="Married"
    #     if name=="SINGLE" and value==1:
    #         value=="Single"
    #     content.append(Paragraph(f"{name}: {value}", styles['Normal']))
    # doc.build(content)
    # return file_path

    table_data = [["Feature", "Value"]]

    for name, value in zip(feature_names, data):

        # Gender
        if name == "SEX":
            table_data.append(["Gender", "Male" if value == 1 else "Female"])
            continue
        
        if name in ["PAY_0","PAY_2","PAY_3","PAY_4","PAY_5","PAY_6"]:
            if value == -2:
                value = "No Bill"
            elif value == -1:
                value = "On Time"
            elif value == 0:
                value = "Minimum Payment"
            elif value == 1:
                value = "Delay 1 Month"
            elif value == 2:
                value = "Delay 2 Months"
            else:
                value = f"Delay {value} Months"
        # Education (only selected one)
        if name.startswith("EDU_"):
            if value == 1:
                if name == "EDU_GRAD":
                    table_data.append(["Education", "Graduate School"])
                elif name == "EDU_HIGH":
                    table_data.append(["Education", "High School"])
                elif name == "EDU_OTHER":
                    table_data.append(["Education", "Others"])
                elif name == "EDU_UNI":
                    table_data.append(["Education", "University"])
            continue

        # Marriage
        if name == "MARRIED" and value == 1:
            table_data.append(["Marital Status", "Married"])
            continue

        if name == "SINGLE" and value == 1:
            table_data.append(["Marital Status", "Single"])
            continue

        if name in ["MARRIED", "SINGLE"]:
            continue

        # Normal values
        table_data.append([name, str(value)])

    # Create table
    table = Table(table_data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
    ]))

    content.append(table)
    content.append(Spacer(1, 20))

    # Date
    content.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))

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

        int(request.form['PAY_0']),
        int(request.form['PAY_2']),
        int(request.form['PAY_3']),
        int(request.form['PAY_4']),
        int(request.form['PAY_5']),
        int(request.form['PAY_6']),
        edu_grad, edu_high, edu_other, edu_uni,
        int(request.form['SEX']),
        married, single
    ]

    #prediction = model.predict([data])
    prob=model.predict_proba([data])
    probability=prob[0][1]*100
    probability=round(probability,2)

    # result = "Oops! you may default on credit card payment" if prediction[0] == 1 else "No Default Risk Detected"
    if probability <20:
        result= "Low Risk Detected"
    elif probability <60:
        result="Moderate Risk Detected"
    else:
        result="High Risk Detected"

    session['data']=data
    session['result']=result
    session['prob']=probability

    return render_template('result.html', result=result,prob=probability)


if __name__ == "__main__":
    app.run(debug=True)