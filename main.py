import sqlite3
import hashlib
import re
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
      format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s', 
      handlers=[logging.FileHandler("uygulama.log", encoding = 'utf-8'),
                 logging.StreamHandler(sys.stdout)])
logger=logging.getLogger(__name__)

#cok kullanilan degisken
VT_YOLU="kullanicilar.db"

#Veritabani baglanma
def veritabani():
    logger.info("Veritabani baglanti kuruluyor ve tablo kontrol ediliyor.")
    try:
        with sqlite3.connect(VT_YOLU) as baglanti:
            imlec=baglanti.cursor()

        #Tablo olusturma
            imlec.execute("""
            CREATE TABLE IF NOT EXISTS uyeler(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  kullanici_adi TEXT UNIQUE,
                  sifre TEXT,
                  eposta  TEXT UNIQUE)
            """)
        baglanti.commit()
        logger.info("Veritabani (uyeler tablosu) basariyla kontrol edildi/olusturuldu.")
    except sqlite3.Error as e:
        logger.error(f"Veritabani hatasi: {e}")
veritabani()

#sifre gizleme 
def sifre_gizleme(sifre):
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()

#sifre kontrolu
def sifre_kontrol(sifre):
    if len(sifre) < 8:
        print("Sifre zayif, sifre en az 8 karakter olmalidir.")
        logger.warning("sifre kontrolu basarisiz: sifre en az 8 karakterden kisa.")
        return False
    elif not re.search(r"[a-z]", sifre):
        print("Sifre en az bir kucuk harf icermelidir.")
        logger.warning("Sifre konntrolu basarisiz: kucuk harf eksik.")
        return False
    elif not re.search(r"[A-Z]", sifre):
        print("Sifre en az bir buyuk karakter icermelidir.")
        logger.warning("sifre kontrolu basarisiz: buyuk harf eksik.")
        return False
    elif not re.search(r"\d", sifre):
        print("Sifre en az bir rakam icermelidir.")
        logging.warning("Sifre kontrol basarisiz: rekam eksik.")
        return False
    else:
        logger.info("Sifre kontrolu basarili.")
        return True

#email kontrol 
def email_kontrol(mail):
    ekalip=r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if re.match(ekalip, mail):
        logger.debug(f"Eposta kontrolu basarili: {mail}")
        return True #email hatasiz
    else:
        logger.warning(f"eposta kontrolu basarisiz : {mail}")
        return False #email hatali
    
#kayit olma sistemi
def kayit_ol():
    print("=== KULLANICI KAYIT SISTEMI ===")

    while True:
        kullanici_eposta=input("--- Eposta adresinizi giriniz ---\n")
        if email_kontrol(kullanici_eposta):
            break
        else:
            print("Hatali eposta adresi girdiniz, lutfen tekrar giriniz.")

    while True:
        sifre=input("--- Sifrenizi belirleyiniz ---\n[1 buyuk ve kucuk harf ve 1 sayi icermelidir en az 8 karakter olmasi gerekli!]\n ")
        sifre_tekrar=input("--- Sifrenizi tekrar giriniz ---\n")
        if not sifre_kontrol(sifre):
            print("Sifre gucsuz.")
            continue
        elif sifre != sifre_tekrar:
            print("Sifreler eslesmiyor, tekrar deneyiniz.")
            logging.warning("Kayit sirasinda sifreler eslesmedi.")
        else:
            gizli_sifre=sifre_gizleme(sifre)
            break

    while True:
        kullanici_adi=input("--- Kullanici adinizi belirleyiniz ---\n")
        with sqlite3.connect(VT_YOLU) as baglanti:
            imlec=baglanti.cursor()
            try:
                imlec.execute("INSERT INTO uyeler (kullanici_adi, sifre, eposta) VALUES (?, ?, ?)", (kullanici_adi,gizli_sifre, kullanici_eposta))
                baglanti.commit()
                print(f"{kullanici_adi}, basariyla kaydoldunuz.")
                logger.info(f"Yeni kullanici basariyla kaydedildi: kullanici adi {kullanici_adi}")
                break
            except sqlite3.IntegrityError:
                print("HATA : Kullanici adi kullanilmaktadir.")
                logger.warning(f"Kayit hatasi: kullanici ad/eposta zaten mevcut. Denenen kullanici adi {kullanici_adi}")
            except sqlite3.Error as e:
                logger.error(f"Kayit sirasinda veritabani hatasi olustu: {e}")

