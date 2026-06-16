// DATABASE INTERNAL KHUSUS AKSES EXECUTIVE (VIP)
const execAppsDatabase = {
    npManager: {
        name: "NP Manager",
        version: "v3.1.2",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png", // Ganti dengan URL gambar asli
        downloadUrl: "https://download.link/npmanager",
        size: "18 MB",
        android: "5.0+",
        category: "Modder Tools app",
        features: [
            "Advanced APK/APKS/XAPK compilation & decompilation.",
            "Sign APK dengan skema V1, V2, V3, dan V4 terlengkap.",
            "Ekstraksi Dex ke Jar, Deobfuscation String, dan analisis file manifesto.",
            "Bypass pengamanan signature dasar langsung via ponsel Android."
        ]
    },
    mtManager: {
        name: "MT Manager",
        version: "v2.16.0",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png", // Ganti dengan URL gambar asli
        downloadUrl: "https://download.link/mtmanager",
        size: "22 MB",
        android: "6.0+",
        category: "Modder Tools app",
        features: [
            "Dual-panel file management yang dirancang khusus untuk reverse engineering.",
            "Dex Editor Plus terintegrasi untuk modifikasi source code secara masif.",
            "Fitur ARSC editor lengkap untuk menerjemahkan bahasa atau memanipulasi aset.",
            "XML Text & Layout Editor pro disertai validasi sintaks otomatis."
        ]
    },
    toolM: {
        name: "Tool M Terminal",
        version: "v1.0.4",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/toolm",
        size: "5 MB",
        android: "7.0+",
        category: "Modder Tools app",
        features: [
            "Android subsystem emulator terminal yang dioptimalkan untuk memproses script berat.",
            "Akses cepat ke perintah root tanpa pengetikan manual.",
            "Modul otomatis pengecekan status arsitektur perangkat (ARM64/X86)."
        ]
    },
    luckyPatcher: {
        name: "Lucky Patcher Proxy",
        version: "v11.4.2",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/luckypatcher",
        size: "10 MB",
        android: "4.4+",
        category: "Modder Tools app",
        features: [
            "Emulasi Server Lisensi Google Play bawaan untuk bypass verifikasi secara real-time.",
            "Sistem otomatis penghapus Google Ads (Iklan) pada level kode biner.",
            "Alat bantu injeksi Custom Patch langsung ke direktori aplikasi data internal."
        ]
    },
    modderhub: {
        name: "Modderhub Repo",
        version: "v4.0",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/modderhub",
        size: "12 MB",
        android: "5.0+",
        category: "Modder Tools app",
        features: [
            "Akses langsung ke server repositori berkas biner mentah modifikasi dunia.",
            "Unduh smali template siap pakai untuk berbagai macam bypass sistem keamanan.",
            "Forum pertukaran payload privat sesama pengembang terverifikasi."
        ]
    },
    hermesPatcher: {
        name: "Hermes Patcher Script",
        version: "v2.1",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/hermes",
        size: "2 MB",
        android: "Termux OS",
        category: "Scrip termux",
        features: [
            "Script otomatisasi patching enkripsi string internal berbasis mesin Hermes.",
            "Membongkar proteksi obfuscation kode dengan satu baris perintah eksekusi."
        ]
    },
    flutterPatcher: {
        name: "Flutter Patcher",
        version: "v1.5",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/flutter",
        size: "4 MB",
        android: "Termux OS",
        category: "Scrip termux",
        features: [
            "Scanning otomatis file libflutter.so untuk mendeteksi struktur fungsi aplikasi.",
            "Bypass SSL Pinning secara instan pada aplikasi berbasis framework Flutter.",
            "Modifikasi logika boolean pengembalian nilai VIP/Premium."
        ]
    },
    ultimateFlutter: {
        name: "Ultimate Flutter Pro",
        version: "v3.0.0",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/ultimate",
        size: "7 MB",
        android: "Termux OS",
        category: "Scrip termux",
        features: [
            "Evolusi script Flutter patcher dengan penambahan algoritma pencarian biner canggih.",
            "Melakukan dump memory secara dinamis ketika aplikasi target sedang dijalankan."
        ]
    },
    blutter: {
        name: "Blutter Dump",
        version: "v1.1",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/blutter",
        size: "3 MB",
        android: "Python 3",
        category: "Scrip termux",
        features: [
            "Menghasilkan pemetaan memori offsets yang presisi untuk di-edit lewat MT Manager.",
            "Terintegrasi dengan compiler Python eksternal untuk pemrosesan super cepat."
        ]
    },
    beautyPlus: {
        name: "BeautyPlus Automation",
        version: "v7.6",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/beautyplus",
        size: "62 MB",
        android: "7.0+",
        category: "Instant Premium",
        features: [
            "Sistem otomatisasi aktivasi lisensi server lokal tanpa akun asli.",
            "Membuka semua filter kosmetik, resolusi ekspor HD Ultra, dan tool AI pengedit wajah."
        ]
    },
    regexVip: {
        name: "Unlock VIP | Regex 1-5",
        version: "v5.2",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/regexvip",
        size: "100 KB",
        android: "All",
        category: "Regex Generator",
        features: [
            "Pola Regex pencarian cepat logika boolean: const/4 v0, 0x1 untuk disuntikkan ke metode cek status premium.",
            "Bypass pembatasan premium berulang menggunakan pencarian metode pengembalian nilai bernilai True."
        ]
    },
    regexAds: {
        name: "Ads Blocker Regex 1",
        version: "v1.0",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/regexads",
        size: "50 KB",
        android: "All",
        category: "Regex Generator",
        features: [
            "Regex pembersih deklarasi iklan: menghapus jalur com/google/android/gms/ads dari file arsc/smali.",
            "Menonaktifkan siklus inisialisasi iklan (ad life cycle)."
        ]
    },
    regexLicense: {
        name: "License Bypass Regex 1",
        version: "v1.0",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/regexlicense",
        size: "80 KB",
        android: "All",
        category: "Regex Generator",
        features: [
            "Formula regex khusus untuk melompati fungsi checkLicense() atau isLicensed() secara universal.",
            "Memaksa alur eksekusi kode biner langsung menuju menu utama aplikasi tanpa verifikasi market."
        ]
    },
    regexFb: {
        name: "Bypass Sign FB Regex 1-2",
        version: "v2.0",
        imageUrl: "https://diverse-aqua-iq7wghij.edgeone.app/M.png",
        downloadUrl: "https://download.link/regexfb",
        size: "90 KB",
        android: "All",
        category: "Regex Generator",
        features: [
            "Pola regex untuk memperbaiki kesalahan login Facebook SDK pada aplikasi hasil modifikasi.",
            "Memotong verifikasi hash tanda tangan (signature hash validation)."
        ]
    }
};