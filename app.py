#THE WORK OF: KARIM BASSEM JOSEPH ID: 231000797

#to use the python app as a website
from flask import Flask, redirect, render_template, request, session
#to use the easy sqlite3
from cs50 import SQL
#to secure 
from werkzeug.utils import secure_filename
#to have the options to manage file from the app
import os

import shutil
from datetime import datetime, timedelta

#to start the app and force it to start as a flask app
app = Flask(__name__)
#the app secret key
app.secret_key = "KB"

#mentien the database 
db = SQL("sqlite:///kbclinic.db")

#a function to select all of the data from the patients and details and transactions table where the id is like given from the html
#and also calculate the age of a person from the date of today - his birthdate
def select_patient():
        id = request.form.get("id")
        d_id = request.form.get("d_id")
        if id is None:
            id_query = db.execute("SELECT id FROM details WHERE d_id = ?", d_id)
            if len(id_query) > 0:
                id = id_query[0]["id"]
            
            doc_id = session.get("doc_id")
            person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE id = ? ", id)
            details = db.execute("SELECT * FROM details WHERE id = ?", id)
            trans = db.execute("SELECT * FROM transactions WHERE doc_id = ?", doc_id)
            return person , details , trans
        else:
            doc_id = session.get("doc_id")
            person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE id = ? ", id)
            details = db.execute("SELECT * FROM details WHERE id = ?", id)
            trans = db.execute("SELECT * FROM transactions WHERE doc_id = ?", doc_id)
            return person , details , trans

#a function to the prescription the innerjoin two tables
def prescription():
        d_id = request.form.get("d_id")
        id = request.form.get("id")
        doc_id = session.get("doc_id")
        query = """
            SELECT details.date, patients.name, details.remarks, details.prescription, patients.id, details.d_id
            FROM details 
            INNER JOIN patients ON details.id = patients.id 
            WHERE details.d_id = ? AND patients.id = ?
        """
        detail = db.execute(query, d_id, id)
        doctor = db.execute("SELECT * FROM doctors WHERE doc_id = ?", doc_id)
        return detail, doctor


def show_doctor_details():
        doc_id = session.get("doc_id")
        doctor = db.execute("SELECT * FROM doctors WHERE doc_id = ?", doc_id)
        prices = db.execute("SELECT * FROM price_cat WHERE doc_id = ?", doc_id)
        appoint_times = db.execute("SELECT * FROM appoint_time WHERE doc_id = ?", doc_id)
        return doctor, prices, appoint_times

def encrypt():
    password = request.form.get("password")
    new_pass = []
    for i in password:
        assci_char = ord(i)-13
        char=chr(assci_char)
        new_pass.append(char)
    encrypted_password = "".join(new_pass)
    return encrypted_password\
    
def shape_check():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        shape = db.execute("SELECT shape FROM doctors WHERE doc_id = ?", doc_id)
        print(shape)
        if len(shape) > 0:
            shape = shape[0]["shape"]
            return shape
        else:
            return 0
    
#the home page route
@app.route("/")
def choose():
    return render_template("choose.html")

#the login route that checks if the username "not case sensitive" and the password the are given from the template are the same as those on the databse
#and also check if the user category of this person is doctor so it shows for him the doctors page and if he is an admin it shows to him the admin page
@app.route("/login", methods=["GET","POST"])
def sign_in_admin():
    #check if the method is post "more secured than get"
    if request.method == "POST":
        username = (request.form.get("username").strip()).lower()
        password = encrypt()


        login = db.execute("SELECT * FROM doctors WHERE LOWER(username) = ? AND password = ?", username , password)
        login_a = db.execute("SELECT * FROM assistants WHERE LOWER(username) = ? AND password = ?", username , password)
        #to fetch data from the database 
        if len(login) > 0:
            user_cat = login[0]["user_cat"]

        if len(login_a) > 0:
            user_cat_a = login_a[0]["user_cat"]
        #checks if the data are in the database make the session logged_in = true if not it shows an error
        if login:
            if user_cat == "doctor":
                    doctor = db.execute("SELECT doc_id FROM doctors WHERE LOWER(username) = ? AND password = ?", username, password)
                    session.pop("logged_in_assistant", None)
                    session.pop("a_id", None)
                    session["logged_in"] = True
                    session["doc_id"] = doctor[0]["doc_id"]
                    return redirect("/home")
            elif user_cat == "admin":
                    doctor = db.execute("SELECT doc_id FROM doctors WHERE LOWER(username) = ? AND password = ?", username, password)
                    session.pop("logged_in_assistant", None)
                    session.pop("a_id", None)
                    session["logged_in_admin"] = True
                    session["doc_id"] = doctor[0]["doc_id"]
                    return redirect("/admin_home")
        elif login_a:
            if user_cat_a == "assistant":
                doctor = db.execute("SELECT a_id FROM assistants WHERE LOWER(username) = ? AND password = ?", username, password)
                session["logged_in_assistant"] = True
                session["a_id"] = doctor[0]["a_id"]
                return redirect("/assistant_home")
        else:    
                error = "Invalid username or password"
                return render_template("login.html", error=error)
    else:
          return render_template("login.html")

#a logout function to go back to login and make the session logged_in = false
@app.route("/logout", methods=["GET","POST"])
def sign_out():
    if session.get("logged_in"):
        session["logged_in"] = False
        return redirect("/login")
    elif session.get("logged_in_admin"):
        session["logged_in_admin"] = False
        return redirect("/login")
    elif session.get("logged_in_assistant"):
        session["logged_in_assistant"] = False
        return redirect("/login")
    else:
        return render_template("login.html")

#a route that opens a page that have all of the doctors and their details to the patients to see what doctor they need
@app.route("/patient_view")
def patient_view():
    doctor = db.execute("SELECT * FROM doctors WHERE user_cat = ? ORDER BY doc_name COLLATE NOCASE", "doctor" )
    return render_template("patient_view.html", doctor = doctor)

#a route that filters the doctors by their category
@app.route("/filter_doctor_cat", methods=["GET"])
def filter_doctor_cat():
        category = request.args.get("category")
        if category:
            doctor = db.execute("SELECT * FROM doctors WHERE category = ? ORDER BY doc_name", category)
            return render_template("search_doctor.html", doctor=doctor)
        else:
            return render_template("search_doctor.html", doctor=[])

#a route that shows all of the details of doctor that the patient have choose to see his details
@app.route("/doctor_show_details", methods=["POST"])
def doctor_show_details():
    doc_id = request.form.get("doc_id")
    doctor = db.execute("SELECT * FROM doctors WHERE doc_id = ?", doc_id)
    return render_template("doctor_show_details.html", doctor = doctor)

@app.route("/home")
def home_page():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        current_date = datetime.now().strftime('%Y-%m-%d')
        date = datetime.now().date()
        doc_id = session.get("doc_id")
        
        # Use SQL JOIN to fetch appointments with patient names
        appoint = db.execute("""
            SELECT appoint.*, patients.name AS patient_name
            FROM appoint
            JOIN patients ON appoint.id = patients.id
            WHERE appoint.doc_id = ? AND appoint.date = ?
        """, doc_id, date)

        return render_template("home.html", appoint=appoint, current_date=current_date)

@app.route("/filter_date_home_doc", methods=["GET"])
def filter_date_home_doc():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        date = request.args.get("date_filter")
        appoint = db.execute("""
            SELECT appoint.*, patients.name AS patient_name
            FROM appoint
            JOIN patients ON appoint.id = patients.id
            WHERE appoint.doc_id = ? AND appoint.date = ?
        """, doc_id, date)
        return render_template("home.html", appoint=appoint)

#a route that a doctor can add a new patient with his details
@app.route("/add_patient", methods=["POST"])
def add_patient():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        name = request.form.get("name")
        phone_number = request.form.get("phone_number")
        birthdate = request.form.get("birthdate")
        gender = request.form.get("gender")
        patient_cat = request.form.get("patient_cat")
        doc_id = session.get("doc_id")
        db.execute("SELECT * FROM price_cat WHERE doc_id = ?", doc_id)
        db.execute("INSERT INTO patients ( doc_id, name, phone_number, birthdate, gender, patient_cat) VALUES(?, ?, ?, ?, ?, ?)",
                    doc_id, name, phone_number, birthdate, gender ,patient_cat)
        return redirect("/show_all")
    
