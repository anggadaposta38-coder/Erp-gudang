import os
import sys
import csv
import datetime
import requests  # Modul utama untuk transfer data via internet

# ====================================================================
# 1. KONFIGURASI DATABASE ONLINE CLOUD (FIREBASE)
# ====================================================================
# Menggunakan URL REST API Firebase berdasarkan data proyek Anda
URL_FIREBASE = "https://erp-gudang-default-rtdb.firebaseio.com/"

USER_AKTIF = None
ROLE_AKTIF = None

def bersihkan_layar():
    """Membersihkan tampilan terminal layar HP agar rapi"""
    os.system('cls' if os.name == 'nt' else 'clear')

# ====================================================================
# 2. INISIALISASI DATA AWAL CLOUD (MENGGANTIKAN DDL SQLITE3)
# ====================================================================
def inisialisasi_sistem_user():
    """Membuat struktur tabel dan akun bawaan otomatis di cloud jika masih kosong"""
    try:
        # 1. Periksa tabel pengguna di internet
        respon_user = requests.get(f"{URL_FIREBASE}pengguna.json")
        data_user = respon_user.json()
        
        if data_user is None:
            # Daftarkan akun default jika database online Anda masih baru/kosong
            akun_bawaan = {
                "owner123": {"password": "adminowner", "role": "OWNER"},
                "stafgudang": {"password": "masukgudang", "role": "ADMIN"}
            }
            requests.put(f"{URL_FIREBASE}pengguna.json", json=akun_bawaan)
            print("\n[ SINKRONISASI CLOUD ] Akun bawaan berhasil dibuat di Internet:")
            print(" -> Owner : username = owner123  | password = adminowner")
            print(" -> Admin : username = stafgudang | password = masukgudang")
            
        # 2. Periksa katalog produk awal untuk simulasi data jika kosong
        respon_produk = requests.get(f"{URL_FIREBASE}produk.json")
        if respon_produk.json() is None:
            produk_awal = {
                "BRG001": {"sku": "SKU-BERAS", "nama_produk": "Beras Premium Win", "lokasi_rak": "A1", "stok_aktual": 50, "stok_minimum": 10, "satuan": "Kg"},
                "BRG002": {"sku": "SKU-MINYAK", "nama_produk": "Minyak Goreng 2L", "lokasi_rak": "B2", "stok_aktual": 125, "stok_minimum": 20, "satuan": "Pcs"}
            }
            requests.put(f"{URL_FIREBASE}produk.json", json=produk_awal)
            
    except Exception as e:
        print(f"[!] Gagal Terhubung ke Firebase Cloud: {e}")
        print("[!] Pastikan HP aktif internet dan Aturan (Rules) Firebase disetel ke true!")
        sys.exit()

# ====================================================================
# 3. MODUL SISTEM LOGIN & MANAJEMEN KARYAWAN ONLINE
# ====================================================================
def login_sistem():
    global USER_AKTIF, ROLE_AKTIF
    print("\n=================================")
    print("   LOGIN ERP GUDANG CLOUD - V2   ")
    print("=================================")
    
    percobaan = 3
    while percobaan > 0:
        username = input("Masukkan Username : ").strip().lower()
        password = input("Masukkan Password : ").strip()
        
        try:
            # Ambil detail data spesifik user langsung dari path internet
            respon = requests.get(f"{URL_FIREBASE}pengguna/{username}.json")
            user_data = respon.json()
            
            if user_data and user_data['password'] == password:
                USER_AKTIF = username
                ROLE_AKTIF = user_data['role']
                print(f"\n Login Sukses! Selamat datang, {USER_AKTIF} ({ROLE_AKTIF})")
                return True
            else:
                percobaan -= 1
                print(f"[!] Login Gagal: Username/Password salah. (Sisa: {percobaan})")
        except Exception as e:
            print(f"[!] Gangguan Server/Jaringan: {e}")
            return False
            
    print("\n[!] Akses Ditolak: Anda salah memasukkan sandi 3 kali.")
    return False

