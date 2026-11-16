"""Draf storyboard D23–D24."""

KWALK = [(0.0, "neutral", "walk", [0], -300, 1400, 640),
         (1.6, "shock", "stand", [0, 3], 250, 1400, 660, {"period": 0.8}),
         (3.4, "neutral", "point", [2], 255, 1400, 662)]
KSTAND = [(0.0, "neutral", "stand", [0], 250, 1400, 650),
          (2.0, "focus", "point", [2], 255, 1400, 655),
          (4.2, "neutral", "stand", [1, 3], 252, 1400, 652, {"period": 0.85})]
KEXPL = [(0.0, "focus", "stand", [1], 250, 1400, 650),
         (2.2, "focus", "point", [3], 255, 1400, 655),
         (4.4, "happy", "stand", [1, 3], 252, 1400, 652, {"period": 0.8})]
KHAPPY = [(0.0, "happy", "stand", [0], 250, 1400, 655),
          (2.6, "happy", "point", [2], 255, 1400, 660),
          (4.8, "neutral", "stand", [1, 3], 252, 1400, 658, {"period": 0.85})]
KTURN = [(0.0, "neutral", "stand", [0], 250, 1400, 650),
         (2.4, "shock", "stand", [0, 3], 255, 1400, 655, {"period": 0.8}),
         (4.6, "happy", "point", [2], 252, 1400, 652)]
KEND = [(0.0, "happy", "stand", [0], 250, 1400, 655),
        (2.0, "happy", "wave", [3], 252, 1400, 660)]

GSTAND = [(0.0, "neutral", "stand", 780, 1420, 615), (2.0, "happy", "stand", 776, 1420, 617)]
GPOINT = [(0.0, "shock", "stand", 780, 1420, 615), (2.4, "happy", "point", 776, 1420, 617)]
GWAVE = [(0.0, "happy", "stand", 780, 1420, 615), (1.6, "happy", "wave", 776, 1420, 617)]
GCONF = [(0.0, "confused", "stand", 780, 1420, 615), (2.0, "neutral", "stand", 776, 1420, 617)]

LUMIF = [(1.0, "happy", "float", 860, 1080, 234)]
LUMIS = [(1.4, "shock", "float", 880, 1100, 232)]
LUMIW = [(1.0, "happy", "wave", 880, 1050, 240)]

C_OPEN = (0.30, 0.55, 0.40, 0.45, 1.00, 1.10)
C_PUSH = (0.46, 0.50, 0.44, 0.46, 1.00, 1.25)
C_SIDE = (0.32, 0.62, 0.45, 0.45, 1.05, 1.05)
C_BACK = (0.50, 0.46, 0.46, 0.42, 1.30, 1.00)
C_LOW = (0.45, 0.45, 0.62, 0.30, 1.00, 1.06)
C_OUT = (0.55, 0.30, 0.45, 0.45, 1.15, 1.00)
C_WIDE = (0.30, 0.70, 0.35, 0.60, 1.00, 1.00)

