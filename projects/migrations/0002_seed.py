"""İlk içerik: alanlar ve sitedeki iki proje (eski tek sayfalık sürümden taşındı)."""
from django.db import migrations

CATEGORIES = [("oyun", "Oyun", "Games", 1), ("backend", "Backend", "Backend", 2), ("web", "Web", "Web", 3)]

PROJECTS = [
    {
        "number": 1, "title": "Safe City: 2072", "slug": "safe-city-2072", "year": 2026, "cats": ["oyun"],
        "stack": "Unity · C#",
        "role_tr": "4 kişilik ekipte sistem mimarisi ve kodlama",
        "role_en": "System architecture and programming in a team of four",
        "duration_tr": "48 saat · game jam", "duration_en": "48 hours · game jam",
        "summary_tr": "Nisan 2026'da bir game jam'de 48 saatte geliştirdiğimiz, pixel art tarzında kontrol noktası denetim oyunu.",
        "summary_en": "A pixel-art checkpoint inspection game we built in 48 hours at a game jam in April 2026.",
        "problem_tr": "48 saat içinde, oyuncunun her kararının bir sonucu olduğu ve kuralları dikkatle uygulamayı gerektiren oynanabilir bir oyun çıkarmamız gerekiyordu.",
        "problem_en": "In 48 hours we had to ship a playable game where every decision has a consequence and the rules must be applied carefully.",
        "did_tr": "Ekipte sistem mimarisini ve kodlamayı üstlendim; kimlik kartı ve sağlık belgesini kural kitabıyla karşılaştıran denetim döngüsünü Unity ve C# ile kurdum.\n"
                  "Geçerli yıl, izinli ve karantinalı bölgeler, onaylı kurumlar ve vücut sıcaklığından oluşan kural setini oyuna bağladım.\n"
                  "Her ziyaretçi için üç karar sundum: içeri al (Clear), tara (Scan) ya da enfekte olarak işaretle (Resurgent).",
        "did_en": "I owned the system architecture and programming, building the inspection loop that checks ID cards and medical certificates against the rulebook in Unity and C#.\n"
                  "I wired in the rule set: valid year, allowed and quarantined zones, approved institutions and body temperature.\n"
                  "Each visitor gets one of three decisions: let in (Clear), scan (Scan) or flag as infected (Resurgent).",
        "result_tr": "Dört kişilik ekiple 48 saatte oynanabilir bir oyun teslim ettik; oyuncu her ziyaretçide belgeleri kurallarla karşılaştırıp karar veriyor.",
        "result_en": "Our team of four delivered a playable game in 48 hours; for every visitor the player compares documents with the rules and decides.",
        "flow_tr": "Kimlik kartı\nSağlık belgesi\nKural kitabı\nKarar",
        "flow_en": "ID card\nMedical certificate\nRulebook\nDecision",
    },
    {
        "number": 2, "title": "ozaydin.dev", "slug": "ozaydin-dev", "year": 2026, "cats": ["backend", "web"],
        "stack": "Django · Three.js · PostgreSQL · Nginx", "live_url": "https://ozaydin.dev",
        "repo_url": "https://github.com/rosko35/ozaydin-dev",
        "role_tr": "Tasarım ve geliştirme", "role_en": "Design and development",
        "duration_tr": "Yayında · gelişiyor", "duration_en": "Live · evolving",
        "summary_tr": "Şu an baktığın site. Django ile yazıldı, kendi sunucumda yayında.",
        "summary_en": "The site you're looking at. Built with Django and running on my own server.",
        "problem_tr": "CV gibi durmayan, ne yaptığımı anlatmak yerine gösteren bir site istedim.",
        "problem_en": "I wanted a site that shows what I do instead of reading like a CV.",
        "did_tr": "Siteyi Python ve Django ile kurdum; projeler ve yazılar admin panelinden ekleniyor, Türkçe ve İngilizce.\n"
                  "Binlerce 0 ve 1'den oluşan 3D alanı ve sayfa geçişlerini Three.js ile hazırladım.\n"
                  "Ubuntu sunucuda Nginx, Gunicorn, PostgreSQL ve HTTPS ile yayına aldım.",
        "did_en": "Built with Python and Django; projects and posts are managed from the admin panel, in Turkish and English.\n"
                  "Made the 3D field of thousands of 0s and 1s and the page transitions with Three.js.\n"
                  "Deployed it on an Ubuntu server with Nginx, Gunicorn, PostgreSQL and HTTPS.",
        "result_tr": "Sayfa önce metin olarak açılır; 3D alan arkadan yüklenir, zayıf cihazlarda kendini hafifletir.",
        "result_en": "Pages open as text first; the 3D field loads afterwards and scales itself down on weaker devices.",
        "flow_tr": "Tarayıcı\nNginx\nGunicorn · Django\nPostgreSQL",
        "flow_en": "Browser\nNginx\nGunicorn · Django\nPostgreSQL",
    },
]


def seed(apps, schema_editor):
    Category = apps.get_model("projects", "Category")
    Project = apps.get_model("projects", "Project")
    cats = {}
    for slug, tr, en, order in CATEGORIES:
        cats[slug], _ = Category.objects.get_or_create(slug=slug, defaults={"name_tr": tr, "name_en": en, "order": order})
    for data in PROJECTS:
        data = dict(data)
        slugs = data.pop("cats")
        if Project.objects.filter(slug=data["slug"]).exists():
            continue
        p = Project.objects.create(**data)
        p.categories.set([cats[s] for s in slugs])


def unseed(apps, schema_editor):
    apps.get_model("projects", "Project").objects.filter(slug__in=[p["slug"] for p in PROJECTS]).delete()


class Migration(migrations.Migration):
    dependencies = [("projects", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