def menu_manajemen_karyawan():
    global USER_AKTIF
    while True:
        print("\n=================================")
        print("    MANAJEMEN KARYAWAN (CLOUD)   ")
        print("=================================")
        print("1. Lihat Daftar Karyawan/User")
        print("2. Tambah Karyawan Baru")
        print("3. Ubah Password Karyawan")
        print("4. Hapus Akun Karyawan")
        print("5. Ganti Username Karyawan")
        print("0. Kembali ke Menu Utama")
        print("---------------------------------")
        sub_pilihan = input("Pilih menu (0-5): ").strip()
        
        if sub_pilihan == '1':
            data = requests.get(f"{URL_FIREBASE}pengguna.json").json()
            print("\n--- DAFTAR PENGGUNA SISTEM ---")
            print(f"{'Username':<15} | {'Hak Akses (Role)'}")
            print("-" * 35)
            if data:
                for username, detail in data.items():
                    print(f"{username:<15} | {detail['role']}")
                    
        elif sub_pilihan == '2':
            print("\n--- TAMBAH KARYAWAN BARU ---")
            username = input("Masukkan Username Baru: ").strip().lower()
            password = input("Masukkan Password Baru: ").strip()
            role = input("Masukkan Role (OWNER/ADMIN): ").strip().upper()
            
            if role not in ['OWNER', 'ADMIN']:
                print("[!] Gagal: Role harus ditulis OWNER atau ADMIN.")
                continue
                
            requests.put(f"{URL_FIREBASE}pengguna/{username}.json", json={"password": password, "role": role})
            print(f" Sukses: Karyawan '{username}' dengan role [{role}] berhasil didaftarkan ke cloud!")
            
        elif sub_pilihan == '3':
            print("\n--- UBAH PASSWORD KARYAWAN ---")
            username = input("Masukkan Username Karyawan: ").strip().lower()
            user_exist = requests.get(f"{URL_FIREBASE}pengguna/{username}.json").json()
            
            if not user_exist:
                print("[!] Gagal: Username tidak ditemukan di server.")
            else:
                password_baru = input("Masukkan Password Baru: ").strip()
                requests.patch(f"{URL_FIREBASE}pengguna/{username}.json", json={"password": password_baru})
                print(f" Sukses: Password untuk user '{username}' berhasil diperbarui di cloud!")
                
        elif sub_pilihan == '4':
            print("\n--- HAPUS AKUN KARYAWAN ---")
            username = input("Masukkan Username yang akan dihapus: ").strip().lower()
            
            if username == USER_AKTIF:
                print("[!] Gagal: Anda tidak bisa menghapus akun Anda sendiri yang sedang aktif!")
            else:
                user_exist = requests.get(f"{URL_FIREBASE}pengguna/{username}.json").json()
                if not user_exist:
                    print("[!] Gagal: Username tidak ditemukan.")
                else:
                    konfirmasi = input(f"Apakah Anda yakin ingin menghapus '{username}' dari cloud? (y/n): ").strip().lower()
                    if konfirmasi == 'y':
                        requests.delete(f"{URL_FIREBASE}pengguna/{username}.json")
                        print(f" Sukses: Akun '{username}' telah dihapus dari sistem cloud.")

        elif sub_pilihan == '5':
            print("\n--- GANTI USERNAME KARYAWAN ---")
            username_lama = input("Masukkan Username yang ingin diganti: ").strip().lower()
            user_data = requests.get(f"{URL_FIREBASE}pengguna/{username_lama}.json").json()
            
            if not user_data:
                print("[!] Gagal: Username lama tidak ditemukan.")
            else:
                username_baru = input("Masukkan Username BARU: ").strip().lower()
                # Cek apakah username baru sudah dipakai orang lain
                target_exist = requests.get(f"{URL_FIREBASE}pengguna/{username_baru}.json").json()
                if target_exist:
                    print("[!] Gagal: Username baru sudah dipakai oleh orang lain.")
                else:
                    # Tulis data ke lokasi baru, hapus lokasi lama
                    requests.put(f"{URL_FIREBASE}pengguna/{username_baru}.json", json=user_data)
                    requests.delete(f"{URL_FIREBASE}pengguna/{username_lama}.json")
                    print(f" Sukses: Username '{username_lama}' diganti menjadi '{username_baru}'!")
                    if username_lama == USER_AKTIF:
                        USER_AKTIF = username_baru
                        
        elif sub_pilihan == '0':
            break
        else:
            print("[!] Pilihan tidak valid.")

