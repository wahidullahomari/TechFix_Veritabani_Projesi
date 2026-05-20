import mysql.connector

class VeritabaniBaglantisi:
    def __init__(self):
        self.config = {
            'user': 'root',
            'password': 'wahid12345', 
            'host': '127.0.0.1',
            'database': 'TechFixDB'   
        }

    def _get_connection(self):
        return mysql.connector.connect(**self.config)

    def randevu_ekle(self, musteri_adi, email, telefon, cihaz_tipi, ariza):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Önce Müşteriyi Ekle
        cursor.callproc('SP_MusteriEkle', (musteri_adi, telefon, email))
        conn.commit()
        
        # Müşterinin yeni oluşan ID'sini bul
        cursor.execute("SELECT LAST_INSERT_ID()")
        musteri_id = cursor.fetchone()[0]
        
        # 2. Sonra Cihazı Ekle
        # MarkaModel alanı için geçici olarak 'Belirtilmedi' yazıyoruz, ücreti 0 gönderiyoruz
        cursor.callproc('SP_CihazEkle', (musteri_id, cihaz_tipi, 'Belirtilmedi', ariza, 0.00))
        conn.commit()
        
        # Cihazın yeni oluşan ID'sini bul (Bunu Takip No olarak kullanacağız)
        cursor.execute("SELECT LAST_INSERT_ID()")
        cihaz_id = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        return cihaz_id

    def kayit_sorgula(self, cihaz_id, telefon):
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.callproc('SP_TumCihazlariGetir')
        
        result = None
        for res in cursor.stored_results():
            tum_kayitlar = res.fetchall()
            for kayit in tum_kayitlar:
                if str(kayit['CihazID']) == str(cihaz_id) and kayit['Telefon'] == telefon:
                    result = kayit
                    break
        
        cursor.close()
        conn.close()
        return result

    def tum_kayitlari_getir(self):
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.callproc('SP_TumCihazlariGetir')
        results = []
        for res in cursor.stored_results():
            results = res.fetchall()
        cursor.close()
        conn.close()
        return results

    def cihaz_durum_guncelle(self, cihaz_id, durum, ucret):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.callproc('SP_CihazDurumGuncelle', (cihaz_id, durum, ucret))
            conn.commit()
            return True, "Durum ve ücret başarıyla güncellendi."
        except mysql.connector.Error as err:
            # Trigger hatasını burada yakalıyoruz
            return False, err.msg
        finally:
            cursor.close()
            conn.close()

    def cihaz_sil(self, cihaz_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.callproc('SP_CihazSil', (cihaz_id,))
        conn.commit()
        cursor.close()
        conn.close()