#Giris sistemi
def giris_sistemi():
    logger.info("Giris sureci baslatildi.")
    print("=== Giris sistemi ===")
    max_deneme=4
    deneme_sayisi=0
    while deneme_sayisi < max_deneme:
        kullanici_adi=input("--- Kullanici adini giriniz --- \n")
        sifre=input("--- Sifreniz ---\n")
        girilen_gizli_sifre= sifre_gizleme(sifre)

        with sqlite3.connect(VT_YOLU) as baglanti:
            try:
                imlec=baglanti.cursor()
                imlec.execute("SELECT * FROM uyeler WHERE kullanici_adi=? AND sifre=?", (kullanici_adi, girilen_gizli_sifre))
                kullanici=imlec.fetchone()
    
                if kullanici:
                    print(f"Sisteme hos geldin, {kullanici_adi}!")
                    logger.info(f"Kullanisi girisi basarili : {kullanici_adi}")
                    break
                else:
                    deneme_sayisi+=1
                    kalan_deneme = max_deneme -deneme_sayisi
                    if kalan_deneme > 0:
                        print(f"HATA: Kullanici adi veya sifre yanlis.")
                    else:
                        print("UYARI : deneme hakkiniz doldu, isleminiz sonlandiriliyor.")
                    logger.warning(f"Kullanici girisi basarisiz : kullanici adi {kullanici_adi}")
            except sqlite3.Error as e:
                logger.error(f"Giris sirasinda veritabani hatasi olustu.")

def sifre_yenileme():
    logger.info("Sifre yenimele sureci baslatildi.")
    print("=== Sifre yenileme sistemi ===")

    while True:
        eposta=input("--- E-posta adresinizi giriniz ---\n")
        if email_kontrol(eposta):
            break
        else:
            print("HATA : eposta adresi hatali.")
            logger.warning("Sifre yenileme: Hatali eposta girildi.")
        
    try:
        with sqlite3.connect(VT_YOLU) as baglanti:
            imlec=baglanti.cursor()
            imlec.execute("SELECT kullanici_adi FROM uyeler WHERE eposta=?", (eposta,))
            kullanici=imlec.fetchone()
    
            if not kullanici:
                print("BILGI : Bu eposta adresine kayitli bir kullanici bulunamadi.")
                return False 
        
            kullanici_adi=kullanici[0]
            print(f"E-posta adresiniz onaylandi. Kullanici : {kullanici_adi}")
        
        while True:
            yeni_sifre=input("--- Yeni sifre ---\n")
            yeni_sifre_tekrar=input("--- Yeni sifre tekrar ---\n")
            if yeni_sifre == yeni_sifre_tekrar:
                yeni_gizli_sifre=sifre_gizleme(yeni_sifre)
                break
            elif yeni_sifre != yeni_sifre_tekrar:
                print("Sifreler eslesmiyor. Tekrar deneyiniz.")
                logger.warning("Sifre yenileme: Yeni sifreler eslesmiyor.")
        imlec.execute("UPDATE uyeler SET sifre=? WHERE eposta=?", (yeni_gizli_sifre, eposta))
        baglanti.commit()

        print("Sifreniz basariyla guncellendi.")
        logger.info(f"Sifre basariyla guncellendi: kullanici {kullanici_adi}")
        return True
    except sqlite3.Error as e:
        logger.error(f"Sifre yenileme sirasinda veritabani hatasi olustu: {e}")
        return False 

def hesap_silme():
    logger.warning("Hesap silme baslatildi.")
    print("=== Hesap silme sistemi ===")
    while True:
        kullanici_adi=input("--- Silmek istediginiz hesap adi ---\n")
        sifre=input("--- Sifrenizi giriniz ---\n")
        girilen_gizli_sifre=sifre_gizleme(sifre)

        try:
            with sqlite3.connect(VT_YOLU) as baglanti:
                imlec=baglanti.cursor()
                imlec.execute("SELECT id FROM uyeler WHERE kullanici_adi=? and sifre=?", (kullanici_adi, girilen_gizli_sifre))
                kullanici=imlec.fetchone()

                if kullanici:
                    onay=input(f"DIKKAT! : {kullanici_adi} hesabiniz KALICI olarak silmek istediginize eminmisiniz :")
                    if onay.upper() == "EVET":
                        imlec.execute("DELETE FROM uyeler WHERE kullanici_adi=?", (kullanici_adi,))
                        baglanti.commit()
                        print(f"{kullanici_adi} hesabi basariyla silindi.")
                        logger.critical(f"Kullanici hesabi kalici olarak silindi : {kullanici_adi}")
                        return True
                    else:
                        print("Hesap silme iptal edildi.")
                        logger.warning("Hesap silme islemi iptal edildi", kullanici_adi)
                        return False
                else:
                    print("HATA : kullanici adi veya sifre hatali. Tekrar deneyiniz.")
                    logger.warning("Hesap silme denemesi basarisiz : Yanlis kimlik bilgisi.")
        except sqlite3.Error as e:
            print(f"Hata : Veritabani islemi sirasinda bir hata olustu: {e}")
            logger.warning(f"Hesap silme sirasinda veritabani hatasi olustu : {e}")
            return False

if __name__ == "__main__":
    kayit_ol()
    giris_sistemi()
    sifre_yenileme()
    hesap_silme()