# ====================================================================
# 4. MODUL UTAMA MANAJEMEN GUDANG OPERASIONAL
# ====================================================================
def lihat_stok():
    data_produk = requests.get(f"{URL_FIREBASE}produk.json").json()
    print("\n========================= LAPORAN STOK GUDANG ONLINE =========================")
    print(f"{'ID':<8} | {'SKU':<15} | {'Nama Produk':<20} | {'Rak':<8} | {'Stok':<6} | {'Status'}")
    print("-" * 75)
    
    if data_produk:
        for id_prod, item in data_produk.items():
            stok_sekarang = item['stok_aktual']
            stok_min = item['stok_minimum']
            if stok_sekarang <= stok_min:
                status = f"!! KRITIS ({stok_sekarang}/{stok_min} {item['satuan']}) !!"
            else:
                status = f"Aman ({stok_sekarang} {item['satuan']})"
            print(f"{id_prod:<8} | {item['sku']:<15} | {item['nama_produk']:<20} | {item['lokasi_rak']:<8} | {stok_sekarang:<6} | {status}")
    print("=======================================================================")

def transaksi_barang(jenis):
    global USER_AKTIF
    data_produk = requests.get(f"{URL_FIREBASE}produk.json").json()
    if not data_produk:
        print("[!] Gudang kosong, belum ada produk terdaftar."); return
        
    lihat_stok()
    id_input = input(f"\nMasukkan ID Produk (Contoh: BRG001) untuk {jenis}: ").strip().upper()
    
    if id_input in data_produk:
        try:
            jumlah = int(input(f"Masukkan Jumlah {jenis} untuk {data_produk[id_input]['nama_produk']}: "))
            ket = input("Masukkan Keterangan: ")
            
            stok_sekarang = data_produk[id_input]['stok_aktual']
            if jenis == 'KELUAR' and stok_sekarang < jumlah:
                print("[!] Gagal: Stok cloud tidak mencukupi!"); return
                
            stok_baru = (stok_sekarang + jumlah) if jenis == 'MASUK' else (stok_sekarang - jumlah)
            
            # 1. Update stok produk ke cloud
            requests.patch(f"{URL_FIREBASE}produk/{id_input}.json", json={"stok_aktual": stok_baru})
            
            # 2. Buat log transaksi_stok baru di server cloud
            waktu_sekarang = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data_transaksi = {
                "tanggal": waktu_sekarang,
                "sku": data_produk[id_input]['sku'],
                "nama_produk": data_produk[id_input]['nama_produk'],
                "jenis_transaksi": jenis,
                "jumlah": jumlah,
                "keterangan": ket,
                "diinput_oleh": USER_AKTIF
            }
            requests.post(f"{URL_FIREBASE}transaksi_stok.json", json=data_transaksi)
            print(f" Sukses: Transaksi online disimpan oleh {USER_AKTIF}!")
        except ValueError:
            print("[!] Input jumlah harus angka.")
    else:
        print("[!] ID Produk tidak ditemukan.")

def lihat_mutasi():
    print("\n--- MENGUNDUH DATA TRANS-MUTASI DARI SERVER INTERNET ---")
    data_mutasi = requests.get(f"{URL_FIREBASE}transaksi_stok.json").json()
    
    print(f"\n=================================== RIWAYAT MUTASI BARANG CLOUD ===================================")
    print(f"{'Tanggal & Waktu':<20} | {'SKU':<12} | {'Nama Produk':<15} | {'Jenis':<6} | {'Jml':<4} | {'Keterangan':<18} | {'Petugas Admin'}")
    print("-" * 110)
    
    if not data_mutasi:
        print("                                    --- Belum ada transaksi tercatat di database cloud ---              ")
    else:
        # Menampilkan data terbaru di urutan paling atas (Metode LIFO)
        for key in reversed(list(data_mutasi.keys())):
            r = data_mutasi[key]
            print(f"{r['tanggal']:<20} | {r['sku']:<12} | {r['nama_produk']:<15} | {r['jenis_transaksi']:<6} | {r['jumlah']:<4} | {r['keterangan']:<18} | {r['diinput_oleh']}")
    print("=============================================================================================")
    input("\nTekan Enter untuk kembali ke menu...")