#a route that returns the add new patient page
@app.route("/add_p_page")
def add_p_redirect():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        patient_cat = db.execute("SELECT * FROM patient_cat WHERE doc_id = ?", doc_id)
        shape = shape_check()
        return render_template("add_new.html", patient_cat=patient_cat, shape = shape)
    
#a route that shows all of the patients that are saved with this doc_id of the doctor signed-in
@app.route("/show_all",methods=["GET"] )
def show_all():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        patients = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE doc_id = ? ORDER BY name COLLATE NOCASE", doc_id)
        shape = shape_check()
        return render_template("show_all.html", patients=patients, shape = shape)
    
#a route to search in the database fo a person with a name like the name written on the database with the doc_id of the doctor signed_in and not case sensitive
@app.route("/search_name", methods=["GET"])
def search_name():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        name = request.args.get("name").lower()
        doc_id = session.get("doc_id")
        if name:
            person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE name LIKE ? AND doc_id = ? ORDER BY name", "%"+ name + "%", doc_id)
            return render_template("search.html", patients=person)
        else:
            return render_template("search.html", patients=[])

#a route to search by id for a person on the database with the doc_id of the doctor signed-in
@app.route("/search_id", methods=["GET"])
def search_id():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        id = request.args.get("id")
        doc_id = session.get("doc_id")
        if id:
            person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE id = ? AND doc_id = ? ORDER BY name", id, doc_id)
            return render_template("search.html", patients=person)
        else:
            return render_template("search.html", patients=[])


#a route to show all of the doctor details to the doctor him self
@app.route("/doctor_details", methods=["GET","POST"])
def doctor_details():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doctor, prices, appoint_times = show_doctor_details()
        return render_template("doctor_details.html", doctor = doctor, prices=prices, appoint_times=appoint_times)

@app.route("/change_shape", methods=["POST"])
def change_shape():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        shape = request.form.get("shape")
        db.execute("UPDATE doctors SET shape = ? WHERE doc_id = ?", shape, doc_id)
        doctor, prices, appoint_times = show_doctor_details()
        return render_template("doctor_details.html", doctor = doctor, prices=prices, appoint_times=appoint_times)

@app.route("/add_appoint_times_redirect", methods=["GET"])
def add_appoint_times_redirect():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        doctor, prices, appoint_times = show_doctor_details()
        time = db.execute("SELECT * FROM appoint_time WHERE doc_id = ?", doc_id)
        return render_template("add_appoint_times.html", time = time, doctor= doctor, prices=prices, appoint_times=appoint_times)
    
@app.route("/add_appoint_times", methods=["POST"])
def add_appoint_times():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        time1 = request.form.get("time1")
        time2 = request.form.get("time2")
        seperate_time = request.form.get("seperate_time")
        day = request.form.get("day")

        existing_time = db.execute("SELECT * FROM appoint_time WHERE doc_id = ? AND day = ?", doc_id, day) #selects every thing from the price_cat where the doc_id and the price_category and the patient_cat is like given before

        if not existing_time:
            db.execute("INSERT INTO appoint_time (doc_id, time1, time2, seperate_time, day) VALUES (?,?,?,?,?)", doc_id, time1, time2, seperate_time, day)
            return redirect("/add_appoint_times_redirect")
        else: 
            error = "This Day Is Assigned"
            doctor, prices, appoint_times = show_doctor_details()
            time = db.execute("SELECT * FROM appoint_time WHERE doc_id = ?", doc_id)
            return render_template("add_appoint_times.html", error=error, doctor = doctor, prices = prices, time = time, appoint_times=appoint_times)

#a route to redirect the doctor to a page that he adds on it his details and could edit it
@app.route("/add_d_details_redirect")
def add_d_details_redirect():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        doctor = db.execute("SELECT * FROM doctors WHERE doc_id = ?", doc_id)
        return render_template("add_doctor_details.html", doctor= doctor)    

#a route that the doctor adds his details
@app.route("/add_d_details", methods=["POST"])              
def add_d_details():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        details = request.form.get("details")
        db.execute("UPDATE doctors SET details = ? WHERE doc_id = ?",details, doc_id)
        return redirect("/doctor_details")

#a route to redirect the doctor to a page that checks his old password if he wants to change it
@app.route("/change_pass_check_redirect")
def change_pass_check_redirect():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        return render_template("password_check.html")
    
#a route that checks if the passwrd written on the template is the same as the password saved on the database
@app.route("/change_password_check", methods=["POST"])
def change_pass_check():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
            password = encrypt()
            doc_id = session.get("doc_id")
            password_check = db.execute("SELECT password from doctors WHERE doc_id = ?", doc_id)
            if password_check and password == password_check[0]["password"]:
                return render_template("change_password.html")
            else:
                error = "Incorrect Password"
                return render_template("password_check.html", error=error)

#a route that change the password of the doctor to a new one
@app.route("/change_password", methods=["POST"])
def change_password():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        password = encrypt()
        doc_id = session.get("doc_id")
        db.execute("UPDATE doctors SET password = ? WHERE doc_id = ?", password , doc_id)
        return redirect("/doctor_details")
    
#a route that redirect to an edit doctor page
@app.route("/edit_doctor", methods=["POST"])
def edit_doctor():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        doctor = db.execute("SELECT * FROM doctors WHERE doc_id = ?", doc_id)
        return render_template("edit_doctor.html", doctor=doctor)
    
#a route that edits the doctor information like his username, phone number, Name
@app.route("/update_doctor", methods=["POST"])
def update_doctor():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        username = request.form.get("username")
        category = request.form.get("category")
        doc_name = request.form.get("doc_name")
        doc_phone_number = request.form.get("doc_phone_number")
        existing_user_query = db.execute("SELECT doc_id FROM doctors WHERE LOWER(username) = ?", username)

        if len(existing_user_query) > 0:
            existing_user = existing_user_query[0]["doc_id"]

        if existing_user and existing_user != doc_id:#an if condition to see if this username is saved by another user
            error_existing = "Username is unavailable. Please choose another one."
            doctor = db.execute("SELECT * FROM doctors WHERE doc_id = ?", doc_id)
            return render_template("edit_doctor.html", error=error_existing, doctor=doctor)
        else:
            db.execute("UPDATE doctors SET username = ?, category = ?, doc_name = ?, doc_phone_number = ? WHERE doc_id = ?", username, category,doc_name, doc_phone_number, doc_id)
            return redirect("/doctor_details")
    
#a route that redirect to a page that edits the patients saved information    
@app.route("/edit_appoint_times", methods=["POST"])
def edit_appoint_time():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        day_id = request.form.get("day_id")
        appoint_times = db.execute("SELECT * FROM appoint_time WHERE day_id = ?",day_id)
        return render_template("edit_appoint_time.html", appoint_times=appoint_times)

#a route that update the saved information of the patient
@app.route("/update_appoint_times", methods=["POST"])
def update_appoint_times():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        day_id = request.form.get("day_id")
        day = request.form.get("day")
        time1 = request.form.get("time1")
        time2 = request.form.get("time2")
        seperate_time = request.form.get("seperate_time")
        existing_time_query = db.execute("SELECT day_id FROM appoint_time WHERE day = ? AND doc_id = ? AND day_id != ?", day, doc_id, day_id)


        if len(existing_time_query) > 0:
            error = "You Have Another Appointment Time With The Same Day"
            appoint_times = db.execute("SELECT * FROM appoint_time WHERE day_id = ?",day_id)
            return render_template("edit_appoint_time.html", appoint_times=appoint_times, error=error)
        else:
            db.execute("UPDATE appoint_time SET day = ?, time1 = ?, time2 = ?, seperate_time = ? WHERE day_id = ?", day, time1, time2, seperate_time, day_id)
            #calling the fuction on the top of the code that select all of the patient data that are saved to redirect to his page
            doctor, prices, appoint_times = show_doctor_details()
            return render_template("doctor_details.html", doctor = doctor, prices=prices, appoint_times=appoint_times)

