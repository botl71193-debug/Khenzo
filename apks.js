// Data Array APK Terupdate - Disimpan terpisah agar mudah diedit
const apks = [
  {
    name: "Minecraft Patch",
    version: "V1.26.23.1",
    category: "Game",
    size: "156 MB",
    android: "Android 5.0+",
    imageUrl: "https://i.ibb.co.com/gZFKwDMd/Minecraft-Bedrock-icon.webp",
    multiDownload: true,
    links: {
      Arm64: "https://www.mediafire.com/file/tlupd5quvwwccdh/1.26.23.Arm64.Capes_Patch.apk/file",
      Arm32: "https://www.mediafire.com/file/h2hy1mqyd0q7de2/12623_Arm32_Patch_Capes.apk/file"
    },
    description: "Sandbox game legendaris versi modifikasi patch jubah (capes unlocked) dengan optimalisasi performa rendering."
  },
  {
    name: "My Supermarket Simulator 3D",
    version: "v1.32.2",
    category: "Game",
    size: "236 MB",
    android: "Android 5.0+",
    imageUrl: "https://i.ibb.co.com/LzZvvrsG/Supermarket-Simulator.webp",
    downloadUrl: "https://safefileku.com/download/0YMvTe9iFaam2Y5c",
    description: "Game simulator supermarket 3D premium unlocked. Kelola toko, stok barang, layani pelanggan, dan kembangkan bisnis supermarketmu tanpa iklan."
  },
  {
    name: "Lane",
    version: "v 1.4",
    category: "Music",
    size: "75 MB",
    android: "Android 6.0+",
    imageUrl: "https://worrying-apricot-utxtj0qs.edgeone.app/lane.png",
    downloadUrl: "https://safefileku.com/download/3sA8xBwdh6oTQ6ZB",
    description: "Aplikasi alternatif pemutar musik Spotify dengan fitur Premium terbuka."
  },
  {
    name: "BeautyPlus",
    version: "V 7.38.1",
    category: "Foto & Video",
    size: "371 MB",
    android: "Android 6.0+",
    imageUrl: "https://i.supaimg.com/1ac260ce-b26f-4f02-a315-4072e31459d4/1f57c4f2-fca5-4414-9788-e3824fa18c2e.png",
    downloadUrl: "https://safefileku.com/download/HO7fPpKhQVw9YmMk",
    description: "Editor foto & video AI dengan fitur premium unlocked, autopilot beauty, dan stiker eksklusif tanpa iklan."
  },
  {
    name: "Cineflow",
    version: "v1.0.2",
    category: "Streaming",
    size: "18 MB",
    android: "Android 5.0+",
    imageUrl: "https://worrying-apricot-utxtj0qs.edgeone.app/cineflow.png",
    downloadUrl: "https://link.adsafelink.com/Q2CBs7SX",
    description: "Streaming film & series premium unlocked tanpa iklan dengan kualitas full HD."
  },
  {
    name: "Bus Simulator",
    version: "V 4.5",
    category: "Game",
    size: "1 GB",
    android: "Android 5.0+",
    imageUrl: "https://i.ibb.co.com/CsKKbjQS/Bussid.webp",
    downloadUrl: "https://www.mediafire.com/file/9gz1qrpal55px45/Busid+Mod+Apk+V4.5+Terbaru+2026.zip/file",
    description: "Game simulasi mengendarai bus dengan peta dan rute realistis, kustomisasi kendaraan, dan mode karier."
  },
  {
    name: "Frag Pro Shooter",
    version: "V 5.1.0",
    category: "Game",
    size: "200 MB",
    android: "Android 5.0+",
    imageUrl: "https://i.ibb.co.com/MkJ1SxSZ/Frag-Pro.webp",
    downloadUrl: "https://www.mediafire.com/file/fcikalep5413ca3/Frag_Pro_Shooter_v5.1.0_Menu.apk/file",
    description: "Shooter multiplayer cepat dengan karakter unik, kemampuan khusus, dan pertarungan tim 4v4."
  },
  {
    name: "Beach Buggy Racing 2",
    version: "V 2026.05.21",
    category: "Game",
    size: "200 MB",
    android: "Android 5.0+",
    imageUrl: "https://coastal-beige-xshefioh.edgeone.app/BeachBuggy.png",
    downloadUrl: "https://www.mediafire.com/file/qv6hjfup8z0nky0/(NO+PW)BB+Racing+2+Mod+Menu+v2026.05.21+Support+All+Fix+v3.zip/file",
    description: "Game balapan kart arcade dengan power-up gila, trek beragam, dan mode multiplayer."
  },
  {
    name: "CloneApp",
    version: "v3.2.1",
    category: "Tools",
    size: "8 MB",
    android: "Android 6.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/CloneApp.png",
    downloadUrl: "https://link.adsafelink.com/8DyG5TiH",
    description: "Kloning aplikasi tanpa batas, support vip feature bypass device-id."
  },
  {
    name: "Dark Aura",
    version: "v2.0.0",
    category: "Entertainment",
    size: "12 MB",
    android: "Android 7.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/DarkAura.png",
    downloadUrl: "https://link.adsafelink.com/SYnCOLUp",
    description: "Kustomisasi tema super dark AMOLED dengan paket ikon premium aesthetic."
  },
  {
    name: "DramaNova",
    version: "v1.1.5",
    category: "Streaming",
    size: "22 MB",
    android: "Android 5.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/DramaNova.png",
    downloadUrl: "https://link.adsafelink.com/NCeRmOa",
    description: "Nonton drama Asia terlengkap, VIP server cepat unlocked tanpa login."
  },
  {
    name: "DramaQueen",
    version: "v1.0.9",
    category: "Streaming",
    size: "19 MB",
    android: "Android 5.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/dramaqueen.png",
    downloadUrl: "https://link.adsafelink.com/es5iMSo",
    description: "Akses eksklusif koleksi drakor premium dan variety show sub Indo ad-free."
  },
  {
    name: "Dramora",
    version: "v2.1.0",
    category: "Streaming",
    size: "25 MB",
    android: "Android 5.5+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/Dramora.png",
    downloadUrl: "https://link.adsafelink.com/Pr9aGT",
    description: "Platform streaming drama terlengkap dengan fitur download offline sepuasnya."
  },
  {
    name: "Floatee",
    version: "v4.0",
    category: "Tools",
    size: "5 MB",
    android: "Android 6.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/floatee.png",
    downloadUrl: "https://link.adsafelink.com/7WhOymr",
    description: "Aplikasi widget melayang (floating shortcut) untuk multitasking pro unlocked."
  },
  {
    name: "Instagram Pro",
    version: "v311.0",
    category: "Tools",
    size: "64 MB",
    android: "Android 6.0+",
    imageUrl: "https://worrying-apricot-utxtj0qs.edgeone.app/igmod.png",
    downloadUrl: "https://link.adsafelink.com/d6hmwu1",
    description: "Download foto, video, story sekali klik, anti-view tersembunyi, feed ad-free."
  },
  {
    name: "KomikBahagia",
    version: "v1.0",
    category: "Entertainment",
    size: "12 MB",
    android: "Android 5.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/comikbahagia.png",
    downloadUrl: "#",
    description: "Baca ratusan manga, manhua, dan manhwa favorit tanpa koin/ad-free."
  },
  {
    name: "KucingPremium",
    version: "v1.8.2",
    category: "Entertainment",
    size: "15 MB",
    android: "Android 5.0+",
    imageUrl: "https://worrying-apricot-utxtj0qs.edgeone.app/images.png",
    downloadUrl: "https://link.adsafelink.com/neE91I9d",
    description: "Aplikasi hiburan dan streaming film/anime premium mod terlengkap."
  },
  {
    name: "Melolo",
    version: "v1.2.0",
    category: "Entertainment",
    size: "21 MB",
    android: "Android 5.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/floatee.png",
    downloadUrl: "https://link.adsafelink.com/9oNC5wAu",
    description: "Aplikasi streaming hiburan musik dan video pendek seru premium mod."
  },
  {
    name: "Music Downloader",
    version: "v4.5",
    category: "Tools",
    size: "11 MB",
    android: "Android 5.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/MusicDownloader.png",
    downloadUrl: "https://link.adsafelink.com/KXD6B",
    description: "Download musik MP3 resolusi tinggi langsung dari berbagai platform musik."
  },
  {
    name: "RCTI+",
    version: "v3.1.2",
    category: "Streaming",
    size: "26 MB",
    android: "Android 5.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/rcti.png",
    downloadUrl: "#",
    description: "Nonton siaran langsung TV nasional tanpa buffer dan tanpa gangguan iklan."
  },
  {
    name: "Remini",
    version: "v3.7.83",
    category: "Foto & Video",
    size: "54 MB",
    android: "Android 6.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/remini.png",
    downloadUrl: "https://link.adsafelink.com/78c34m3",
    description: "Penjernih foto AI pro unlocked, kuota edit tanpa batas, kualitas ultra HD."
  },
  {
    name: "TeraBox",
    version: "v3.24.1",
    category: "Tools",
    size: "68 MB",
    android: "Android 6.0+",
    imageUrl: "https://worrying-apricot-utxtj0qs.edgeone.app/tera.png",
    downloadUrl: "https://link.adsafelink.com/g5mo8dv",
    description: "Penyimpanan cloud raksasa dengan fitur download kecepatan tinggi VIP unlocked."
  },
  {
    name: "WPS Office",
    version: "v18.7.1",
    category: "Tools",
    size: "62 MB",
    android: "Android 7.0+",
    imageUrl: "https://worrying-apricot-utxtj0qs.edgeone.app/wps.png",
    downloadUrl: "https://link.adsafelink.com/aBAHAU4J",
    description: "Buka dan edit semua dokumen PDF ke Word, edit ppt premium unlocked gratis."
  },
  {
    name: "Xeno",
    version: "v1.0.5",
    category: "Tools",
    size: "14 MB",
    android: "Android 6.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/Xeno.png",
    downloadUrl: "https://link.adsafelink.com/9Iww9zQd",
    description: "Browser keamanan enkripsi tinggi lengkap dengan VPN internal bypass internet positif."
  },
  {
    name: "XGames",
    version: "v2.0",
    category: "Game",
    size: "45 MB",
    android: "Android 5.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/xgame.png",
    multiDownload: true,
    links: {
      PSP: "https://link.adsafelink.com/wFQ5ZE",
      PS2: "https://link.adsafelink.com/1L8k",
      PS3: "https://link.adsafelink.com/KwC4WD13",
      GameBoy: "https://link.adsafelink.com/2yPweIK3"
    },
    description: "Pusat download game emulator terlengkap dengan script bawaan berbagai konsol."
  },
  {
    name: "Youshort",
    version: "v1.0.1",
    category: "Entertainment",
    size: "16 MB",
    android: "Android 5.0+",
    imageUrl: "https://clever-aquamarine-zdzgpsly.edgeone.app/youshort.png",
    downloadUrl: "https://link.adsafelink.com/1ZOUs",
    description: "Nonton berbagai video pendek premium dan drama singkat menarik unlocked tanpa batas."
  }
];