import re
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'RAF2021-2022'

mydb = mysql.connector.connect (
    host = 'localhost',
    user = 'root',
    password = '',
    database = 'kolokvijum2'
)

@app.route('/index')
def index():
    return 'Hello World'


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template(
            'register.html'
        )

    else:
        indeks = request.form['indeks']
        ime_prezime = request.form['ime_prezime']
        godina = request.form['godina']
        password = request.form['password']
        confirm = request.form['confirm']
        prosek = request.form['prosek']
        ispiti = request.form['ispiti']

        cursor = mydb.cursor(prepared = True)
        sql = "SELECT * FROM korisnik WHERE broj_indeksa = ?"
        values = (indeks, )
        cursor.execute(sql, values)

        res = cursor.fetchone()

        if res != None:
            return render_template(
                'register.html',
                indeks_error = 'Vec postoji nalog sa tim indeksom!'
            )

        if password != confirm:
            return render_template(
                'register.html',
                confirm_error = 'Lozinke se ne poklapaju!'
            )

        if float(prosek) < 6 or float(prosek) > 10:
            return render_template(
                'register.html',
                prosek_error = 'Prosek mora biti izmedju 6 i 10!'
            )

        if int(ispiti) < 0:
            return render_template(
                'register.html',
                ispiti_error = 'Broj polozenih ispita ne moze biti negativan!'
            )

        cursor = mydb.cursor(prepared = True)
        sql = "INSERT INTO korisnik VALUES (null, ?, ?, ?, ?, ?, ?)"
        values = (indeks, ime_prezime, godina, password, prosek, ispiti)
        cursor.execute(sql, values)
        mydb.commit()

        return redirect(
            url_for('show_all')
        )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'indeks' in session:
        return redirect('show_all')

    if request.method == 'GET':
        return render_template(
            'login.html'
        )

    indeks = request.form['indeks']
    password = request.form['password']

    cursor = mydb.cursor(prepared = True)
    sql = "SELECT * FROM korisnik WHERE broj_indeksa = ?"
    values = (indeks, )
    cursor.execute(sql, values)

    res = cursor.fetchone()

    if res == None:
        return render_template(
            'login.html',
            indeks_error = 'Indeks koji ste uneli ne postoji!'
        )

    res = dekodiraj(res)

    if password != res[4]:
        return render_template(
            'login.html',
            password_error = 'Pogresna lozinka!'
        )

    session['indeks'] = res[1]

    return redirect(
        url_for('show_all')
    )


@app.route('/logout')
def logout():
    if 'indeks' not in session:
        return redirect(
            url_for('show_all')
        )

    session.pop('indeks')
    return redirect(
        url_for('login')
    )


@app.route('/show_all')
def show_all():

    cursor = mydb.cursor(prepared = True)
    sql = "SELECT * FROM korisnik"
    cursor.execute(sql)
    
    res = cursor.fetchall()

    if res == None:
        'Ne postoji ni jedan korisnik u bazi'

    n = len(res)
    for i in range(n):
        res[i] = dekodiraj(res[i])

    return render_template(
        'show_all.html',
        korisnici = res
    )


@app.route('/update/<indeks>', methods=['GET', 'POST'])
def update(indeks):

    if 'indeks' not in session:
        return 'Morate se prijaviti da bi ste modifikovali vas nalog!'
    
    if session['indeks'] != indeks:
        return 'Nemate pravo da modifikujete tudji nalog!'

    cursor = mydb.cursor(prepared = True)
    sql = "SELECT * FROM korisnik WHERE broj_indeksa = ?"
    values = (indeks, )
    cursor.execute(sql, values)

    res = cursor.fetchone()

    if res == None:
        return 'Ne postoji nalog sa tim indeksom'

    res = dekodiraj(res)

    if request.method == 'GET':
        return render_template(
            'update.html',
            korisnik = res
        )

    if request.method == 'POST':
        ime_prezime = request.form['ime_prezime']
        godina = request.form['godina']
        password = request.form['password']
        confirm = request.form['confirm']
        prosek = request.form['prosek']
        ispiti = request.form['ispiti']

        if password != confirm:
            return render_template(
                'update.html',
                confirm_error = 'Lozinke se ne poklapaju!',
                korisnik = res
            )

        if float(prosek) < 6 or float(prosek) > 10:
            return render_template(
                'update.html',
                prosek_error = 'Prosek mora biti izmedju 6 i 10!',
                korisnik = res
            )

        if int(ispiti) < 0:
            return render_template(
                'update.html',
                ispiti_error = 'Broj polozenih ispita ne moze biti negativan!',
                korisnik = res
            )

        cursor = mydb.cursor(prepared = True)
        sql = "UPDATE korisnik SET ime_prezime = ?, godina_rodjenja = ?, sifra = ?, prosek = ?, polozeni_ispiti = ? WHERE broj_indeksa = ?"
        values = (ime_prezime, godina, password, prosek, ispiti, indeks)
        cursor.execute(sql, values)
        mydb.commit()

        return redirect(
            url_for('show_all')
        )


@app.route('/delete/<indeks>', methods=['POST'])
def delete(indeks):
    if 'indeks' not in session:
        return redirect(
            url_for('/login')
        )

    if session['indeks'] != indeks:
        return 'Ne mozete da brisete tudji nalog!'

    cursor = mydb.cursor(prepared = True)
    sql = "DELETE FROM korisnik WHERE broj_indeksa = ?"
    values = (indeks, )
    cursor.execute(sql, values)
    mydb.commit()

    session.pop('indeks')

    return redirect(
        url_for('show_all')
    )


@app.route('/better_than_average/<average>')
def better_average(average):
    cursor = mydb.cursor(prepared = True)
    sql = "SELECT * FROM korisnik WHERE prosek > ?"
    values = (average, )
    cursor.execute(sql, values)

    res = cursor.fetchall()

    if res == None:
        return 'Ne postoji korisnik koji ima veci prosek od navedenog!'

    n = len(res)
    for i in range(n):
        res[i] = dekodiraj(res[i])

    return render_template(
        'average.html',
        korisnici = res
    )

def dekodiraj(data):
    data = list(data)
    n = len(data)

    for i in range(n):
        if isinstance(data[i], bytearray):
            data[i] = data[i].decode()

    return data 



app.run(debug = True)