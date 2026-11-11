"""
Arayüz metinleri: (Türkçe, İngilizce).

Şablonda {% ui "anahtar" %} ile kullanılır. Yeni metin eklerken iki dili birlikte yaz.
Uzun içerik (Hakkımda, proje ve blog metinleri) burada değil, şablonlarda ve admin'de.
"""

STRINGS = {
    # Menü
    "nav.home": ("Ana", "Home"),
    "nav.home_long": ("Ana sayfa", "Home"),
    "nav.projects": ("Projeler", "Projects"),
    "nav.blog": ("Blog", "Blog"),
    "nav.about": ("Hakkımda", "About"),
    "nav.contact": ("İletişim", "Contact"),
    "nav.pages": ("Sayfalar", "Pages"),
    "nav.footer": ("Alt menü", "Footer"),
    "lang.switch": ("Dil", "Language"),
    # Genel
    "site.title": ("Emre Özaydın · ozaydin.dev", "Emre Özaydın · ozaydin.dev"),
    "site.description": (
        "Emre Özaydın — bilişim öğrencisi. Django ile web, Unity ile oyun geliştiriyor.",
        "Emre Özaydın — information systems student building web apps with Django and games with Unity.",
    ),
    "clock.city": ("İstanbul", "Istanbul"),
    "clock.label": ("İstanbul saati", "Istanbul time"),
    "copyright": ("© 2026 Emre Özaydın", "© 2026 Emre Özaydın"),
    # Ana sayfa
    "home.eyebrow": ("Bilişim öğrencisi · Doğu Akdeniz Üniversitesi", "IT student · Eastern Mediterranean University"),
    "home.lead": (
        "Sıfırlardan ve birlerden, <b>çalışan sistemlere</b>. Django ile web, Unity ile oyun geliştiriyorum.",
        "From zeros and ones to <b>working systems</b>. I build web apps with Django and games with Unity.",
    ),
    "home.cta_projects": ("Projeleri gör", "See projects"),
    "home.cta_contact": ("İletişime geç", "Get in touch"),
    "home.principle": ("İlke", "Principle"),
    "home.manifesto": (
        "Her şey iki durumla başlar: 0 ve 1. Gerisi, onları doğru sıraya dizmek.",
        "Everything starts with two states: 0 and 1. The rest is putting them in the right order.",
    ),
    "home.projects": ("Projeler", "Projects"),
    "home.see_all": ("Tümünü gör", "See all"),
    "home.writing": ("Yazılar", "Writing"),
    "home.all_posts": ("Tüm yazılar", "All posts"),
    "home.what": ("Ne yapıyorum", "What I do"),
    "cap.backend": ("Backend", "Backend"),
    "cap.backend_p": (
        "Veri modelinden login sistemine kadar bir web uygulamasının backend'ini kurarım.",
        "I build the backend of a web app, from the data model to the login system.",
    ),
    "cap.game": ("Game development", "Game development"),
    "cap.game_p": (
        "Kuralları olan, oyuncuyu karar vermeye zorlayan oyunlar tasarlar ve kodlarım.",
        "I design and code games with clear rules that make the player decide.",
    ),
    "cap.frontend": ("Frontend", "Frontend"),
    "cap.frontend_p": (
        "Tasarımları her ekrana uyan responsive sayfalara çeviririm.",
        "I turn designs into responsive pages that fit every screen.",
    ),
    "cap.video": ("Video ve motion graphics", "Video and motion graphics"),
    "cap.video_p": (
        "Kurgu ve motion graphics ile bir projeyi anlatılır hâle getiririm.",
        "I use editing and motion graphics to make a project easy to explain.",
    ),
    "home.closing": ("Birlikte bir şey kuralım.", "Let's build something together."),
    # Projeler
    "projects.title": ("Projeler", "Projects"),
    "projects.count": ("{n} proje", "{n} projects"),
    "projects.filter": ("Alana göre filtrele", "Filter by area"),
    "projects.mask": ("Maske", "Mask"),
    "projects.empty": ("Bu maskeye uyan proje yok.", "No project matches this mask."),
    "projects.none": ("Henüz proje eklenmedi.", "No projects yet."),
    "project.back": ("Projeler", "Projects"),
    "project.year": ("Yıl", "Year"),
    "project.role": ("Rol", "Role"),
    "project.duration": ("Süre", "Duration"),
    "project.stack": ("Araçlar", "Tools"),
    "project.code": ("Kod", "Code"),
    "project.live": ("Canlı", "Live"),
    "project.problem": ("Sorun", "Problem"),
    "project.did": ("Ne yaptım", "What I did"),
    "project.flow": ("Akış", "Flow"),
    "project.result": ("Sonuç", "Result"),
    "project.gallery": ("Görseller", "Gallery"),
    "project.next": ("Sıradaki proje", "Next project"),
    "project.tape": ("UTF-8 · {n} bayt · her sütun bir bayt", "UTF-8 · {n} bytes · one column per byte"),
    "gallery.close": ("Kapat", "Close"),
    "gallery.prev": ("Önceki", "Previous"),
    "gallery.next": ("Sonraki", "Next"),
    "gallery.open": ("Büyüt", "Enlarge"),
    # İletişim
    "contact.title": ("İletişim", "Contact"),
    "contact.state": ("Bağlantı", "Link"),
    "contact.lead": (
        "Uzun dönem staj, proje ya da sadece bir merhaba. Genelde <b>bir gün içinde</b> dönerim.",
        "Long-term internship, a project or just a hello. I usually reply <b>within a day</b>.",
    ),
    "contact.copy": ("Adresi kopyala", "Copy address"),
    "contact.copied": ("Kopyalandı", "Copied"),
    "contact.selected": ("Seçildi, Ctrl+C", "Selected, Ctrl+C"),
    "contact.name": ("Adın", "Your name"),
    "contact.email": ("E-posta adresin", "Your email"),
    "contact.message": ("Mesajın", "Your message"),
    "contact.send": ("Gönder", "Send"),
    "contact.sending": ("Gönderiliyor…", "Sending…"),
    "contact.note": ("Mesajın doğrudan bana ulaşır.", "Your message comes straight to me."),
    "contact.profiles": ("Profiller", "Profiles"),
    "contact.hp": ("Bu alanı boş bırak", "Leave this field empty"),
    # Hakkımda
    "about.title": ("Hakkımda", "About"),
    "about.eyebrow": ("Bilişim öğrencisi · Türkiye", "IT student · Türkiye"),
    # Blog
    "blog.title": ("Blog", "Blog"),
    # 404
    "404.title": ("Bu adreste bir şey yok", "Nothing at this address"),
    "404.lead": ("Aradığın sayfa taşınmış ya da hiç var olmamış olabilir.", "The page may have moved or never existed."),
    "404.home": ("Ana sayfaya dön", "Back to home"),
}
