import os
import datetime

from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder="")
app.secret_key = "SIH"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")

db = SQLAlchemy(app)


class UserList(db.Model):
    __tablename__ = "user_list"
    username = db.Column(db.String(250), primary_key=True)
    passwords = db.Column(db.String(250))


class Products(db.Model):
    __tablename__ = "product"
    sn = db.Column(db.String(250), primary_key=True)
    product_name = db.Column(db.String(250))
    maintenance = db.relationship('MaintenanceReport', backref='product')


class MaintenanceReport(db.Model):
    __tablename__ = "maintenance_report"
    id = db.Column(db.Integer, primary_key=True)
    sn = db.Column(db.String(250), db.ForeignKey('product.sn'))
    report = db.Column(db.String(250))
    username = db.Column(db.String(250))
    datetime = db.Column(db.DateTime, default=datetime.datetime.now())


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/QRCodeScan")
def scanQRCode():
    return render_template("QRCodeScanner.html")


@app.route("/QRDataProcess", methods=["POST"])
def QRDataProcess():
    QRData = request.form.get("QR")

    try:
        QRData = eval(QRData)
    except:
        return render_template("QRCodeScanner.html", message="QR code not belong to Airports Authority of India")

    try:
        if QRData["org"] != "Airports Authority of India":
            return render_template("QRCodeScanner.html", message="QR code not belong to Airports Authority of India")
    except:
        return render_template("QRCodeScanner.html", message="QR code not belong to Airports Authority of India")

    try:
        sn = QRData["sn"]
    except:
        return render_template("QRCodeScanner.html", message="QR code not belong to Airports Authority of India")

    count_product = Products.query.filter_by(sn=sn).count()

    if count_product:
        p = db.session.query(MaintenanceReport, Products).filter(MaintenanceReport.sn == Products.sn).order_by(
            MaintenanceReport.datetime.desc()).all()

        ptemp = []
        for i in p:
            if i.MaintenanceReport.sn == sn:
                ptemp.append(i)

        session["sn"] = sn
        return render_template("report.html", datas=ptemp)
    else:
        return render_template("QRCodeScanner.html", message="Not in inventory")


@app.route("/update_main", methods=["POST"])
def update_main():
    return render_template("update_details.html")


@app.route("/login", methods=["POST"])
def login():
    return render_template("login.html")


@app.route("/login_check", methods=["POST"])
def login_check():
    username = request.form.get("username")
    password = request.form.get("password")

    login = UserList.query.filter_by(username=username, passwords=password).first()

    if login is None:
        return render_template("login.html", message="Wrong Username and Password")

    session["username"] = username
    return render_template("update_details.html")


@app.route("/update_main_database", methods=["POST"])
def update_main_database():
    report = request.form.get("report")

    temp = MaintenanceReport(sn=session["sn"], report=report, username=session["username"],
                             datetime=datetime.datetime.now())
    db.session.add(temp)
    db.session.commit()

    return redirect("index.html")


if __name__ == "__main__":
    app.run(debug=True)