#a route that redirect to a page that edits the patients saved information    
@app.route("/edit_patient", methods=["POST"])
def edit_patient():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        id = request.form.get("id")
        doc_id = session.get("doc_id")
        person = db.execute("SELECT * FROM patients WHERE id = ?", id)
        patient_cat = db.execute("SELECT * FROM patient_cat WHERE doc_id = ?", doc_id)
        return render_template("edit_patient.html", person=person, patient_cat=patient_cat)

#a route that update the saved information of the patient
@app.route("/update", methods=["POST"])
def update():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        id = request.form.get("id")
        name = request.form.get("name")
        phone_number = request.form.get("phone_number")
        gender = request.form.get("gender")
        birthdate = request.form.get("birthdate")
        patient_cat = request.form.get("patient_cat")
        db.execute("UPDATE patients SET name = ?, phone_number = ?, gender = ?, birthdate = ? , patient_cat = ? WHERE id = ?",
                    name, phone_number, gender, birthdate,patient_cat, id)
        #calling the fuction on the top of the code that select all of the patient data that are saved to redirect to his page
        person , details , trans = select_patient()
        return render_template("open_patient.html", person = person, details = details, trans=trans)

#a route that open the patient with more details and a table that have all of his details
@app.route("/open_patient", methods=["GET","POST"])
def open_patient():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        #calling the fuction on the top of the code that select all of the patient data that are saved
        person , details , trans = select_patient()
        shape = shape_check()
        return render_template("open_patient.html", person = person, details = details, trans = trans, shape = shape)

    #a route that make the admin can edit and modify the doctor prices
@app.route("/edit_prices_doc", methods=["POST"])
def edit_prices_doc():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        price_cat_id = request.form.get("price_cat_id")
        prices = db.execute("SELECT * FROM price_cat WHERE doc_id = ? AND price_cat_id = ?", doc_id, price_cat_id)
        return render_template("edit_prices_doc.html", prices=prices)
    
    #a route the execute the route before that
@app.route("/update_prices_doc", methods=["POST"])
def edit_price_doc():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        price = request.form.get("price")
        price_cat_id = request.form.get("price_cat_id")
        db.execute("UPDATE price_cat SET price = ? WHERE doc_id = ? AND price_cat_id = ?", price, doc_id, price_cat_id)
        return redirect("/doctor_details")

@app.route("/add_appoint_date_doc_redirect", methods=["POST"])
def add_appoint_date_doc_redirect():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        id = request.form.get("id")
        doc_id = session.get("doc_id")
        person = db.execute("SELECT * FROM patients WHERE id = ?", id)
        prices_cat = db.execute("SELECT DISTINCT price_category FROM price_cat WHERE doc_id = ?", doc_id)
       # Define the current date and the date one month ahead
        current_date = datetime.now()
        next_month = current_date + timedelta(days=7)

        # Prepare to collect free time slots
        free_appoint = []

        # Iterate through each day in the next month
        while current_date <= next_month:
            day_of_week = current_date.strftime("%A")
            times = db.execute("SELECT * FROM appoint_time WHERE doc_id = ? AND day = ?", doc_id, day_of_week)

            if times:
                time1 = datetime.strptime(times[0]["time1"], "%H:%M")
                time2 = datetime.strptime(times[0]["time2"], "%H:%M")
                separate_time = timedelta(minutes=times[0]["seperate_time"])

                current_time = time1
                while current_time + separate_time <= time2:
                    existing_appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ? AND time = ?", doc_id, current_date.strftime("%Y-%m-%d"), current_time.strftime("%H:%M"))
                    if not existing_appoint:
                        free_appoint.append({'date': current_date.strftime("%Y-%m-%d"), 'time': current_time.strftime("%H:%M"), 'day_of_week' : day_of_week})
                    current_time += separate_time

            current_date += timedelta(days=1)
        return render_template("add_appoint_doc.html", person=person, free_appoint=free_appoint, prices_cat=prices_cat)

@app.route("/add_appoint_doc", methods = ["POST"])
def app_appoint_doc():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        id = request.form.get("id")
        doc_id = session.get("doc_id")
        datetime = request.form.get("datetime")
        date , time = datetime.split()
        category = request.form.get("category")
        db.execute("INSERT INTO appoint(id, doc_id, date, category, time, status) VALUES (?,?,?,?,?,?)", id, doc_id, date, category, time, "Not Done")
        return redirect("/show_all")

#a route that redirect to an edit doctor page
@app.route("/edit_appoint_doc", methods=["POST"])
def edit_appoint_doc():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        appoint_id = request.form.get("appoint_id")
        date = request.form.get("date")
        chech_appoint_status = db.execute("SELECT status FROM appoint WHERE appoint_id = ?", appoint_id)

        if len(chech_appoint_status) > 0:
            appoint_status = chech_appoint_status[0]["status"]

        if appoint_status == "Not Done":
            appoint = db.execute("SELECT * FROM appoint WHERE appoint_id = ?", appoint_id)
            prices_cat = db.execute("SELECT DISTINCT price_category FROM price_cat WHERE doc_id = ?", doc_id)
            date_object = datetime.strptime(date, "%Y-%m-%d")

            # Get the day of the week as a string (e.g., "Monday")
            day_of_week = date_object.strftime("%A")

            time = db.execute("SELECT * FROM appoint_time WHERE doc_id = ? AND day = ?",doc_id, day_of_week)
            free_time = []
            if len(time) > 0:
                time1 = datetime.strptime(time[0]["time1"], "%H:%M")
                time2 = datetime.strptime(time[0]["time2"], "%H:%M")
                separate_time = timedelta(minutes=time[0]["seperate_time"])

                current_time = time1
                while current_time + separate_time <= time2:
                    existing_appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ? AND time = ? AND appoint_id != ?", doc_id, date, current_time.strftime("%H:%M"), appoint_id)
                    if not existing_appoint:
                        free_time.append(current_time.strftime("%H:%M"))
                    current_time += separate_time
            return render_template("edit_appoint_doc.html", appoint=appoint, prices_cat=prices_cat , free_time = free_time)
        else:
            error = "Can't Edit This Appointment Is Done"
            current_date = datetime.now().strftime('%Y-%m-%d')
            date = datetime.now().date()
            appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ?", doc_id, date)
            return render_template("home.html", appoint=appoint, current_date=current_date, error=error)
    
#a route that edits the doctor information like his username, phone number, Name
@app.route("/update_appoint_doc", methods=["POST"])
def update_appoint_doc():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        appoint_id = request.form.get("appoint_id")
        time = request.form.get("time")
        category = request.form.get("category")
        status = request.form.get("status")
        chech_appoint_status = db.execute("SELECT status FROM appoint WHERE appoint_id = ?", appoint_id)

        if len(chech_appoint_status) > 0:
            appoint_status = chech_appoint_status[0]["status"]

        if appoint_status == "Not Done":
            db.execute("UPDATE appoint SET time = ? , category = ? , status = ? WHERE appoint_id = ?", time, category, status, appoint_id)
            return redirect("/home")
        else:
            error = "Can't Edit This Appointment Is Done"
            current_date = datetime.now().strftime('%Y-%m-%d')
            date = datetime.now().date()
            doc_id = session.get("doc_id")
            appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ?", doc_id, date)
            return render_template("home.html", appoint=appoint, current_date=current_date, error=error)
        
@app.route("/delete_appoint_doc", methods=["POST"])
def delete_appoint_doc():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        appoint_id = request.form.get("appoint_id")
        chech_appoint_status = db.execute("SELECT status FROM appoint WHERE appoint_id = ?", appoint_id)

        if len(chech_appoint_status) > 0:
            appoint_status = chech_appoint_status[0]["status"]

        if appoint_status == "Not Done":
            db.execute("DELETE FROM appoint WHERE appoint_id = ?", appoint_id)
            return redirect("/home")
        else :
            error = "Can't Delete This Appointment Is Done"
            current_date = datetime.now().strftime('%Y-%m-%d')
            date = datetime.now().date()
            doc_id = session.get("doc_id")
            appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ?", doc_id, date)
            return render_template("home.html", appoint=appoint, current_date=current_date, error=error)
        
