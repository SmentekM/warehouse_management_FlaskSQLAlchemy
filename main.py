from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_alembic import Alembic

db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mag.db"
db.init_app(app)
alembic = Alembic()
alembic.init_app(app)


class Produkt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String, nullable=False)
    il = db.Column(db.Integer, nullable=False)
    cena= db.Column(db.Float, nullable=False)

    def __str__(self):
        return f'{self.nazwa} \\ {self.il} \\ {self.cena}'



class Konto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    konto = db.Column(db.Float, nullable=False)

    def __str__(self):
        return f'{self.konto}'

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zadanie = db.Column(db.String, nullable=False)

    def __str__(self):
        return f'{self.zadanie}'



with app.app_context():
    db.create_all()


def op_kon(db,zm):
    db.session.query(Konto).filter(Konto.id == "1").delete()
    db.session.add(zm)
    db.session.commit()
def zapis_history(db,zad):
    db.session.add(zad)
    db.session.commit()



@app.route('/', methods=['POST', 'GET'])
def index():
    title = "Witaj na stronie głownej Twojej firmy"
    mag = db.session.query(Produkt).all()
    kon = db.session.query(Konto).first()
    brak = "Brak towaru"

    print(db.session.query(Konto).all())
    print(mag)
    print(kon)

    if not kon:
        kon =0
        # kwota = Konto(konto=0)
        # db.session.add(kwota)
        # db.session.commit()

    else:
        kon = kon.konto

    if request.method == "POST":
        nazwa = str(request.form.get("nazwa"))
        ilosc_do_sprzedazy = request.form.get("ilosc")
        operacja = str(request.form.get("rodzaj"))
        kwota = request.form.get("kwota")
        nazwa_produktu = request.form.get('nazwa_zakupu')
        ilosc_do_zakupu = request.form.get('ilosc_zakupiona')
        cena = request.form.get('cena')
        if operacja and kwota:
            kwota = float(kwota)
            if operacja ==  "w":
                zm = Konto(konto=kon+kwota)
                op_kon(db, zm)
                zad = History(zadanie=f'wpłata {kwota}')
                zapis_history(db,zad)
            elif operacja == "p":
                zm = Konto(konto=kon - kwota)
                op_kon(db, zm)
                zad = History(zadanie=f'płatność {kwota}')
                zapis_history(db, zad)
            return redirect(url_for("index"))

        if nazwa and ilosc_do_sprzedazy:
            ilosc_do_sprzedazy = float(ilosc_do_sprzedazy)
            if db.session.query(Produkt).filter(Produkt.nazwa == nazwa).all():
                zmiana =db.session.query(Produkt).filter(Produkt.nazwa == nazwa).first()
                zmiana.il = zmiana.il -ilosc_do_sprzedazy
                db.session.add(zmiana)
                db.session.commit()
                zm = Konto(konto=kon + (ilosc_do_sprzedazy * zmiana.cena))
                op_kon(db, zm)
                zad = History(zadanie=f'sprzedaż {nazwa} w ilości {ilosc_do_sprzedazy}')
                zapis_history(db, zad)


        if nazwa_produktu and ilosc_do_zakupu and cena:
            ilosc_do_zakupu = int(ilosc_do_zakupu)
            cena = float(cena)

            if db.session.query(Produkt).filter(Produkt.nazwa==nazwa_produktu).all():
                zmiana = db.session.query(Produkt).filter(Produkt.nazwa == nazwa_produktu).first()
                zmiana.il =zmiana.il +ilosc_do_zakupu
                zmiana.cena =cena
                db.session.add(zmiana)
                db.session.commit()
                zm = Konto(konto=kon -(ilosc_do_zakupu*cena))
                op_kon(db, zm)
                zad = History(zadanie=f'zakup {nazwa_produktu} w ilości {ilosc_do_zakupu} w cenie {cena}')
                zapis_history(db, zad)


            else:
                p = Produkt(nazwa=nazwa_produktu, il=ilosc_do_zakupu, cena=cena)
                db.session.add(p)
                db.session.commit()
                zm = Konto(konto=kon - (ilosc_do_zakupu * cena))
                op_kon(db, zm)
                zad = History(zadanie=f'zakup {nazwa_produktu} w ilości {ilosc_do_zakupu} w cenie {cena}')
                zapis_history(db, zad)

        return redirect(url_for("index"))

    context = {
        "title": title,
        "saldo": kon,
        "magazyn": mag,
        "brak" : brak

    }
    return render_template('strona glowna.html', context=context)


@app.route('/history', methods=['POST', 'GET'])
def history():
    his = db.session.query(History).all()
    if request.method == "POST":
        start = request.form.get("start")
        koniec = request.form.get("koniec")
        return redirect(url_for("zakres_histori", start=start, koniec=koniec))
    else:

        title = "Historia operacji"
        context = {
            "title": title,
            "historia": his
        }
        return render_template('history.html', context=context)


@app.route('/history/<start>/<koniec>')
def zakres_histori(start, koniec):
    title = "Historia operacj w wybranym zakresie"
    max_zakres = int(db.session.query(func.max(History.id)).scalar())
    if int(koniec) > max_zakres:
        wiad = f"Niewłaściwy zakres minimalny zakres = 1, maksymalny zakres ={max_zakres}"
        context = {
            "title": title,
            "wiad": wiad
        }
    else:
        zakres = db.session.query(History).filter(History.id >= start, History.id <= koniec).all()

        context = {
            "title": title,
            "historia": zakres,
        }

    return render_template('history_zakres.html', context=context)



