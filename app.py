import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash

# DAL'ı içeri aktar
from dal import VeritabaniBaglantisi

app = Flask(__name__)
app.secret_key = "super_secret_techfix_key_123"

# DAL Nesnesi
db = VeritabaniBaglantisi()

# Admin Bilgileri
ADMIN_USER = "admin"
ADMIN_PASS = "12345"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/randevu_al', methods=['POST'])
def randevu_al():
    musteri = request.form['musteri']
    email = request.form['email']
    telefon = request.form['telefon']
    cihaz = request.form['cihaz']
    ariza = request.form['ariza']
    
    # DAL üzerinden iki tabloya birden kayıt atacak fonksiyonu çağırıyoruz
    talep_id = db.randevu_ekle(musteri, email, telefon, cihaz, ariza)
    
    flash(f"Randevunuz başarıyla alındı! Takip Numaranız: #{talep_id}", "success")
    return redirect(url_for('home'))

@app.route('/sorgula', methods=['POST'])
def sorgula():
    kayit_no = request.form.get('kayit_no')
    telefon = request.form.get('telefon')
    
    if kayit_no.startswith('#'):
        kayit_no = kayit_no[1:]

    # DAL üzerinden sorgula
    kayit = db.kayit_sorgula(kayit_no, telefon)

    if kayit:
        # Arayüzün hata vermemesi için isimleri HTML'in beklediği formata çeviriyoruz
        formatli_kayit = {
            'id': kayit['CihazID'],
            'musteri': kayit['AdSoyad'],
            'cihaz': kayit['CihazTipi'],
            'ariza': kayit['MarkaModel'], # Geçici eşleştirme
            'ucret': kayit['TahminiUcret'],
            'durum': kayit['Durum']
        }
        return render_template('sorgu_sonuc.html', kayit=formatli_kayit)
    else:
        flash("Kayıt bulunamadı. Lütfen Takip No ve Telefonunuzu doğru girdiğinizden emin olun.", "error")
        return redirect(url_for('home') + '#takip')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Hatalı kullanıcı adı veya şifre!", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin')
@login_required
def admin_dashboard():
    tum_kayitlar = db.tum_kayitlari_getir()
    
    aktif_kayitlar = []
    gecmis_kayitlar = []
    ciro = 0
    
    for k in tum_kayitlar:
        formatli_kayit = {
            'id': k['CihazID'],
            'musteri': k['AdSoyad'],
            'telefon': k['Telefon'],
            'email': k.get('Email', ''), # Email eklendi
            'cihaz': k['CihazTipi'],
            'ariza': k.get('ArizaDetayi', k['MarkaModel']), # HTML'de uzun açıklama için
            'ucret': k['TahminiUcret'],
            'durum': k['Durum']
        }
        
        if k['Durum'] == 'TESLİM EDİLDİ':
            gecmis_kayitlar.append(formatli_kayit)
            ciro += k['TahminiUcret']
        else:
            aktif_kayitlar.append(formatli_kayit)

    return render_template('index.html', 
                           aktif_kayitlar=aktif_kayitlar, 
                           gecmis_kayitlar=gecmis_kayitlar, 
                           ciro=ciro, 
                           bekleyen=len(aktif_kayitlar), 
                           yeni_randevu=0, 
                           biten=len(gecmis_kayitlar))

@app.route('/update_status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    yeni_durum = request.form['yeni_durum']
    ucret = request.form.get('ucret', type=float) # Kuruşlu değerler için float

    if ucret is None:
        ucret = 0.00
        
    # Trigger kontrolü için DAL'dan gelen cevabı ayırıyoruz
    basarili, mesaj = db.cihaz_durum_guncelle(id, yeni_durum, ucret)
    
    if basarili:
        flash(mesaj, "success")
    else:
        flash(mesaj, "error") # Eksi fiyat girilirse burası çalışır ve sistem çökmez
        
    return redirect(url_for('admin_dashboard'))

@app.route('/add_manual', methods=['POST'])
@login_required
def add_manual():
    musteri = request.form['musteri']
    telefon = request.form['telefon']
    email = request.form.get('email', 'belirtilmedi@mail.com')
    cihaz = request.form['cihaz']
    ariza = request.form['ariza']
    
    talep_id = db.randevu_ekle(musteri, email, telefon, cihaz, ariza)
    flash(f"Manuel kayıt eklendi! Takip No: #{talep_id}", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete/<int:id>')
@login_required
def delete_service(id):
    db.cihaz_sil(id)
    flash("Kayıt kalıcı olarak silindi.", "success")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)