#a function to add a new patient details with his id and the doctor id that is signed-in
def add_patient_details():
        id = request.form.get("id")
        doc_id = session.get("doc_id")
        appoint_id = request.form.get("appoint_id")
        prices_cat = db.execute("SELECT DISTINCT price_category FROM price_cat WHERE doc_id = ?", doc_id)
        person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE id = ?", id)
        detail = db.execute("SELECT * FROM details WHERE id = ?", id)
        appoint = db.execute("SELECT * FROM appoint WHERE appoint_id = ?", appoint_id)
        return prices_cat, person, detail , appoint

#a route that  redirect to a page that the doctor can add some information about the patient every time he came to him and save them in the database
@app.route("/add_details_redirect", methods=["POST"])
def add_page_redirect():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        #calling the function of adding a patient details
        prices_cat, person, detail, appoint = add_patient_details()
        shape = shape_check()
        return render_template("add_details.html", person=person, detail=detail, prices_cat=prices_cat, appoint=appoint, shape = shape)
    
#a route that adds a new record to the database with the date and the remarks and the details of the patient and save it to the database and show them on the open_patient route"metiened before"   
@app.route("/add_details", methods=["POST"])
def add_details():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        id = request.form.get("id")
        details = request.form.get("details")
        date = request.form.get("date")
        remarks = request.form.get("remarks")
        price_category = request.form.get("price_category")
        print(price_category)

        if price_category is None:    
            db.execute("INSERT INTO details (details,remarks, date, id, doc_id, category) VALUES (?, ?, ?, ?, ?, ?)", details,remarks, date, id, doc_id, price_category)
            person , details , trans= select_patient()
            return render_template("open_patient.html", person = person, details = details, trans=trans)
        else:
            patient_cat_select = db.execute("SELECT patient_cat FROM patients WHERE id = ?", id)
            #this if condtion makes sure that the user haven't choosen a wrong thing that have no patient_category on it and if not it shows an error 
            if len(patient_cat_select) > 0:
                #to fetch that data from the data base and make it as a string not a list
                patient_cat = patient_cat_select[0]["patient_cat"]
                #a database query to select the price for that specific patient
                price1 = db.execute("SELECT price FROM price_cat WHERE doc_id = ? AND price_category = ? AND patient_cat = ?", doc_id, price_category, patient_cat)
                #another if cndition because if the user puts somthing wrong it shows to him an error massege
                if price1 and len(price1) > 0:
                    #to fetch the data from the database as a string
                    price = price1[0]["price"]
                    db.execute("INSERT INTO details (details,remarks, date, id, doc_id, category) VALUES (?, ?, ?, ?, ?, ?)", details,remarks, date, id, doc_id, price_category)
                    db.execute("INSERT INTO transactions (doc_id, id, price, category, date, patient_cat) VALUES (?,?,?,?,?,?)", doc_id, id, price, price_category, date, patient_cat)
                    db.execute("UPDATE appoint SET status = ? WHERE id = ? AND date = ?", "Done", id, date)
                else:
                #calling the function of adding a patient details
                    prices_cat, person, detail, appoint = add_patient_details()
                    #the error massege that will show if somthing is incorrect
                    error = "This patient category does not have a price, or you have not selected a category."
                    return render_template("add_details.html", error=error, person=person, detail=detail, prices_cat=prices_cat, appoint=appoint)
            else:
                #calling the function of adding a patient details
                prices_cat, person, detail, appoint = add_patient_details()
                error = "This patient category does not have a price, or you have not selected a category."
                return render_template("add_details.html", error=error, person=person, detail=detail, prices_cat=prices_cat, appoint = appoint)

            #callig the function on the top of the code to open patients page
            person , details , trans= select_patient()
            return render_template("open_patient.html", person = person, details = details, trans=trans)

#a route that delete the details "record" saved with a date from the database
@app.route("/delete_details", methods=["POST"])
def delete_record():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        d_id = request.form.get("d_id")
        id = request.form.get("id")
        if d_id:
            date1 = db.execute("SELECT * FROM details WHERE d_id = ?", d_id)
            if len(date1) > 0:
                date = date1[0]["date"]
            db.execute("DELETE FROM details WHERE d_id = ?", d_id)
            db.execute("DELETE FROM transactions WHERE date = ? AND id = ?", date, id)
        person , details , trans = select_patient()
        return render_template("open_patient.html", person = person, details = details, trans = trans)

# a route that redirect to a page that edits the details saved in the database for this day
@app.route("/edit_details", methods=["POST"])
def edit_details():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        d_id = request.form.get("d_id")
        detail = db.execute("SELECT * FROM details WHERE d_id = ?", d_id)
        person = select_patient()
        return render_template("edit_details.html", detail=detail, person = person)
    
#a route that updates the details saved in the database for this day
@app.route("/update_details", methods=["POST"])
def update_details():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        d_id = request.form.get("d_id")
        details = request.form.get("details")
        date = request.form.get("date")
        remarks = request.form.get("remarks")
        db.execute("UPDATE details SET details = ?, date = ?, remarks = ? WHERE d_id = ?", details, date, remarks, d_id)
        person , details , trans = select_patient()
        return render_template("open_patient.html", person = person, details = details, trans = trans)

#a route that filter the shown data on the show all page by gender to show "male" or "female"
@app.route("/filter_gender", methods=["GET"])
def filetr_gender():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        gender = request.args.get("gender")
        doc_id = session.get("doc_id")
        if gender:
            person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE gender = ? AND doc_id = ? ORDER BY name", gender, doc_id)
            return render_template("search.html", patients=person)
        else:
            return render_template("search.html", patients=[])

#a route that filter the shown data on the show all page by age to show people who are between the two age that are written
@app.route("/filter_age", methods=["GET"])
def filter_age():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        age1 = request.args.get("age1")
        age2 = int(request.args.get("age2"))
        age2_1 = age2 + 1
        doc_id = session.get("doc_id")
        query = """
            SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - 
            (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age 
            FROM patients 
            WHERE doc_id = ? AND 
            date('now') >= date(birthdate, '+' || ? || ' years') AND 
            date('now') <= date(birthdate, '+' || ? || ' years')
            ORDER BY name
        """
        person = db.execute(query, doc_id, age1, age2_1)
        return render_template("search.html", patients=person)
    
#a route to show the patient details that are saved on a biggger sacale that the table and show more info
@app.route("/open_patient_details", methods=["POST"])
def open_patient_details():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        d_id = request.form.get("d_id")
        if d_id:
            detail = db.execute("SELECT * FROM details WHERE d_id = ?", d_id)
            return render_template("open_patient_details.html", detail=detail)
        else:
            error = "There Is No Date, EDIT or DELETE"
            person , details , trans = select_patient()
            return render_template("open_patient.html", person = person, details = details, trans = trans, error = error)

#a route that redirect to a page that adds a prescription of this date
@app.route("/prescription", methods=["POST"])
def prescription_add():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        #the call of the prescription function that is defined on the top of the code
        detail, doctor = prescription()
        return render_template("prescription.html", detail=detail, doctor=doctor)

#a route that adds a prescription to the database and save it with this date
@app.route("/add_prescription", methods=["POST"])
def add_prescription():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        d_id = request.form.get("d_id")
        print(d_id)
        prescription = request.form.get("prescription")
        db.execute("UPDATE details SET prescription = ? WHERE d_id = ?", prescription, d_id)
        return redirect("/show_all")

#a route that shows the saved prescription saved with a specific date
@app.route("/show_prescription", methods=["POST"])
def show_prescription():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
            #the call of the prescription function that is defined on the top of the code
            detail, doctor = prescription()
            return render_template("prescription_show.html", detail=detail, doctor=doctor)

#got the most of the ideas of the upload files from the flask documentry website but changed most of them with my style
#a limitation to any file that the user can upload to be maximum of 16MB
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024

#the path that the user will save the photo that will be uploaded
app.config["UPLOAD_FOLDER_PHOTO"] = "//home//kbclinic//static//doc"

app.config["UPLOAD_FOLDER_LOGO"] = "//home//kbclinic//static//doc_logo"

#a list with all of the file extentions that are allowed to be uploaded for more secuirity
ALLOWED_EXTENSIONS = ("png", "jpg", "jpeg")