def cari_barang():
    print("\n=== PENCARIAN CEPAT BARANG CLOUD ===")
    kata_kunci = input("Masukkan nama barang atau kode SKU yang dicari: ").strip().lower()
    data_produk = requests.get(f"{URL_FIREBASE}produk.json").json()
    
    print("\n--- Hasil Pencarian Cloud ---")
    ditemukan = False
    if data_produk:
        for id_prod, item in data_produk.items():
            if kata_kunci in item['nama_produk'].lower() or kata_kunci in item['sku'].lower():
                print(f"ID : {id_prod} | SKU : {item['sku']} | Nama : {item['nama_produk']} | Rak : {item['lokasi_rak']} | Stok : {item['stok_aktual']} {item['satuan']}")
                ditemukan = True
    if not ditemukan:
        print("Barang tidak ditemukan di server.")

def stock_opname():
    global USER_AKTIF
    data_produk = requests.get(f"{URL_FIREBASE}produk.json").json()
    print("\n=== FORM STOCK OPNAME ONLINE (PENYESUAIAN STOK) ===")
    id_input = input("Masukkan ID Produk (Contoh: BRG001): ").strip().upper()
    
    if id_input in data_produk:
        try:
            stok_fisik = int(input(f"Masukkan Jumlah Fisik Nyata di Rak untuk {data_produk[id_input]['nama_produk']}: "))
            stok_aplikasi = data_produk[id_input]['stok_aktual']
            selisih = stok_fisik - stok_aplikasi
            
            if selisih == 0:
                print("\n Sukses: Jumlah cocok dan seimbang!"); return
                
            jenis_transaksi = 'MASUK' if selisih > 0 else 'KELUAR'
            waktu_sekarang = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            data_log = {
                "tanggal": waktu_sekarang,
                "sku": data_produk[id_input]['sku'],
                "nama_produk": data_produk[id_input]['nama_produk'],
                "jenis_transaksi": jenis_transaksi,
                "jumlah": abs(selisih),
                "keterangan": f"OPNAME ({'SURPLUS' if selisih > 0 else 'DEFISIT'})",
                "diinput_oleh": USER_AKTIF
            }
            requests.post(f"{URL_FIREBASE}transaksi_stok.json", json=data_log)
            requests.patch(f"{URL_FIREBASE}produk/{id_input}.json", json={"stok_aktual": stok_fisik})
            print(f" Sukses: Stock Opname cloud berhasil dicatat oleh {USER_AKTIF}!")
        except ValueError:
            print("[!] Input angka tidak valid.")
    else:
        print("[!] ID Produk tidak ditemukan.")

