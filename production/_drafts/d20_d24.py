"""Draf storyboard D20–D24."""

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
        "id": "BOCA-D20", "day": 20, "duration": 45,
        "title": "Kenapa es bisa mengapung di air?",
        "logline": "Pak Darno heran es batu ngambang di atas air. Boca menjelaskan rongga udara kecil yang membuat es lebih ringan.",
        "guest": "pak_darno",
        "hook": ("H3", "Air yang dibekukan ternyata lebih ringan dari air biasa.",
                 "Bukannya padat harus lebih berat dari cair?", "Ada rongga kecil berisi udara di dalamnya."),
        "analogy": {
            "source": "penonton yang berdiri berjarak di lapangan yang sama",
            "maps": [("molekul air tersusun berjarak saat membeku", "penonton berdiri berjarak di lapangan"),
                     ("es memakai ruang lebih besar untuk berat yang sama", "jumlah orang sama tapi area yang dipakai lebih luas")],
            "line_shot": 4,
            "why_it_works": "Semua orang pernah melihat kerumunan: jumlahnya sama, tapi area yang dipakai bisa jauh berbeda.",
        },
        "shots": [
            {"scene": "lake_ice", "beat": "hook", "cam": C_OPEN, "keys": KWALK,
             "guest": GSTAND, "sfx": [(0.05, "whoosh", 0.8)],
             "lines": [("pak_darno", "Boca, es batu bisa ngambang di atas air. Kenapa bisa, ya?", "es batu ngambang di atas air", "pertanyaan klasik"),
                       ("boca", "Kalau batu biasa, kan langsung tenggelam. Es ini kelihatan ngambang aja.", "batu biasa tenggelam, es ngambang", "kontras batu dan es")]},
            {"scene": "kitchen", "beat": "setup", "cam": C_PUSH, "keys": KSTAND, "lumi": LUMIF,
             "guest": GSTAND,
             "lines": [("boca", "Coba lihat es di secangkir minum. Esnya ngambang di atas, kan?", "es di secangkir ngambang", "pengamatan sehari-hari"),
                       ("pak_darno", "Iya, ngambang. Airnya yang naik atau esnya yang lebih ringan?", "airnya naik atau esnya ringan", "dua hipotesis")]},
            {"scene": "city_street", "beat": "explain", "cam": C_SIDE, "keys": KEXPL,
             "lines": [("boca", "Esnya yang lebih ringan dari air, makanya bisa ngambang.", "es lebih ringan dari air", "prinsip mengapung"),
                       ("boca", "Wujud padat bukan berarti selalu lebih berat dari cairan.", "padat tidak selalu lebih berat", "koreksi generalisasi")]},
            {"scene": "classroom", "beat": "explain", "cam": C_BACK, "keys": KEXPL,
             "guest": GCONF,
             "lines": [("boca", "Bayangkan penonton yang berdiri berjarak di lapangan yang luas.", "penonton berdiri berjarak", "analogi kerumunan"),
                       ("boca", "Jumlah orangnya sama, tapi areanya jadi jauh lebih luas.", "jumlah sama, area lebih luas", "pemetaan kerapatan")]},
            {"scene": "park_evening", "beat": "twist", "cam": C_SIDE, "keys": KTURN, "lumi": LUMIS,
             "lines": [("boca", "Molekul air juga begitu saat membeku: menyusun diri saling berjarak.", "molekul menyusun diri berjarak", "kisi kristal es"),
                       ("lumi", "Jadi es seperti penonton yang berdiri berjarak, ya?", "es seperti penonton berjarak", "klarifikasi analogi")]},
            {"scene": "classroom", "beat": "payoff", "cam": C_LOW, "keys": KHAPPY,
             "lines": [("boca", "Susunan renggang itu membuat es memakan ruang lebih banyak.", "es memakai ruang lebih banyak", "konsekuensi susunan"),
                       ("boca", "Beratnya sama, tapi ruang yang dipakai lebih banyak, jadi lebih ringan per volume.", "berat sama, ruang lebih besar", "definisi massa jenis")]},
            {"scene": "lake_ice", "beat": "cta", "cam": C_OUT, "keys": KEND, "guest": GWAVE,
             "sfx": [(0.05, "pop", 0.6)],
             "lines": [("boca", "Coba masukkan es di gelas, lalu lihat bagian yang mengapung.", "masukkan es, lihat bagian mengapung", "tindakan praktis"),
                       ("pak_darno", "Rupanya susunan molekulnya yang bikin es jadi lebih ringan.", "susunan molekul bikin ringan", "kesimpulan penonton")]},
        ],
        "notes": "Tamu pak_darno bicara 3 baris. Semua scene sudah ada.",
    },
    {
        "id": "BOCA-D21", "day": 21, "duration": 60,
        "title": "Bagaimana hujan bisa turun dari langit?",
        "logline": "Sari menanyakan asal air hujan. Boca menelusuri siklus air dari laut, uap, awan, sampai turun lagi.",
        "guest": "sari",
        "hook": ("H6", "Sari bertanya: air hujan itu sebenarnya berasal dari mana?",
                 "Kalau awan cuma uap, bagaimana bisa jadi air yang jatuh?",
                 "Kita telusuri siklusnya dari laut sampai tanah."),
        "analogy": {
            "source": "kain basah dijemur di bawah matahari terik",
            "maps": [("matahari menguapkan air dari permukaan laut", "panas menguapkan air dari kain basah"),
                     ("uap naik, mendingin, lalu jadi butir air", "uap naik dan kental jadi embun di sisi kain")],
            "line_shot": 4,
            "why_it_works": "Menjemur pakaian itu pekerjaan rumah tangga yang selalu ada di semua keluarga.",
        },
        "shots": [
            {"scene": "rain_cloud", "beat": "hook", "cam": C_OPEN, "keys": KWALK,
             "guest": GSTAND, "sfx": [(0.05, "whoosh", 0.8)],
             "lines": [("sari", "Boca, air hujan itu sebenarnya berasal dari mana sih?", "air hujan berasal dari mana", "pertanyaan asal"),
                       ("boca", "Dari air yang menguap, tapi perjalanannya jauh lebih panjang.", "dari air yang menguap", "siklus air")]},
            {"scene": "garden", "beat": "setup", "cam": C_PUSH, "keys": KSTAND, "lumi": LUMIF,
             "guest": GSTAND,
             "lines": [("boca", "Matahari menghangatkan permukaan air laut, jadi airnya berubah jadi uap lembap.", "matahari menguapkan air laut", "evaporasi"),
                       ("lumi", "Terus uapnya naik terus sampai ke awan yang tinggi sekali?", "uapnya naik sampai ke awan", "pertanyaan alur")]},
            {"scene": "rain_cloud", "beat": "explain", "cam": C_SIDE, "keys": KEXPL,
             "lines": [("boca", "Naik, lalu mendingin di atas. Uap dingin berubah jadi butir air.", "uap mendingin jadi butir air", "kondensasi"),
                       ("boca", "Ribuan butir air menempel bersama, dan gumpalan itulah yang kita sebut awan.", "ribuan butir membentuk awan", "pembentukan awan")]},
            {"scene": "market", "beat": "explain", "cam": C_BACK, "keys": KEXPL,
             "guest": GCONF,
             "lines": [("boca", "Bayangkan kain basah dijemur di bawah matahari terik di siang hari.", "kain basah dijemur di matahari", "analogi sehari-hari"),
                       ("boca", "Airnya menguap, naik, lalu mengembun lagi di sisi kain.", "uap naik lalu jadi embun", "pemetaan kondensasi")]},
            {"scene": "house_cutaway", "beat": "twist", "cam": C_SIDE, "keys": KTURN, "lumi": LUMIS,
             "lines": [("boca", "Jadi awan bukan kabut tipis, tapi tetesan air yang sangat banyak.", "awan berisi tetesan air banyak", "koreksi salah paham"),
                       ("lumi", "Kalau udaranya lebih dingin, awan lebih cepat jadi hujan?", "udara dingin, awan jadi hujan", "klarifikasi proses")]},
            {"scene": "bedroom_night", "beat": "explain", "cam": C_WIDE, "keys": KEXPL,
             "lines": [("boca", "Kalau suhunya makin dingin, butir air itu saling menempel.", "butir air saling menempel saat dingin", "kondensasi lebih lanjut"),
                       ("lumi", "Jadi butir-butir air itu mulai berat dan akhirnya jatuh?", "butir air berat lalu jatuh", "klarifikasi proses")]},
            {"scene": "beach", "beat": "twist", "cam": C_BACK, "keys": KEXPL,
             "guest": GPOINT,
             "lines": [("boca", "Begitu. Air di awan makin berat, lalu akhirnya jatuh ke bawah tanah.", "air di awan makin berat lalu jatuh", "hujan sebagai fase"),
                       ("sari", "Dan sekali jatuh, dia langsung mengulang siklusnya lagi?", "jatuh lalu mengulang siklus", "siklus berulang")]},
            {"scene": "park_evening", "beat": "payoff", "cam": C_LOW, "keys": KHAPPY,
             "lines": [("boca", "Iya. Namanya siklus air, dan dia berjalan terus sejak dulu.", "namanya siklus air", "istilah siklus air"),
                       ("boca", "Air yang kita minum hari ini mungkin pernah jadi hujan bertahun lalu.", "air minum pernah jadi hujan", "koneksi personal")]},
            {"scene": "rain_cloud", "beat": "cta", "cam": C_OUT, "keys": KEND, "guest": GWAVE,
             "sfx": [(0.05, "chime", 0.7)],
             "lines": [("boca", "Coba lihat jendela yang berkabut pagi hari. Itu uap air yang mengembun.", "jendela berkabut itu uap air", "pengamatan"),
                       ("sari", "Jadi embun itu hujan yang belum cukup berat untuk jatuh ke tanah?", "embun hujan yang belum jatuh", "klarifikasi status")]},
        ],
        "notes": "Tamu sari bicara 3 baris. Semua scene sudah ada.",
    },
    {
        "id": "BOCA-D22", "day": 22, "duration": 60,
        "title": "Kenapa harga barang bisa naik?",
        "logline": "Bu Ratna perplexed harga barang merangkak naik. Boca menjelaskan hubungan antara permintaan, penawaran, dan kemampuan beli.",
        "guest": "bu_ratna",
        "hook": ("H5", "Harga barang naik terus, padahal barangnya sama saja.",
                 "Kalau barang sama, kenapa harganya bisa naik?", "Yang berubah adalah uang di tangan kita."),
        "analogy": {
            "source": "tiket bus yang lebih mahal saat bus penuh",
            "maps": [("harga naik saat banyak orang beli", "tiket lebih mahal saat bus penuh"),
                     ("permintaan naik, barang jadi terbatas", "penumpang banyak, kursi terbatas")],
            "line_shot": 4,
            "why_it_works": "Tiket bus dan kereta yang naik saat ramai adalah pengalaman sehari-hari semua orang.",
        },
        "shots": [
            {"scene": "market", "beat": "hook", "cam": C_OPEN, "keys": KWALK,
             "guest": GSTAND, "sfx": [(0.05, "whoosh", 0.8)],
             "lines": [("bu_ratna", "Boca, harga barang naik terus dari bulan ke bulan. Kenapa bisa?", "harga barang naik terus", "pengamatan pemilik warung"),
                       ("boca", "Barangnya sama saja kok. Yang berubah adalah daya beli kita semua.", "barang sama, uang yang berubah", "koreksi asumsi")]},
            {"scene": "money_print", "beat": "setup", "cam": C_PUSH, "keys": KSTAND, "lumi": LUMIF,
             "guest": GSTAND,
             "lines": [("boca", "Kalau uang yang beredar bertambah banyak, harga barang bisa ikut terdorong naik.", "uang dicetak lebih banyak", "hubungan uang dan permintaan"),
                       ("lumi", "Kalau barangnya terbatas, berarti harganya naik dong, ya?", "barang terbatas berarti harga naik", "hipotesis")]},
            {"scene": "city_street", "beat": "explain", "cam": C_SIDE, "keys": KEXPL,
             "lines": [("boca", "Betul. Ini yang disebut permintaan naik, tapi barangnya tetap terbatas.", "permintaan naik, barang terbatas", "istilah ekonomi"),
                       ("boca", "Jadi banyak orang berebut barang yang sama, dan harganya pun ikut naik.", "banyak orang berebut barang sama", "mekanisme harga")]},
            {"scene": "playground_clock", "beat": "explain", "cam": C_BACK, "keys": KEXPL,
             "guest": GCONF,
             "lines": [("boca", "Bayangkan tiket bus yang lebih mahal kalau busnya penuh.", "tiket bus lebih mahal saat penuh", "analogi"),
                       ("lumi", "Penumpang makin banyak, kursinya tetap, jadi tiketnya jadi mahal.", "penumpang banyak, kursi tetap", "pemetaan analogi")]},
            {"scene": "garden", "beat": "twist", "cam": C_SIDE, "keys": KTURN, "lumi": LUMIS,
             "lines": [("boca", "Jadi harga naik bukan karena penjualnya rakus.", "bukan karena penjual rakus", "koreksi asumsi"),
                       ("boca", "Kadang karena banyak orang butuh hal yang sama pada waktu yang sama.", "banyak orang butuh hal yang sama", "permintaan bersama")]},
            {"scene": "market", "beat": "twist", "cam": C_BACK, "keys": KEXPL,
             "guest": GPOINT,
             "lines": [("bu_ratna", "Jadi kalau barangnya dikit, harganya pasti naik semua, ya?", "barang dikit harga pasti naik", "pertanyaan"),
                       ("lumi", "Dan kalau barangnya banyak, harganya turun lagi, ya?", "barang banyak harga turun", "klarifikasi kebalikan")]},
            {"scene": "kitchen", "beat": "explain", "cam": C_WIDE, "keys": KEXPL,
             "lines": [("boca", "Di dapur, satu kilogram beras pun harganya ikut biaya transportasinya yang panjang.", "harga beras ikut biaya transport", "biaya logistik"),
                       ("lumi", "Jadi ongkos jalan ikut menentukan harga di meja kita semua.", "ongkos jalan menentukan harga", "pemetaan biaya ke harga")]},
            {"scene": "park_sunleft", "beat": "payoff", "cam": C_LOW, "keys": KHAPPY,
             "lines": [("boca", "Iya. Dan harga juga naik karena ongkos angkut dan bahan baku ikut naik.", "ongkos angkut dan bahan baku naik", "biaya produksi"),
                       ("boca", "Jadi harga naik bukan karena satu orang saja.", "bukan karena satu orang saja", "ringkasan multi-faktor")]},
            {"scene": "market", "beat": "cta", "cam": C_OUT, "keys": KEND, "guest": GWAVE,
             "sfx": [(0.05, "pop", 0.6)],
             "lines": [("boca", "Coba perhatikan harga barang yang paling sering kamu beli di warung.", "perhatikan harga barang favorit", "tindakan praktis"),
                       ("bu_ratna", "Beras dan minyak. Dua-duanya naik bulan ini juga, ya?", "beras dan minyak naik", "contoh nyata")]},
        ],
        "notes": "Tamu bu_ratna bicara 3 baris. Semua scene sudah ada.",
    },
]