#a function that split the filename of the photo uploaded by the user after the . and selects the elememt with index [1]
#and sees if he is in the list of the ALLOWED _EXTENTIONS it will workd if not will return false  
def allowed_file(filename):
    if "." in filename:
        filename_check = filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        return filename_check
    else:
        return False

#a function that seperate the file extention form the filename by spliting it after the . and selects the index [1]
def file_ext(filename):
        if "." in filename:
                file_ext = filename.split('.', 1)[1].lower()
        return file_ext

#a route to redirect to the upload page
@app.route("/upload_redirect")
def upload_redirect():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        return render_template("upload.html")

#a route the upload the image to the folder "server" with the file_name is the doc_id of the doctor
@app.route("/upload_image", methods=["POST"])
def upload_file():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        if "file" in request.files:    #ensure the the file is uploaded correctly
            doc_id = session.get("doc_id")
            file = request.files['file']
            if file and allowed_file(file.filename): #ensure if the file has the same extention that are accepted
                filename = secure_filename(file.filename)  
                file_extention = file_ext(filename) #recall to the function that is defined up

                photo_name = f"{doc_id}.{file_extention}" #renaming the file with an f string with the doc_id and the file extention
                photo_path = os.path.join(app.config['UPLOAD_FOLDER_PHOTO'], photo_name) #to get the photo path that h will save on

                file.save(photo_path) #saving the file

                db.execute("UPDATE doctors SET photo_path = ? WHERE doc_id = ?", photo_name, doc_id) #a sqlite3 query to put the photo name on the database
                doctor, prices,appoint_times = show_doctor_details()
                return render_template("doctor_details.html", doctor=doctor, prices=prices, appoint_times=appoint_times)
            else:
                error = "Invalid file format. Allowed formats are: png, jpg, jpeg" #if the extention isn't from allowed shows this error 
                return render_template("upload.html", error=error)
        else:
            error = "file upload failed"
            return render_template("upload.html", error=error)

@app.route("/upload_logo_redirect")
def upload_logo_redirect():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        return render_template("upload_logo.html")

@app.route("/upload_logo", methods=["POST"])
def upload_logo():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        if "file" in request.files:    #ensure the the file is uploaded correctly
            doc_id = session.get("doc_id")
            file = request.files['file']
            if file and allowed_file(file.filename): #ensure if the file has the same extention that are accepted
                filename = secure_filename(file.filename)  
                file_extention = file_ext(filename) #recall to the function that is defined up

                photo_name = f"{doc_id}.{file_extention}" #renaming the file with an f string with the doc_id and the file extention
                photo_path = os.path.join(app.config['UPLOAD_FOLDER_LOGO'], photo_name) #to get the photo path that h will save on

                file.save(photo_path) #saving the file

                db.execute("UPDATE doctors SET logo_path = ? WHERE doc_id = ?", photo_name, doc_id) #a sqlite3 query to put the photo name on the database
                doctor, prices,appoint_times = show_doctor_details()
                return render_template("doctor_details.html", doctor=doctor, prices=prices,appoint_times=appoint_times)
            else:
                error = "Invalid file format. Allowed formats are: png, jpg, jpeg" #if the extention isn't from allowed shows this error 
                return render_template("upload.html", error=error)
        else:
            error = "file upload failed"
            return render_template("upload.html", error=error)


#a function to delete the images from the database and from the server it own
def image_delete():
    doc_id = session.get("doc_id")
    photo_name = db.execute("SELECT * FROM doctors WHERE doc_id = ?", doc_id)

    if len(photo_name) > 0:
        photo_name = photo_name[0]["photo_path"] #to fetch the data from teh database because this can't be done automaticly on the cs50 library
        if photo_name: #to ensue that the file name is founde
            file_extension = file_ext(photo_name) #to get the extention of the file with the recall of the function mentiend before

            photo_name = f"{doc_id}.{file_extension}" #using f string to rename the filename again
            photo_path = os.path.join(app.config['UPLOAD_FOLDER_PHOTO'], photo_name) #to get the photo path to delete it 

            if os.path.exists(photo_path): #ensure that this path have a file
                os.remove(photo_path) #delete the file using the os library
                delete = db.execute("UPDATE doctors SET photo_path = NULL WHERE doc_id = ?", doc_id) #a sqlite3 querry to set the photo_path in the database a null again
                return delete
            else:
                error = "File not found or unable to delete." #a condition if there is not file
                return render_template("error.html", error=error)
        else:
            error = "No image associated with this doctor to delete." #if this docotr don't have an image
            return render_template("error.html", error=error)
                
#a route to delete a saved photo to a doctor from the files and from the database
@app.route("/delete_image", methods=["POST"])
def delete_image():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        #calling the delete image function that delet from the database the images
        image_delete()
        return redirect("/doctor_details")

@app.route("/delete_logo", methods=["POST"])
def delete_logo():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        photo_name = db.execute("SELECT * FROM doctors WHERE doc_id = ?", doc_id)

        if len(photo_name) > 0:
            photo_name = photo_name[0]["logo_path"] #to fetch the data from teh database because this can't be done automaticly on the cs50 library
            if photo_name: #to ensue that the file name is founde
                file_extension = file_ext(photo_name) #to get the extention of the file with the recall of the function mentiend before

                photo_name = f"{doc_id}.{file_extension}" #using f string to rename the filename again
                logo_path = os.path.join(app.config['UPLOAD_FOLDER_LOGO'], photo_name) #to get the photo path to delete it 

                if os.path.exists(logo_path): #ensure that this path have a file
                    os.remove(logo_path) #delete the file using the os library
                    db.execute("UPDATE doctors SET logo_path = NULL WHERE doc_id = ?", doc_id) #a sqlite3 querry to set the photo_path in the database a null again
                    return redirect("/doctor_details")
                else:
                    error = "File not found or unable to delete." #a condition if there is not file
                    return render_template("error.html", error=error)
            else:
                error = "No image associated with this doctor to delete." #if this docotr don't have an image
                return render_template("error.html", error=error)
        return redirect("/doctor_details")
            

#redirect to a page that the doctor could add his prices for every patient category and for every price_cat
@app.route("/price_cat_redirect", methods=["GET"])
def price_cat_redirect():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doctor, prices,appoint_times = show_doctor_details()
        return render_template("price_cat.html", prices=prices, doctor=doctor, appoint_times=appoint_times)

#the page that the doctor can put his prices categories
@app.route("/price_cat", methods=["POST"])
def price_cat():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        price_category = request.form.get("price_category")
        patient_cat = request.form.get("patient_cat")
        price = request.form.get("price")

        existing_price_categories = db.execute(
            "SELECT * FROM price_cat WHERE doc_id = ? AND price_category = ? AND patient_cat = ?",
            doc_id, price_category, patient_cat) #selects every thing from the price_cat where the doc_id and the price_category and the patient_cat is like given before

        if not existing_price_categories:#checks if there is no saved data with this condotions from the mentioned before to be sure that there is no 2 prices by the same doctor for the same categories exactly
            db.execute(
                "INSERT INTO price_cat (doc_id, price_category, price, patient_cat) VALUES (?,?,?,?)",
                doc_id, price_category, price, patient_cat)
            patient_cat_check = db.execute("SELECT category FROM patient_cat WHERE doc_id = ?", doc_id)
            existing_categories = []
            for row in patient_cat_check:
                existing_categories.append(row['category'])

            if patient_cat not in existing_categories:
                db.execute("INSERT INTO patient_cat (doc_id, category) VALUES (?,?)", doc_id, patient_cat)
                doctor, prices, appoint_times = show_doctor_details()
                return render_template("price_cat.html", doctor=doctor, prices=prices, appoint_times=appoint_times)
        else:#an error massege shows when a doctor puts two prices for the same prices category
            error = "This Price Category and Patient Category combination is already assigned."
            doctor, prices, appoint_times = show_doctor_details()
            return render_template("price_cat.html", error=error, doctor=doctor, prices=prices, appoint_times=appoint_times)
        