# ====================================================================
# [FITUR BARU] MODUL MANAJEMEN KATALOG BARANG (ADD / DELETE)
# ====================================================================
def menu_manajemen_katalog():
    """Menu khusus OWNER untuk menambah varian barang baru atau menghapus produk dari Firebase"""
    while True:
        print("\n=================================")
        print("    MANAJEMEN KATALOG BARANG     ")
        print("=================================")
        print("1. Tambah Produk Baru ke Katalog")
        print("2. Hapus Produk dari Katalog")
        print("0. Kembali ke Menu Utama")
        print("---------------------------------")
        sub_pilihan = input("Pilih menu (0-2): ").strip()
        
        if sub_pilihan == '1':
            print("\n--- TAMBAH KATALOG PRODUK BARU ---")
            id_baru = input("Masukkan ID Produk Baru (Contoh: BRG003): ").strip().upper()
            
            # Validasi apakah ID sudah terpakai di cloud
            exist = requests.get(f"{URL_FIREBASE}produk/{id_baru}.json").json()
            if exist:
                print(f"[!] Gagal: ID '{id_baru}' sudah digunakan oleh produk '{exist['nama_produk']}'!")
                continue
                
            sku = input("Masukkan Kode SKU: ").strip().upper()
            nama = input("Masukkan Nama Produk: ").strip()
            rak = input("Masukkan Lokasi Rak (Contoh: C3): ").strip().upper()
            try:
                stok_awal = int(input("Masukkan Angka Stok Awal Fisik: "))
                stok_min = int(input("Masukkan Batas Stok Minimum: "))
            except ValueError:
                print("[!] Gagal: Input stok harus berupa angka!"); continue
                
            satuan = input("Masukkan Satuan Barang (Contoh: Pcs/Kg): ").strip()
            
            # Siapkan paket data JSON
            data_produk_baru = {
                "sku": sku,
                "nama_produk": nama,
                "lokasi_rak": rak,
                "stok_aktual": stok_awal,
                "stok_minimum": stok_min,
                "satuan": satuan
            }
            
            # Kirim data ke Firebase menggunakan metode PUT
            requests.put(f"{URL_FIREBASE}produk/{id_baru}.json", json=data_produk_baru)
            print(f" Sukses: Produk baru '{nama}' [{id_baru}] berhasil didaftarkan ke Database Online!")
            
        elif sub_pilihan == '2':
            print("\n--- HAPUS PRODUK DARI KATALOG CLOUD ---")
            lihat_stok()
            id_hapus = input("\nMasukkan ID Produk yang ingin DIHAPUS PERMANEN: ").strip().upper()
            
            # Cek ketersediaan produk di internet
            exist = requests.get(f"{URL_FIREBASE}produk/{id_hapus}.json").json()
            if not exist:
                print("[!] Gagal: ID Produk tidak ditemukan.")
            else:
                print(f"\n[⚠️ PERINGATAN ] Anda akan menghapus data '{exist['nama_produk']}' secara permanen dari Cloud server.")
                konfirmasi = input(f"Apakah Anda yakin? Ketik 'YAKIN' untuk melanjutkan: ").strip()
                if konfirmasi == 'YAKIN':
                    # Jalankan penghapusan data di cloud via HTTP DELETE
                    requests.delete(f"{URL_FIREBASE}produk/{id_hapus}.json")
                    print(f" Sukses: Produk '{exist['nama_produk']}' telah dihapus dari sistem.")
                else:
                    print("[-] Penghapusan dibatalkan.")
                    
        elif sub_pilihan == '0':
            break
        else:
            print("[!] Pilihan tidak valid.")

def dasbor_analisis():
    data_produk = requests.get(f"{URL_FIREBASE}produk.json").json()
    print("\n=======================================================")
    print("         DASBOR ANALISIS & STATISTIK CLOUD             ")
    print("=======================================================")
    
    total_produk = 0
    total_stok = 0
    total_kritis = 0
    
    if data_produk:
        total_produk = len(data_produk)
        for item in data_produk.values():
            total_stok += item['stok_aktual']
            if item['stok_aktual'] <= item['stok_minimum']:
                total_kritis += 1
                
    print(f" Total Variasi Produk (Katalog) : {total_produk} Jenis Barang")
    print(f" Total Fisik Barang di Gudang   : {total_stok} Unit")
    print(f" Jumlah Produk Stok Kritis      : {total_kritis} Produk")
    print("=======================================================")

