"""Yeni alanlar (Güvenlik, Ağ, Altyapı, IoT) ve GitHub'daki yedi yeni proje."""
from django.db import migrations

CATEGORIES = [
    ("guvenlik", "Güvenlik", "Security", 4),
    ("ag", "Ağ", "Network", 5),
    ("altyapi", "Altyapı", "Infrastructure", 6),
    ("iot", "IoT", "IoT", 7),
]

REPO = "https://github.com/rosko35/"

PROJECTS = [
    {
        "number": 3, "title": "Mini SIEM", "slug": "mini-siem", "year": 2026, "cats": ["guvenlik", "altyapi"],
        "featured": True, "repo_url": REPO + "mini-siem",
        "stack": "Python · FastAPI · SQLite · Docker",
        "role_tr": "Tasarım ve geliştirme", "role_en": "Design and development",
        "summary_tr": "Tek bir Linux sunucusu için yazdığım küçük bir log izleme ve saldırı tespit sistemi. SSH ve nginx loglarını okuyup kurallara göre alarm üretiyor.",
        "summary_en": "A small log monitoring and intrusion detection system I wrote for a single Linux server. It reads SSH and nginx logs and raises alerts based on rules.",
        "problem_tr": "Sitemin çalıştığı sunucuya gerçekte neyin saldırdığını görmek istedim. Ama ücretli bir SIEM ya da siteden fazla bellek isteyen büyük bir log yığını istemedim.",
        "problem_en": "I wanted to see what was actually attacking the server my site runs on, without paying for a SIEM or running a log stack that needs more memory than the site itself.",
        "did_tr": "SSH ve nginx loglarını takip eden, kaldığı yerden devam eden bir okuyucu yazdım.\n"
                  "Brute force ve web taraması gibi denemeleri yakalayan YAML kuralları hazırladım; her kural MITRE ATT&CK ile eşleşiyor.\n"
                  "Alarmlar Telegram'a toplu gidiyor; olaylar SQLite'ta duruyor ve saldırı haritası olan salt okunur bir dashboard'da görünüyor.",
        "did_en": "Wrote a reader that follows SSH and nginx logs and picks up where it left off.\n"
                  "Wrote YAML rules that catch attempts like brute force and web scanning; every rule is mapped to MITRE ATT&CK.\n"
                  "Alerts go to Telegram in batches; events are kept in SQLite and shown on a read-only dashboard with an attack map.",
        "result_tr": "Sitenin yanında salt okunur çalışıyor: hiçbir ayara dokunmuyor, dışarıya port açmıyor. Sunucu olmadan denemek için sahte trafik üreten bir demo modu da var.",
        "result_en": "It runs next to the site as a read-only guest: it doesn't touch any settings and opens no public ports. There's also a demo mode that generates fake traffic, so it can be tried without a server.",
        "flow_tr": "SSH ve nginx logları\nKural motoru\nSQLite\nDashboard · Telegram",
        "flow_en": "SSH and nginx logs\nRule engine\nSQLite\nDashboard · Telegram",
    },
    {
        "number": 4, "title": "SSH Honeypot", "slug": "ssh-honeypot", "year": 2026, "cats": ["guvenlik", "ag"],
        "featured": True, "repo_url": REPO + "ssh-honeypot",
        "stack": "Python · asyncssh · SQLite",
        "role_tr": "Tasarım ve geliştirme", "role_en": "Design and development",
        "summary_tr": "Sıradan bir SSH sunucusu gibi görünen ve botların denediği kullanıcı adı ile parolaları kaydeden düşük etkileşimli bir honeypot.",
        "summary_en": "A low-interaction honeypot that looks like an ordinary SSH server and records the usernames and passwords bots try.",
        "problem_tr": "Mini SIEM brute force denemelerini gösteriyordu ama parolaları ve botların içeri girince ne yaptığını göstermiyordu. Bunu kimseye gerçek bir shell vermeden görmek istedim.",
        "problem_en": "Mini SIEM showed brute force attempts, but not the passwords or what bots do once they get in. I wanted to see that without giving anyone a real shell.",
        "did_tr": "asyncssh ile gerçek bir SSH sunucusu gibi davranan, her giriş denemesini ve istemcinin parmak izini kaydeden bir sunucu yazdım.\n"
                  "Tamamen bellekte çalışan sahte bir shell yaptım; komutlar sistemde hiç çalışmıyor, indirme denemelerinde yalnızca adres kaydediliyor.\n"
                  "Kayıtlar SQLite'a ve Mini SIEM'in okuyabildiği sshd biçiminde bir loga gidiyor; üstüne küçük bir dashboard ekledim.",
        "did_en": "Built a server with asyncssh that behaves like a real SSH server and records every login attempt and the client's fingerprint.\n"
                  "Made a fake shell that runs entirely in memory; commands never run on the system, and download attempts only record the address.\n"
                  "Records go to SQLite and to an sshd-style log that Mini SIEM can read; I added a small dashboard on top.",
        "result_tr": "Saldırgan hiçbir zaman gerçek bir shell'e ulaşmıyor ve her bağlantının süresi ile boyutu sınırlı. Bunu testlerle doğruladım: indirme ya da port yönlendirme denendiğinde dışarıya tek bir bağlantı açılmıyor.",
        "result_en": "The attacker never reaches a real shell, and every connection is limited in time and size. I checked this with tests: when a download or port forwarding is attempted, not a single outbound connection is opened.",
        "flow_tr": "SSH botları\nSahte SSH sunucusu\nSahte shell\nSQLite · log\nDashboard",
        "flow_en": "SSH bots\nFake SSH server\nFake shell\nSQLite · log\nDashboard",
    },
    {
        "number": 5, "title": "Async Vuln Scanner", "slug": "async-vuln-scanner", "year": 2026, "cats": ["guvenlik", "ag"],
        "featured": False, "repo_url": REPO + "async-vuln-scanner",
        "stack": "Python · asyncio · Docker",
        "role_tr": "Tasarım ve geliştirme", "role_en": "Design and development",
        "summary_tr": "asyncio ile yazdığım bir port tarayıcı. Açık portlarda çalışan servisin sürümünü bulup bilinen açıkları NVD'de arıyor.",
        "summary_en": "A port scanner I wrote with asyncio. It finds the version of the service on each open port and looks up known vulnerabilities in NVD.",
        "problem_tr": "nmap gibi araçların ağda gerçekte ne yaptığını çıktısına bakarak değil, kendim yazarak anlamak istedim. Ev ağım için de büyütebileceğim küçük bir tarayıcı lazımdı.",
        "problem_en": "I wanted to understand what tools like nmap actually do on the network by writing one, not just by reading their output. I also needed a small scanner I could build on for my home network.",
        "did_tr": "Root yetkisi istemeyen bir TCP taraması yazdım.\n"
                  "Banner'lardan ürün ve sürümü çıkaran bir imza tablosu ve cevapları önbelleğe alan bir NVD istemcisi ekledim.\n"
                  "JSON ve HTML raporlarının yanına iki taramayı karşılaştıran bir diff komutu koydum; denemek için eski servislerle bir Docker laboratuvarı kurdum.",
        "did_en": "Wrote a TCP scan that needs no root.\n"
                  "Added a signature table that pulls product and version out of banners, and an NVD client that caches its answers.\n"
                  "Next to JSON and HTML reports I added a diff command that compares two scans; I set up a Docker lab with old services to test against.",
        "result_tr": "Açıkça izin verilmedikçe herkese açık adresleri taramayı reddediyor. Homelab Security Panel'deki haftalık tarama bu tarayıcının üzerine kurulu.",
        "result_en": "It refuses to scan public addresses unless permission is given explicitly. The weekly scan in Homelab Security Panel is built on this scanner.",
        "flow_tr": "Hedefler\nPort taraması\nBanner · sürüm\nCVE araması\nRapor · diff",
        "flow_en": "Targets\nPort scan\nBanner · version\nCVE lookup\nReport · diff",
    },
    {
        "number": 6, "title": "Net Traffic Analyzer", "slug": "net-traffic-analyzer", "year": 2026, "cats": ["ag", "guvenlik"],
        "featured": False, "repo_url": REPO + "net-traffic-analyzer",
        "stack": "Python",
        "role_tr": "Tasarım ve geliştirme", "role_en": "Design and development",
        "summary_tr": "Paket kayıtlarını okuyup kimin kiminle konuştuğunu ve ağda neyin şifresiz dolaştığını raporlayan bir araç.",
        "summary_en": "A tool that reads packet captures and reports who talks to whom and what travels unencrypted on the network.",
        "problem_tr": "Wireshark çıktısını okuyabiliyordum ama baytların aslında ne olduğunu tam bilmiyordum. Bu yüzden paket kütüphanesi kullanmadan her başlığı kendim ayrıştırmaya karar verdim.",
        "problem_en": "I could read Wireshark's output but didn't really know what the bytes were. So I decided to parse every header myself, without a packet library.",
        "did_tr": "Ethernet ve TCP'den HTTP, TLS, DNS ve MQTT'ye kadar protokol çözücülerini elle yazdım.\n"
                  "Açık metin parola, şifresiz MQTT, port taraması ve ARP zehirleme gibi sorunları bulan kurallar ekledim.\n"
                  "Konsol, JSON ve HTML raporlarına ek olarak iki kaydı yan yana koyan bir karşılaştırma komutu yazdım.",
        "did_en": "Wrote the protocol decoders by hand, from Ethernet and TCP up to HTTP, TLS, DNS and MQTT.\n"
                  "Added rules that find problems like cleartext passwords, unencrypted MQTT, port scans and ARP poisoning.\n"
                  "Besides console, JSON and HTML reports, wrote a compare command that puts two captures side by side.",
        "result_tr": "Projeyle gelen örnek kayıtlarda farkı tek bir tablo gösteriyor: şifresiz MQTT'de parolalar ve ölçümler okunuyor, TLS'li olanda okunmuyor. Bulduğu gizli bilgiler raporlarda varsayılan olarak maskeleniyor.",
        "result_en": "On the sample captures that ship with the project, one table shows the difference: with plain MQTT the passwords and readings are readable, with TLS they aren't. Secrets it finds are masked in reports by default.",
        "flow_tr": "Paket kaydı\nÇözücüler\nAkış birleştirme\nBulgu kuralları\nRapor",
        "flow_en": "Packet capture\nDecoders\nStream reassembly\nFinding rules\nReport",
    },
    {
        "number": 7, "title": "Server Hardening", "slug": "server-hardening", "year": 2026, "cats": ["altyapi", "guvenlik"],
        "featured": True, "repo_url": REPO + "server-hardening",
        "stack": "Ansible · Python · Lynis",
        "role_tr": "Tasarım ve geliştirme", "role_en": "Design and development",
        "summary_tr": "Ansible ile yazdığım, işe sunucuyu değiştirerek değil önce denetleyerek başlayan bir sunucu sıkılaştırma projesi.",
        "summary_en": "A server hardening project in Ansible that starts by auditing the server instead of changing it.",
        "problem_tr": "Sitemi ve e-postamı çalıştıran tek bir sunucum var. Okuduğum rehberlerin çoğu, yanlış sırayla yapılınca beni sunucunun dışında bırakabilecek adımlarla başlıyordu.",
        "problem_en": "I have one server that runs my site and my email. Most guides I read started with steps that could lock me out of it if done in the wrong order.",
        "did_tr": "Varsayılan hâliyle hiçbir şeyi değiştirmeyen, yalnızca okuyup rapor yazan bir denetim adımı kurdum.\n"
                  "SSH, güvenlik duvarı ve fail2ban gibi her düzeltmeyi ayrı bir kategori yaptım; her biri tek tek açılıyor ve önce kuru çalıştırılabiliyor.\n"
                  "Değişiklikten önce orijinal dosyaları yedekleyen ve hepsini geri yükleyebilen bir rollback playbook'u yazdım.",
        "did_en": "Built an audit step that changes nothing by default; it only reads and writes a report.\n"
                  "Made every fix, like SSH, the firewall and fail2ban, its own category; each is turned on one at a time and can be dry-run first.\n"
                  "Wrote a rollback playbook that backs up the original files before any change and can restore all of them.",
        "result_tr": "SSH ayarı değişince yeni bir bağlantı açılıp girişin hâlâ çalıştığı kontrol ediliyor; güvenlik duvarı çalışan bir servisi onay almadan kapatmıyor. CI her şeyi iki kez uyguluyor ve ikinci turda değişiklik görürse hata veriyor.",
        "result_en": "After an SSH change, a new connection is opened to check that login still works; the firewall won't close a running service without approval. CI applies everything twice and fails if the second run changes anything.",
        "flow_tr": "Denetim\nPlan\nTek kategori uygula\nDoğrula\nGeri al",
        "flow_en": "Audit\nPlan\nApply one category\nVerify\nRoll back",
    },
    {
        "number": 8, "title": "IoT Sensor Panel", "slug": "iot-sensor-panel", "year": 2026, "cats": ["iot", "guvenlik"],
        "featured": False, "repo_url": REPO + "iot-sensor-panel",
        "stack": "ESP32 · MQTT · InfluxDB · Grafana",
        "role_tr": "Tasarım ve geliştirme", "role_en": "Design and development",
        "summary_tr": "Sensör verisini MQTT ile toplayıp Grafana'da canlı gösteren bir panel. Bir eşik aşılınca ya da cihaz susunca Telegram'a uyarı gidiyor.",
        "summary_en": "A panel that collects sensor data over MQTT and shows it live in Grafana. When a threshold is crossed or a device goes quiet, an alert goes to Telegram.",
        "problem_tr": "Sensörden başlayıp bir panele ve telefonumdaki bir uyarıya kadar giden bütün bir zincir kurmak istedim. Şifresiz MQTT'nin ağda neyi açık ettiğini de kendim görmek istedim.",
        "problem_en": "I wanted to build the whole chain, from a sensor to a panel and an alert on my phone. I also wanted to see for myself what plain MQTT exposes on the network.",
        "did_tr": "Gün içi değişimi ve arızaları taklit eden bir sensör simülatörü yazdım; aynı veriyi gönderen mikrodenetleyici firmware'ini de hazırladım.\n"
                  "Gelen veriyi doğrulayıp InfluxDB'ye yazan ve kurallarla uyarı üreten bir Python servisi yazdım.\n"
                  "Aynı sistemi hem şifresiz hem de TLS, parola ve cihaz başına yetki ile çalışacak şekilde kurdum.",
        "did_en": "Wrote a sensor simulator that mimics daily changes and faults, and the microcontroller firmware that sends the same data.\n"
                  "Wrote a Python service that validates incoming data, writes it to InfluxDB and raises alerts based on rules.\n"
                  "Set up the same system to run both unencrypted and with TLS, passwords and per-device permissions.",
        "result_tr": "Tek komutla ayağa kalkıyor ve birkaç saniyede simüle cihazlar panelde görünüyor. Testler, şifresiz modda parolanın ve verinin ağda okunduğunu, TLS'li modda okunmadığını kendiliğinden doğruluyor.",
        "result_en": "It starts with one command and the simulated devices show up on the panel within seconds. Tests check on their own that the password and data are readable on the wire in plain mode and not with TLS.",
        "flow_tr": "Sensör · simülatör\nMQTT\nIngest servisi\nInfluxDB\nGrafana",
        "flow_en": "Sensor · simulator\nMQTT\nIngest service\nInfluxDB\nGrafana",
    },
    {
        "number": 9, "title": "Homelab Security Panel", "slug": "homelab-security-panel", "year": 2026, "cats": ["guvenlik", "ag"],
        "featured": True, "repo_url": REPO + "homelab-security-panel",
        "stack": "Python · Docker · Grafana",
        "role_tr": "Tasarım ve geliştirme", "role_en": "Design and development",
        "summary_tr": "Port tarayıcımı, Mini SIEM'i ve sensör panelimi tek bir kurulumda birleştiren ev ağı güvenlik paneli.",
        "summary_en": "A home network security panel that brings my port scanner, Mini SIEM and sensor panel together in one setup.",
        "problem_tr": "Üç proje ayrı ayrı çalışıyordu ama ağımla ilgili asıl soruma hiçbiri tek başına cevap vermiyordu: tanımadığım bir cihaz var mı, geçen hafta kapalı olan bir şey dinlemeye başladı mı?",
        "problem_en": "The three projects worked on their own, but none of them answered my real question alone: is there a device I don't know, and did something start listening that wasn't last week?",
        "did_tr": "Ağdaki cihazların envanterini tutan ve bilinmeyen bir cihaz girince Telegram'a mesaj atan bir keşif servisi yazdım.\n"
                  "Cihazları her hafta tarayıp bir önceki haftayla karşılaştıran bir iş ekledim.\n"
                  "Router loglarını Mini SIEM'e aktaran küçük bir syslog alıcısı yazdım ve hepsini tek bir Grafana panelinde topladım.",
        "did_en": "Wrote a discovery service that keeps an inventory of devices on the network and sends a Telegram message when an unknown one joins.\n"
                  "Added a weekly job that scans the devices and compares the results with the previous week.\n"
                  "Wrote a small syslog receiver that passes router logs to Mini SIEM, and put everything on one Grafana panel.",
        "result_tr": "Hepsi tek komutla başlıyor ve aksi söylenmedikçe yalnızca yerelde dinliyor. Bütün uyarılar tek bir sohbete düşüyor.",
        "result_en": "Everything starts with one command and listens only locally unless told otherwise. All alerts land in a single chat.",
        "flow_tr": "Ev ağı · router\nKeşif · tarama · syslog\nMini SIEM\nInfluxDB\nGrafana · Telegram",
        "flow_en": "Home network · router\nDiscovery · scan · syslog\nMini SIEM\nInfluxDB\nGrafana · Telegram",
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
    Category = apps.get_model("projects", "Category")
    apps.get_model("projects", "Project").objects.filter(slug__in=[p["slug"] for p in PROJECTS]).delete()
    # Yalnızca bu migration'ın eklediği ve artık boş kalan alanlar silinir.
    Category.objects.filter(slug__in=[c[0] for c in CATEGORIES], projects__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("projects", "0004_kart_gorseli")]
    operations = [migrations.RunPython(seed, unseed)]