@app.route("/trans_doc")
def trans_doc():
    if not session.get("logged_in"):
        return render_template("login.html")
    else:
        doc_id = session.get("doc_id")
        datas = db.execute("SELECT * FROM transactions WHERE doc_id = ? ORDER BY date", doc_id)
        sum = db.execute("SELECT SUM(price) FROM transactions WHERE doc_id = ? ORDER BY date", doc_id)
        return render_template("all_trans_doc.html", datas = datas, sum=sum)

@app.route("/filter_date_doc", methods=["GET"])
def filter_date_doc():
    if not session.get("logged_in"):
        return redirect("/login")
    else:
        doc_id =session.get("doc_id")
        date1 = request.args.get("date1")
        date2 = request.args.get("date2")
        query = """
            SELECT *
            FROM transactions 
            WHERE date BETWEEN ? AND ? AND doc_id = ?
            ORDER BY date
        """
        datas = db.execute(query, date1, date2, doc_id)
        sum = db.execute("SELECT SUM(price) FROM transactions WHERE doc_id = ? AND date BETWEEN ? AND ? ORDER BY date", doc_id, date1, date2)
        return render_template("all_trans_doc.html", datas=datas, sum=sum)

#the page that tha admin see when he open account (admin module)
@app.route("/admin_home")
def admin_home():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        datas = db.execute("SELECT * FROM transactions")#this page have all of the transactions done by the doctors and patients
        return render_template("admin_home.html", datas = datas)
    
#a route that returns a register page to the admin users
@app.route("/register_redirect")
def register_redirect():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        return render_template("register.html")

#the route that add a new user by an admin
@app.route("/register", methods=["POST"])
def register():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        username = (request.form.get("username").strip()).lower()
        password = encrypt()
        category = request.form.get("category")
        doc_name = request.form.get("doc_name")
        doc_phone_number = request.form.get("doc_phone_number")
        user_cat = request.form.get("user_cat")

    existing_user = db.execute("SELECT * FROM( SELECT username FROM doctors WHERE LOWER(username) = ? UNION ALL SELECT username FROM assistants WHERE LOWER(username) =?) AS combined_table", username, username)

    if existing_user and user_cat == "doctor":#an if condition to see if this username is saved by another user
        error_existing = "Username is unavailable. Please choose another one."
        return render_template("register_doctor.html", error=error_existing)
    
    elif existing_user and user_cat == "admin":#an if condition to see if this username is saved by another user
        error_existing = "Username is unavailable. Please choose another one."
        return render_template("register_admin.html", error=error_existing)
    
    else:
        db.execute("INSERT INTO doctors (username, password, category, doc_name, doc_phone_number, user_cat) VALUES (?, ?, ? ,? , ?, ?)", username, password, category, doc_name, doc_phone_number, user_cat)
        return redirect("/show_all_doctors")
        
@app.route("/show_all_doctors", methods=["GET"])#a route that shows all of the doctors on only one page
def show_all_doctors():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        doctor = db.execute("SELECT * FROM doctors WHERE user_cat = ? ORDER BY doc_name COLLATE NOCASE", "doctor" )
        return render_template("show_all_doctors.html", doctor=doctor)

@app.route("/show_all_admin", methods=["GET"])#a route that shows all of the doctors on only one page
def show_all_admin():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        admin = db.execute("SELECT * FROM doctors WHERE user_cat = ? ORDER BY doc_name COLLATE NOCASE", "admin" )
        return render_template("show_all_admin.html", admin=admin)

@app.route("/show_all_assi", methods=["GET"])#a route that shows all of the doctors on only one page
def show_all_assi():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        query = """
            SELECT doctors.doc_id , assistants.a_phonenumber, assistants.a_name, doctors.a_id
            FROM assistants 
            INNER JOIN doctors ON doctors.a_id = assistants.a_id 
        """
        doctor = db.execute(query)
        return render_template("show_all_assi.html", doctor=doctor)
    
@app.route("/show_all_patients", methods=["GET"])#a route that shows all of the patients on only one page
def show_all_patients():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        patients = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients ORDER BY name COLLATE NOCASE")
        return render_template("show_all_patients.html", patients=patients)
    
@app.route("/doctor_show_details_admin", methods=["POST"])#a route that opens a page that have all of the doctors details except the password (for secuirity)
def doctor_show_details_admin():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        doc_id = request.form.get("doc_id")
        prices = db.execute("SELECT * FROM price_cat WHERE doc_id = ?", doc_id)
        doctor = db.execute("SELECT * FROM doctors WHERE doc_id = ?", doc_id)
        return render_template("doctor_show_details_admin.html", doctor = doctor, prices=prices)
    
    #a route that make the admin can edit and modify the doctor prices
@app.route("/edit_prices", methods=["POST"])
def edit_prices():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        doc_id = request.form.get("doc_id")
        price_cat_id = request.form.get("price_cat_id")
        prices = db.execute("SELECT * FROM price_cat WHERE doc_id = ? AND price_cat_id = ?", doc_id, price_cat_id)
        return render_template("edit_prices.html", prices=prices)
    
    #a route the execute the route before that
@app.route("/update_prices", methods=["POST"])
def edit_price_0():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        doc_id = request.form.get("doc_id")
        price = request.form.get("price")
        price_cat_id = request.form.get("price_cat_id")
        db.execute("UPDATE price_cat SET price = ? WHERE doc_id = ? AND price_cat_id = ?", price, doc_id, price_cat_id)
        return redirect("/show_all_doctors")
    
    #a route that make a search by patient's id to show this specific patient
@app.route("/search_patient_id", methods=["GET"])
def search_patient_id():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        id = request.args.get("id")
        if id:
            person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE id = ? ORDER BY name", id)
            return render_template("search_patient_admin.html", patients=person)
        else:
            return render_template("search_patient_admin.html", patients=[])
        
        #a route that make a search by doctor's id to show this specific doctor
@app.route("/search_doctor_id", methods=["GET"])
def search_doctor_id():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        doc_id = request.args.get("doc_id")
        if doc_id:
            doctor = db.execute("SELECT * FROM doctors WHERE doc_id = ? ORDER BY doc_name", doc_id)
            return render_template("search_doctor_admin.html", doctor=doctor)
        else:
            return render_template("search_doctor_admin.html", doctor=[])

#a route that filters the tarnsacation by the date of it to show that dates between these two dates
@app.route("/filter_date", methods=["GET"])
def filter_date():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        date1 = request.args.get("date1")
        date2 = request.args.get("date2")
        query = """
            SELECT *
            FROM transactions 
            WHERE date BETWEEN ? AND ? 
            ORDER BY date
        """
        datas = db.execute(query, date1, date2)
        return render_template("search_transactions.html", datas=datas)
    
#a route to delete a patient from the database
@app.route("/delete_patient", methods=["POST"])
def delete_patient():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        id = request.form.get("id")
        if id:
            db.execute("DELETE FROM details WHERE id = ?", id)
            db.execute("DELETE FROM transactions WHERE id = ?", id)
            db.execute("DELETE FROM patients WHERE id = ?", id)
        return redirect("/show_all_patients")

#a route to delete a doctor from the database and delete all of his data
@app.route("/delete_doctor", methods=["POST"])
def delete_doctor():
    if not session.get("logged_in_admin"):
        return redirect("/login")
    else:
        doc_id = request.form.get("doc_id")
        if id: 
            photo_name = db.execute("SELECT * FROM doctors WHERE doc_id = ?", doc_id)

            if len(photo_name) > 0:
                photo_name = photo_name[0]["photo_path"] #to fetch the data from teh database because this can't be done automaticly on the cs50 library
                if photo_name: #to ensue that the file name is founde
                    file_extension = file_ext(photo_name) #to get the extention of the file with the recall of the function mentiend before

                    photo_name = f"{doc_id}.{file_extension}" #using f string to rename the filename again
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER_PHOTO'], photo_name) #to get the photo path to delete it 

                    if os.path.exists(photo_path): #ensure that this path have a file
                        os.remove(photo_path) #delete the file using the os library
                        db.execute("UPDATE doctors SET photo_path = NULL WHERE doc_id = ?", doc_id) #a sqlite3 querry to set the photo_path in the database a null again
            
            db.execute("DELETE FROM details WHERE doc_id = ?", doc_id)
            db.execute("DELETE FROM transactions WHERE doc_id = ?", doc_id)
            db.execute("DELETE FROM price_cat WHERE doc_id = ?", doc_id)
            db.execute("DELETE FROM patients WHERE doc_id = ?", doc_id)
            db.execute("DELETE FROM doctors WHERE doc_id = ?", doc_id)
            return redirect("/show_all_doctors")
        