def ekspor_ke_csv():
    print("\n=== PROSES EKSPOR CLOUD DATABASE KE CSV LOKAL ===")
    data_produk = requests.get(f"{URL_FIREBASE}produk.json").json()
    data_mutasi = requests.get(f"{URL_FIREBASE}transaksi_stok.json").json()
    
    folder_tujuan = "/sdcard/Download"
    if not os.path.exists(folder_tujuan): folder_tujuan = "."
        
    path_stok = os.path.join(folder_tujuan, 'laporan_stok_cloud.csv')
    path_mutasi = os.path.join(folder_tujuan, 'laporan_mutasi_cloud.csv')
    
    try:
        if data_produk:
            with open(path_stok, mode='w', newline='', encoding='utf-8') as f_stok:
                writer = csv.writer(f_stok)
                writer.writerow(['ID', 'SKU', 'Nama Produk', 'Lokasi Rak', 'Stok Aktual', 'Stok Minimum', 'Satuan', 'Status'])
                for i, item in data_produk.items():
                    status = "KRITIS" if item['stok_aktual'] <= item['stok_minimum'] else "AMAN"
                    writer.writerow([i, item['sku'], item['nama_produk'], item['lokasi_rak'], item['stok_aktual'], item['stok_minimum'], item['satuan'], status])
                    
        if data_mutasi:
            with open(path_mutasi, mode='w', newline='', encoding='utf-8') as f_mutasi:
                writer = csv.writer(f_mutasi)
                writer.writerow(['Tanggal & Waktu', 'SKU', 'Nama Produk', 'Jenis Transaksi', 'Jumlah', 'Keterangan', 'Petugas Admin'])
                for r in data_mutasi.values():
                    writer.writerow([r['tanggal'], r['sku'], r['nama_produk'], r['jenis_transaksi'], r['jumlah'], r['keterangan'], r['diinput_oleh']])
                    
        print(f"\n Sukses: Seluruh data cloud berhasil diunduh ke folder **{folder_tujuan}**!")
    except Exception as e:
        print(f"[!] Gagal mengekspor data: {e}")

# ====================================================================
# 5. MENU INTERFACES / MAIN DRIVER
# ====================================================================
def main_menu():
    global USER_AKTIF, ROLE_AKTIF
    while True:
        print(f"\n=================================")
        print(f"    ERP GUDANG ONLINE CLOUD - V2 ")
        print(f"    User: {USER_AKTIF} ({ROLE_AKTIF}) ")
        print("=================================")
        print("1. Lihat Laporan Stok Saat Ini")
        print("2. Catat Barang Masuk (Inbound)")
        print("3. Catat Barang Keluar (Outbound)")
        print("4. Lihat Mutasi Barang (Riwayat)")
        print("5. Cari Informasi Barang Cepat")
        print("6. Manajemen Katalog Barang (Owner Only) <-- [BARU]")
        print("7. Jalankan Stock Opname (Owner Only)")
        print("8. Lihat Dasbor Analisis Bisnis (Owner Only)")
        print("9. Ekspor Laporan ke Excel/CSV (Owner Only)")
        print("10. Manajemen Karyawan/User (Owner Only)")
        print("0. Keluar Aplikasi (Logout)")
        print("---------------------------------")
        
        pilihan = input("Pilih menu (0-10): ").strip()
        
        # Proteksi hak akses OWNER untuk menu 6 sampai 10
        if pilihan in ['6', '7', '8', '9', '10'] and ROLE_AKTIF != 'OWNER':
            print(f"\n[⚠️ DITOLAK ] Menu rahasia, hanya untuk akun berstatus OWNER!")
            continue
            
        if pilihan == '1': lihat_stok()
        elif pilihan == '2': transaksi_barang('MASUK')
        elif pilihan == '3': transaksi_barang('KELUAR')
        elif pilihan == '4': lihat_mutasi()
        elif pilihan == '5': cari_barang()
        elif pilihan == '6': menu_manajemen_katalog()  # Mengarah ke fungsi baru
        elif pilihan == '7': stock_opname()
        elif pilihan == '8': dasbor_analisis()
        elif pilihan == '9': ekspor_ke_csv()
        elif pilihan == '10': menu_manajemen_karyawan()
        elif pilihan == '0':
            print(f"\nUser {USER_AKTIF} berhasil logout.")
            break
        else:
            print("\nPilihan tidak valid.")

if __name__ == "__main__":
    inisialisasi_sistem_user()
    if login_sistem():
        main_menu()