EPISODES = [
    {
        "id": "BOCA-D23", "day": 23, "duration": 90,
        "title": "Kenapa negara bisa punya utang?",
        "logline": "Kak Bima ingin tahu kenapa negara boleh punya utang. Boca menjelaskan bahwa utang adalah cara negara mendanai pembangunan yang belum bisa dibayar sekaligus.",
        "guest": "kak_bima",
        "hook": ("H2", "Negara punya utang, padahal uang itu milik rakyat.",
                 "Bukannya itu harusnya dikembalikan semua?", "Utang justru alat untuk mendanai pembangunan."),
        "analogy": {
            "source": "cicilan rumah yang dibayar dari gaji bulanan",
            "maps": [("pinjaman dipakai untuk membangun yang hasilnya jangka panjang", "cicilan dipakai untuk membangun rumah yang dipakai bertahun-tahun"),
                     ("utang harus dibayar dari penghasilan tahun berikutnya", "cicilan dibayar dari gaji bulan berikutnya")],
            "line_shot": 4,
            "why_it_works": "Pinjaman dan cicilan rumah adalah cara meminjam yang paling sering dipakai orang Indonesia.",
        },
        "shots": [
            {"scene": "bank", "beat": "hook", "cam": C_OPEN, "keys": KWALK,
             "guest": GSTAND, "sfx": [(0.05, "whoosh", 0.8)],
             "lines": [("kak_bima", "Boca, kenapa negara boleh punya utang? Bukannya itu kan uang rakyat semua orang?", "kenapa negara boleh punya utang", "pertanyaan normalisasi"),
                       ("boca", "Iya, uangnya dari rakyat. Tapi uang juga bisa dipinjam buat yang lebih besar.", "uangnya dari rakyat tapi bisa dipinjam", "pengantar jawaban")]},
            {"scene": "stock_board", "beat": "setup", "cam": C_PUSH, "keys": KSTAND, "lumi": LUMIF,
             "guest": GSTAND,
             "lines": [("boca", "Misalnya negara mau membangun jembatan besar, dan uangnya belum cukup banyak lagi.", "mau bangun jembatan, uang belum cukup", "contoh kebutuhan"),
                       ("lumi", "Jadi dia pinjam dulu, lalu bayar cicilannya nanti-nanti dari tahun depan?", "pinjam dulu, bayar cicilan nanti", "alur utang")]},
            {"scene": "money_print", "beat": "explain", "cam": C_SIDE, "keys": KEXPL,
             "lines": [("boca", "Iya. Pinjamannya dipakai buat jalan, jembatan, dan fasilitas yang dipakai umum.", "dipakai buat jalan dan jembatan", "makna pinjaman"),
                       ("lumi", "Jadi orang yang memakai fasilitas itu tiap hari juga ikut menikmatinya?", "pemakai fasilitas ikut menikmatinya", "klarifikasi manfaat")]},
            {"scene": "data_center", "beat": "explain", "cam": C_BACK, "keys": KEXPL,
             "guest": GCONF,
             "lines": [("boca", "Iya. Pinjaman itu berubah jadi aset yang bisa dipakai bertahun-tahun lamanya.", "pinjaman berubah jadi aset", "konversi utang jadi aset"),
                       ("lumi", "Jadi utangnya bukan beban, tapi alat untuk membagi hasil ke banyak orang?", "utang alat membagi hasil", "klarifikasi peran utang")]},
            {"scene": "city_top", "beat": "explain", "cam": C_SIDE, "keys": KEXPL,
             "lines": [("boca", "Betul, tapi hanya kalau dipakai buat hal yang hasilnya jangka panjang.", "hanya buat hasil jangka panjang", "syarat"),
                       ("boca", "Kalau uangnya buat kesalahan, utangnya jadi beban yang menyesal sekali juga.", "kalau salah, utang jadi beban", "risiko akibat salah")]},
            {"scene": "galaxy", "beat": "twist", "cam": C_BACK, "keys": KTURN, "lumi": LUMIS,
             "guest": GPOINT,
             "lines": [("boca", "Dan sama seperti cicilan rumah, utangnya juga harus dibayar setiap tahun.", "utang harus dibayar setiap tahun", "kewajiban pembayaran"),
                       ("lumi", "Jadi negara harus menyisihkan sebagian uangnya untuk membayar utangnya tiap tahun?", "sisihkan uang untuk bayar utang", "klarifikasi beban")]},
            {"scene": "park_evening", "beat": "twist", "cam": C_LOW, "keys": KEXPL,
             "lines": [("boca", "Benar. Negara yang menunda terus-menerus akan menumpuk beban bunga yang berat.", "menunda menumpuk beban bunga", "akibat menunda"),
                       ("lumi", "Jadi semakin lama ditunda, semakin mahal juga semuanya jadi?", "semakin lama ditunda makin mahal", "klarifikasi konsekuensi")]},
            {"scene": "bank", "beat": "payoff", "cam": C_WIDE, "keys": KHAPPY,
             "guest": GCONF,
             "lines": [("boca", "Iya. Utang yang sehat itu yang bisa dilayani dari penghasilan tahun depan.", "utang sehat bisa dilayani tahun depan", "kriteria utang sehat"),
                       ("boca", "Kalau tidak bisa dilayani, negara itu masuk ke jalan yang jauh lebih sulit.", "kalau tidak bisa, jalan lebih sulit", "risiko nyata")]},
            {"scene": "city_top", "beat": "payoff", "cam": C_WIDE, "keys": KHAPPY,
             "lines": [("lumi", "Jadi bukan utang atau tidaknya yang penting, tapi hasilnya dipakai atau tidak?", "hasilnya dipakai atau tidak", "kriteria penentu"),
                       ("boca", "Tepat. Jembatan yang dipakai tiap hari bukti bahwa utangnya berguna buat orang.", "jembatan bukti utang berguna", "bukti lapangan")]},
            {"scene": "beach", "beat": "payoff", "cam": C_OUT, "keys": KHAPPY, "guest": GPOINT,
             "lines": [("boca", "Pokoknya, utang itu alat. Yang menentukan adalah kita pakai untuk apa saja.", "utang alat, menentukan pemakaiannya", "kriteria utama"),
                       ("lumi", "Jadi yang dinilai bukan utangnya, tapi hasilnya buat warga banyak?", "yang dinilai hasilnya buat warga", "klarifikasi penutup")]} ,
            {"scene": "money_print", "beat": "payoff", "cam": C_OUT, "keys": KHAPPY, "guest": GPOINT,
             "lines": [("boca", "Jadi utang itu seperti pinjaman pribadi yang hasilnya jauh lebih besar dari pokoknya.", "utang seperti pinjaman pribadi", "analogi penutup"),
                       ("kak_bima", "Bedanya, kalau pribadi gagal bayar, yang rugi cuma dia sendiri dan keluarga.", "kalau gagal bayar, rugi sendiri", "perbedaan risiko")]},
            {"scene": "house_cutaway", "beat": "cta", "cam": C_OUT, "keys": KEND, "guest": GWAVE,
             "sfx": [(0.05, "chime", 0.7)],
             "lines": [("boca", "Coba lihat jalan, jembatan, atau sekolah yang ada di sekitarmu sekarang.", "lihat jalan jembatan sekolah", "undang penonton"),
                       ("kak_bima", "Yang dipakai setiap hari itu hasil dari uang bersama kita semua, ya?", "yang dipakai tiap hari hasil uang bersama", "kesimpulan penonton")]},
        ],
        "notes": "Tier 90 detik, 11 shot. Tamu kak_bima bicara 3 baris.",
    },
    {
        "id": "BOCA-D24", "day": 24, "duration": 60,
        "title": "Kenapa bank mau meminjamkan uang?",
        "logline": "Kak Bima bertanya kenapa bank mau meminjami uang. Boca menjelaskan bahwa bunga adalah cara bank menukar waktu menjadi keuntungan.",
        "guest": "kak_bima",
        "hook": ("H6", "Kak Bima bertanya: bank itu untung dari mana saat meminjamkan uang?",
                 "Kan uangnya cuma dipinjam, bukan diberikan.",
                 "Ternyata dari waktu, lewat bunga."),
        "analogy": {
            "source": "meminjam payung dari teman saat hujan",
            "maps": [("pinjamannya dipakai dan dikembalikan utuh", "payung dipinjam dan dikembalikan utuh"),
                     ("ada inconvenience yang ditanggung pemberi pinjaman", "ada kesibukan yang ditanggung teman")],
            "line_shot": 4,
            "why_it_works": "Meminjam payung dari teman adalah kejadian yang sangat sering dan mudah diingat.",
        },
        "shots": [
            {"scene": "playground_clock", "beat": "hook", "cam": C_OPEN, "keys": KWALK,
             "guest": GSTAND, "sfx": [(0.05, "whoosh", 0.8)],
             "lines": [("kak_bima", "Boca, bank itu untung dari mana saat meminjamkan uang ke orang?", "bank untung dari mana", "pertanyaan"),
                       ("boca", "Dari waktu. Kamu pinjam sekarang, tapi bayar lagi nanti dengan jumlah lebih banyak.", "dari waktu: bayar nanti lebih banyak", "jawaban inti")]},
            {"scene": "beach", "beat": "setup", "cam": C_PUSH, "keys": KSTAND, "lumi": LUMIF,
             "guest": GSTAND,
             "lines": [("boca", "Bayangkan pinjam payung ke teman, lalu besok dibalas dengan cara yang sama.", "pinjam payung ke teman", "analogi"),
                       ("lumi", "Tadi dia membalas dengan cara yang sama persis sekali, kan?", "dibalas dengan cara yang sama", "klarifikasi analogi")]},
            {"scene": "phone_inside", "beat": "explain", "cam": C_SIDE, "keys": KEXPL,
             "lines": [("boca", "Iya, tapi waktu itu juga punya harga. Lampu yang menyala malam ini butuh listrik.", "waktu juga punya harga", "nilai waktu"),
                       ("lumi", "Jadi memakai sesuatu yang kita dapat di tempat lain juga ada biayanya?", "memakai sesuatu ada biayanya", "klarifikasi biaya")]},
            {"scene": "garden", "beat": "explain", "cam": C_BACK, "keys": KEXPL,
             "guest": GCONF,
             "lines": [("boca", "Jadi bunga itu bayaran atas waktu yang dipinjamkan sekarang juga, kan?", "bunga bayaran atas waktu", "isi bunga"),
                       ("kak_bima", "Dan kalau uangnya dipakai buat usaha, hasilnya bisa jauh lebih besar dari bunganya.", "hasil usaha lebih besar dari bunga", "alasan risiko invest")]},
            {"scene": "bedroom_night", "beat": "twist", "cam": C_SIDE, "keys": KTURN, "lumi": LUMIS,
             "lines": [("boca", "Betul. Dan kenapa bank mau memberi pinjaman? Karena risikonya besar sekali.", "bank memberi pinjaman karena risiko besar", "alasan bank"),
                       ("lumi", "Jadi bunga itu sebenarnya imbalan atas risiko yang diambil?", "bunga sebagai imbalan risiko", "klarifikasi risiko")]},
            {"scene": "playground_clock", "beat": "twist", "cam": C_BACK, "keys": KEXPL,
             "guest": GPOINT,
             "lines": [("boca", "Karena risikonya besar sekali, bank juga butuh tambahan imbalan dari peminjamnya.", "butuh tambahan imbalan", "alasan tambahan"),
                       ("lumi", "Jadi bunga itu bayaran atas waktu sekaligus atas risiko, ya?", "bunga bayaran waktu dan risiko", "rangkuman dua fungsi")]},
            {"scene": "classroom", "beat": "payoff", "cam": C_LOW, "keys": KHAPPY,
             "lines": [("boca", "Iya. Dan karena itu orang tetap meminjam walau bunganya terasa mahal.", "orang tetap meminjam walau mahal", "alasan economics"),
                       ("boca", "Karena satu tahun lebih awal nilainya jauh lebih besar dari biaya bunganya.", "nilai satu tahun lebih besar", "alasan nilai waktu")]},
            {"scene": "classroom", "beat": "cta", "cam": C_OUT, "keys": KEND, "guest": GWAVE,
             "sfx": [(0.05, "pop", 0.6)],
             "lines": [("boca", "Coba hitung bunga pinjamannya, angkanya kecil atau justru besar?", "hitung bunga pinjamannya", "tindakan praktis"),
                       ("kak_bima", "Agak besar juga. Jadi memang ada biaya memakai uang orang lain.", "ada biaya memakai uang orang", "kesimpulan penonton")]},
        ],
        "notes": "Tamu kak_bima bicara 3 baris. Semua scene sudah ada.",
    },
]