@app.route("/version_admin", methods=["GET"])
def version_admin():
    if not session.get("logged_in_admin"):
        return render_template("login.html")
    else:
        return render_template("version_admin.html")

@app.route("/version_doctor", methods=["GET"])
def version_doctor():
    if not session.get("logged_in"):
        return render_template("login.html")
    else:
        return render_template("version_doctor.html")

@app.route("/version_public", methods=["GET"])
def version_public():
    return render_template("version_public.html")

@app.route("/version_assi", methods=["GET"])
def version_assi():
    if not session.get("logged_in_assistant"):
        return render_template("login.html")
    else:
        return render_template("version_assi.html")

def backup_database():
    source_db_path = '//home//kbclinic//kbclinic.db'
    backup_folder = '//home//kbclinic//db_Backup'
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup_{current_time}.db"
    backup_db_path = backup_folder + backup_filename

    if not os.path.exists(backup_db_path):
        try:
            shutil.copyfile(source_db_path, backup_db_path)
            print(f"Database backup completed: {backup_filename}")
        except Exception as e:
            print(f"An error occurred during backup: {e}")
    else:
        print(f"Backup file already exists for: {backup_filename}")

@app.route("/backup_databse", methods=["POST"])
def backup_run():
    if not session.get("logged_in_admin"):
        return render_template("login.html")
    else:
        backup_database()
        done = "Backed Up successfully"
        return render_template("admin_home.html", done=done)
    
@app.route("/register_doctor_redirect")
def register_doctor_redirect():
    if not session.get("logged_in_admin"):
        return render_template("login.html")
    else:
        return render_template("register_doctor.html")

@app.route("/register_admin_redirect")
def register_admin_redirect():
    if not session.get("logged_in_admin"):
        return render_template("login.html")
    else:
        return render_template("register_admin.html") 

@app.route("/register_a_redirect")
def register_a_redirect():
    if not session.get("logged_in_admin"):
        return render_template("login.html")
    else:
        doc = db.execute("SELECT * FROM doctors WHERE user_cat = ?", "doctor")
        return render_template("register_a.html", doc=doc)

@app.route("/register_a", methods=["POST"])
def register_a():
    if not session.get("logged_in_admin"):
        return render_template("login.html")
    else:
        username = (request.form.get("username").strip()).lower()
        password = encrypt()
        doc_name = request.form.get("doc_name")
        doc_phone_number = request.form.get("doc_phone_number")
        
        existing_user = db.execute("SELECT * FROM( SELECT username FROM doctors WHERE LOWER(username) = ? UNION ALL SELECT username FROM assistants WHERE LOWER(username) =?) AS combined_table", username, username)
        if existing_user:#an if condition to see if this username is saved by another user
            error = "Username is unavailable. Please choose another one."
            doc = db.execute("SELECT * FROM doctors WHERE user_cat = ?", "doctor")
            return render_template("register_a.html", error=error, doc=doc)
        
        else:
            db.execute("INSERT INTO assistants (username, password, a_name, a_phonenumber, user_cat) VALUES (?, ?, ? ,? ,?)", username, password, doc_name, doc_phone_number, "assistant")

            a_id_querry = db.execute("SELECT a_id FROM assistants WHERE username = ? AND password = ?", username, password)
        
            if len(a_id_querry) > 0:
                a_id = a_id_querry[0]["a_id"]

                selected_docs = request.form.getlist("selected_docs[]")
                for selected_doc in selected_docs:
                        db.execute("UPDATE doctors SET a_id = ? WHERE doc_id = ?", a_id, selected_doc)
            return redirect("/show_all_doctors")

def assistant_id():
        a_id = session.get("a_id")
        doc_id_query = db.execute("SELECT doc_id FROM doctors WHERE a_id = ?", a_id)
        if len(doc_id_query) > 0:
            doc_id = doc_id_query[0]["doc_id"]
        return doc_id

@app.route("/assistant_home")
def assistant_home():
    if not session.get("logged_in_assistant"):
        return render_template("login.html")
    else:
        current_date = datetime.now().strftime('%Y-%m-%d')
        date = datetime.now().date()
        doc_id = assistant_id()
        appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ?", doc_id, date)
        return render_template("assistant_home.html", appoint=appoint, current_date=current_date)

@app.route("/filter_date_home_assi", methods=["GET"])
def filter_date_home_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        doc_id = assistant_id()
        date = request.args.get("date_filter")
        appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ? ORDER BY time", doc_id, date)
        return render_template("assistant_home.html", appoint=appoint)

@app.route("/trans_assi")
def trans_assi():
    if not session.get("logged_in_assistant"):
        return render_template("login.html")
    else:
        doc_id = assistant_id()
        datas = db.execute("SELECT * FROM transactions WHERE doc_id = ?", doc_id)
        sum = db.execute("SELECT SUM(price) FROM transactions WHERE doc_id = ? ORDER BY date", doc_id)
        return render_template("all_trans_assi.html", datas = datas, sum=sum)

@app.route("/show_all_patients_a", methods=["GET"])#a route that shows all of the patients on only one page
def show_all_patients_a():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        doc_id = assistant_id()
        patients = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE doc_id = ? ORDER BY name COLLATE NOCASE", doc_id)
        return render_template("show_all_patients_a.html", patients=patients)

@app.route("/add_new_a")
def add_new_a():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        doc_id = session.get("doc_id")
        patient_cat = db.execute("SELECT * FROM patient_cat WHERE doc_id = ?", doc_id)
        return render_template("add_new_a.html", patient_cat=patient_cat)
  
@app.route("/add_patient_a", methods=["POST"])
def add_patient_a():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        name = request.form.get("name")
        phone_number = request.form.get("phone_number")
        birthdate = request.form.get("birthdate")
        gender = request.form.get("gender")
        patient_cat = request.form.get("patient_cat")
        doc_id = assistant_id()
        db.execute("SELECT * FROM price_cat WHERE doc_id = ?", doc_id)
        db.execute("INSERT INTO patients ( doc_id, name, phone_number, birthdate, gender, patient_cat) VALUES(?, ?, ?, ?, ?, ?)",
                    doc_id, name, phone_number, birthdate, gender ,patient_cat)
        return redirect("/show_all_patients_a")
    
@app.route("/filter_date_assi", methods=["GET"])
def filter_date_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        doc_id = assistant_id()
        date1 = request.args.get("date1")
        date2 = request.args.get("date2")
        query = """
            SELECT *
            FROM transactions 
            WHERE date BETWEEN ? AND ? AND doc_id = ?
            ORDER BY date
        """
        datas = db.execute(query, date1, date2, doc_id)
        sum = db.execute("SELECT SUM(price) FROM transactions WHERE doc_id = ? AND date BETWEEN ? AND ? ORDER BY date", doc_id, date1, date2)
        return render_template("search_transactions_assi.html", datas=datas, sum=sum)
    
#a route that filter the shown data on the show all page by gender to show "male" or "female"
@app.route("/filter_gender_assi", methods=["GET"])
def filetr_gender_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        gender = request.args.get("gender")
        doc_id = assistant_id()
        if gender:
            person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE gender = ? AND doc_id = ? ORDER BY name", gender, doc_id)
            return render_template("table_all_patients_a.html", patients=person)
        else:
            return render_template("table_all_patients_a.html", patients=[])

#a route that filter the shown data on the show all page by age to show people who are between the two age that are written
@app.route("/filter_age_assi", methods=["GET"])
def filter_age_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        age1 = request.args.get("age1")
        age2 = int(request.args.get("age2"))
        age2_1 = age2 + 1
        doc_id = assistant_id()
        query = """
            SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - 
            (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age 
            FROM patients 
            WHERE doc_id = ? AND 
            date('now') >= date(birthdate, '+' || ? || ' years') AND 
            date('now') <= date(birthdate, '+' || ? || ' years')
            ORDER BY name
        """
        person = db.execute(query, doc_id, age1, age2_1)
        return render_template("table_all_patients_a.html", patients=person)
    
#a route to search by id for a person on the database with the doc_id of the doctor signed-in
@app.route("/search_id_assi", methods=["GET"])
def search_id_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        id = request.args.get("id")
        doc_id = assistant_id()
        if id:
            person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE id = ? AND doc_id = ? ORDER BY name", id, doc_id)
            return render_template("table_all_patients_a.html", patients=person)
        else:
            return render_template("table_all_patients_a.html", patients=[])
        
@app.route("/open_patient_assi", methods=["GET"])
def open_patien_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        id = request.args.get("id")
        person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE id = ? ", id)
        details = db.execute("SELECT * FROM details WHERE id = ?", id)
        return render_template("open_patient_assi.html", person = person, details=details)
    
#a route to search by id for a person on the database with the doc_id of the doctor signed-in
@app.route("/search_phone_assi", methods=["GET"])
def search_phone_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        phone_number = request.args.get("phone_number")
        doc_id = assistant_id()
        if phone_number:
            person = db.execute("SELECT *, strftime('%Y', 'now') - strftime('%Y', birthdate) - (strftime('%m-%d', 'now') < strftime('%m-%d', birthdate)) AS age FROM patients WHERE phone_number = ? AND doc_id = ? ORDER BY name", phone_number, doc_id)
            return render_template("table_all_patients_a.html", patients=person)
        else:
            return render_template("table_all_patients_a.html", patients=[])
        
@app.route("/add_appoint_date_assi_redirect", methods=["POST"])
def add_appoint_date_assi_redirect():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        id = request.form.get("id")
        doc_id = assistant_id()
        person = db.execute("SELECT * FROM patients WHERE id = ?", id)
        prices_cat = db.execute("SELECT DISTINCT price_category FROM price_cat WHERE doc_id = ?", doc_id)
       # Define the current date and the date one month ahead
        current_date = datetime.now()
        next_month = current_date + timedelta(days=7)

        # Prepare to collect free time slots
        free_appoint = []

        # Iterate through each day in the next month
        while current_date <= next_month:
            day_of_week = current_date.strftime("%A")
            times = db.execute("SELECT * FROM appoint_time WHERE doc_id = ? AND day = ?", doc_id, day_of_week)

            if times:
                time1 = datetime.strptime(times[0]["time1"], "%H:%M")
                time2 = datetime.strptime(times[0]["time2"], "%H:%M")
                separate_time = timedelta(minutes=times[0]["seperate_time"])

                current_time = time1
                while current_time + separate_time <= time2:
                    existing_appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ? AND time = ?", doc_id, current_date.strftime("%Y-%m-%d"), current_time.strftime("%H:%M"))
                    if not existing_appoint:
                        free_appoint.append({'date': current_date.strftime("%Y-%m-%d"), 'time': current_time.strftime("%H:%M"), 'day_of_week' : day_of_week})
                    current_time += separate_time

            current_date += timedelta(days=1)
        return render_template("add_appoint_assi.html", person=person, free_appoint=free_appoint, prices_cat=prices_cat)

@app.route("/add_appoint_assi", methods = ["POST"])
def app_appoint_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        id = request.form.get("id")
        doc_id = assistant_id()
        datetime = request.form.get("datetime")
        date , time = datetime.split()
        category = request.form.get("category")
        db.execute("INSERT INTO appoint(id, doc_id, date, category, time, status) VALUES (?,?,?,?,?,?)", id, doc_id, date, category, time, "Not Done")
        return redirect("/show_all_patients_a")

@app.route("/edit_appoint_assi", methods=["POST"])
def edit_appoint_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        doc_id = assistant_id()
        appoint_id = request.form.get("appoint_id")
        date = request.form.get("date")
        chech_appoint_status = db.execute("SELECT status FROM appoint WHERE appoint_id = ?", appoint_id)

        if len(chech_appoint_status) > 0:
            appoint_status = chech_appoint_status[0]["status"]

        if appoint_status == "Not Done":
            appoint = db.execute("SELECT * FROM appoint WHERE appoint_id = ?", appoint_id)
            prices_cat = db.execute("SELECT DISTINCT price_category FROM price_cat WHERE doc_id = ?", doc_id)
            date_object = datetime.strptime(date, "%Y-%m-%d")

            # Get the day of the week as a string (e.g., "Monday")
            day_of_week = date_object.strftime("%A")

            time = db.execute("SELECT * FROM appoint_time WHERE doc_id = ? AND day = ?",doc_id, day_of_week)
            free_time = []
            if len(time) > 0:
                time1 = datetime.strptime(time[0]["time1"], "%H:%M")
                time2 = datetime.strptime(time[0]["time2"], "%H:%M")
                separate_time = timedelta(minutes=time[0]["seperate_time"])

                current_time = time1
                while current_time + separate_time <= time2:
                    existing_appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ? AND time = ? AND appoint_id != ?", doc_id, date, current_time.strftime("%H:%M"), appoint_id)
                    if not existing_appoint:
                        free_time.append(current_time.strftime("%H:%M"))
                    current_time += separate_time
            return render_template("edit_appoint_assi.html", appoint=appoint, prices_cat=prices_cat , free_time = free_time)
        else:
            error = "Can't Edit This Appointment Is Done"
            current_date = datetime.now().strftime('%Y-%m-%d')
            date = datetime.now().date()
            doc_id = assistant_id()
            appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ?", doc_id, date)
            return render_template("assistant_home.html", appoint=appoint, current_date=current_date, error=error)

@app.route("/update_appoint_assi", methods=["POST"])
def update_appoint_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        appoint_id = request.form.get("appoint_id")
        time = request.form.get("time")
        category = request.form.get("category")
        status = request.form.get("status")
        db.execute("UPDATE appoint SET time = ? , category = ? , status = ? WHERE appoint_id = ?", time, category, status, appoint_id)
        return redirect("/assistant_home") 

@app.route("/delete_appoint_assi", methods=["POST"])
def delete_appoint_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        appoint_id = request.form.get("appoint_id")
        chech_appoint_status = db.execute("SELECT status FROM appoint WHERE appoint_id = ?", appoint_id)

        if len(chech_appoint_status) > 0:
            appoint_status = chech_appoint_status[0]["status"]

        if appoint_status == "Not Done":
            db.execute("DELETE FROM appoint WHERE appoint_id = ?", appoint_id)
            return redirect("/assistant_home")
        else :
            error = "Can't Delete This Appointment Is Done"
            current_date = datetime.now().strftime('%Y-%m-%d')
            date = datetime.now().date()
            doc_id = assistant_id()
            appoint = db.execute("SELECT * FROM appoint WHERE doc_id = ? AND date = ?", doc_id, date)
            return render_template("assistant_home.html", appoint=appoint, current_date=current_date, error=error)

@app.route("/edit_assi", methods=["GET"])
def edit_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        a_id = session.get("a_id")
        assi = db.execute("SELECT * FROM assistants WHERE a_id = ?", a_id)
        return render_template("edit_assi.html", assi=assi)

@app.route("/update_assi", methods=["POST"])
def update_assi():
    if not session.get("logged_in_assistant"):
        return redirect("/login")
    else:
        a_id = session.get("a_id")
        username = request.form.get("username")
        a_name = request.form.get("a_name")
        a_phonenumber = request.form.get("a_phonenumber")
        existing_user_query = db.execute("SELECT a_id FROM assistants WHERE LOWER(username) = ?", username)

        if len(existing_user_query) > 0:
            existing_user = existing_user_query[0]["a_id"]

        if existing_user_query and existing_user != a_id:
            error = "Username is unavailable. Please choose another one."
            assi = db.execute("SELECT * FROM assistants WHERE a_id = ?", a_id)
            return render_template("edit_doctor.html", assi=assi, error=error)
        else:
            db.execute("UPDATE assistants SET username = ?, a_name = ?, a_phonenumber = ? WHERE a_id = ?", username,a_name, a_phonenumber, a_id)
            return redirect("/assistant_home")
