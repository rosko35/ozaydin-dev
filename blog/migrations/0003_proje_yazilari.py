"""Yedi yeni proje için blog yazıları (yayında). Her yazı ilgili projeye bağlanır."""
import datetime

from django.db import migrations

TAGS = {
    "guvenlik": ("güvenlik", "security"),
    "python": ("python", "python"),
    "ag": ("ağ", "network"),
    "iot": ("iot", "iot"),
    "sunucu": ("sunucu", "server"),
}
NEW_TAGS = ["guvenlik", "python", "ag", "iot"]  # bu migration'ın eklediği; sunucu 0002'den gelir

POSTS = [
    {
        "slug": 'mini-siem-log-izleme',
        "project": 'mini-siem',
        "day": 14,
        "tags": ['guvenlik', 'python', 'sunucu'],
        "title_tr": 'Tek sunucu için küçük bir log izleme sistemi: mini-siem',
        "title_en": 'A small log monitor for a single server: mini-siem',
        "summary_tr": "Tek bir Linux sunucusunun loglarını izleyip şüpheli girişleri Telegram'a bildiren küçük bir sistem yaptım.",
        "summary_en": "I built a small system that watches a single Linux server's logs and sends suspicious activity to Telegram.",
        "body_tr": """\
Sunucuma gerçekte neyin saldırdığını görmek için küçük bir log izleme ve saldırı tespit sistemi yazdım. Küçük bir VPS'te, canlı bir web sitesinin yanında çalıştırıyorum.

## Ne yapıyor

SSH ve nginx loglarını takip ediyor, satırları YAML ile yazılmış kurallardan geçiriyor. Kurallardan biri tetiklenince alarm Telegram'a düşüyor. Alarmlar toplu gönderiliyor; yani bir saldırı seli binlerce mesaj yerine birkaç saniyede bir tek mesaj üretiyor. Her kural MITRE ATT&CK ile eşleştirilmiş. Olaylar SQLite'ta duruyor ve saldırıların haritasını gösteren salt okunur bir dashboard var.

## Misafir gibi davranmak

Aynı VPS'te canlı bir web sitesi çalıştığı için mini-siem'i salt okunur bir misafir olarak tasarladım. nginx'e, SSH'a ya da güvenlik duvarına dokunmuyor ve dışarıya port açmıyor.

Kural pencereleri duvar saati yerine olay zamanını kullanıyor. Bu yüzden eski bir logu baştan oynattığımda canlıda çıkacak alarmların aynısı çıkıyor ve kuralları test etmek kolaylaşıyor.
""",
        "body_en": """\
I wrote a small log monitoring and intrusion detection system to see what is actually attacking my server. I run it on a small VPS next to a live website.

## What it does

It follows the SSH and nginx logs and runs every line through rules written in YAML. When a rule fires, an alert goes to Telegram. Alerts are sent in batches, so an attack flood produces one message every few seconds instead of thousands. Each rule is mapped to MITRE ATT&CK. Events are stored in SQLite, and there is a read-only dashboard with a map of the attacks.

## Acting like a guest

Since a live website runs on the same VPS, I designed mini-siem as a read-only guest. It does not touch nginx, SSH or the firewall, and it opens no public port.

Rule windows use event time instead of wall-clock time. So when I replay an old log from the start, it raises the same alerts a live run would, which makes the rules easier to test.
""",
    },
    {
        "slug": 'ssh-honeypot-notlari',
        "project": 'ssh-honeypot',
        "day": 15,
        "tags": ['guvenlik', 'python'],
        "title_tr": 'Botları izlemek için sahte bir SSH sunucusu: ssh-honeypot',
        "title_en": 'A fake SSH server for watching bots: ssh-honeypot',
        "summary_tr": 'Gerçek bir sunucu gibi görünen ama hiçbir şey çalıştırmayan, bağlanan botların denemelerini kaydeden bir SSH honeypot yazdım.',
        "summary_en": 'I wrote an SSH honeypot that looks like a real server but runs nothing, and records what connecting bots try.',
        "body_tr": """\
ssh-honeypot, sıradan bir OpenSSH sunucusu gibi görünen sahte bir SSH sunucusu. Boştaki bir portu dinliyor ve ona bağlanan botların neler denediğini kaydediyor: kullanıcı adları, parolalar, istemci sürümleri. İstersem bazı denemelere "giriş yaptırıp" sahte bir shell'e düşürüyor ve orada yazılan komutları da kaydediyor.

## Sahte shell

Shell tamamen Python ile, bellekte yapılmış bir taklit. Hiçbir komut gerçekten çalışmıyor ve hiçbir şey indirilmiyor.

## Neye dikkat ettim

Bir honeypot'un kendisi sunucudaki en tehlikeli şey olmamalı. O yüzden süreç hiçbir ayrıcalıkla çalışmıyor ve her bağlantı süre, boyut ve sayı olarak sınırlı. Saldırganın etkileyebildiği her şey tek yönde akıyor, yani soketten kaydediciye. Giriş ve boşta kalma için zaman aşımları var. Dashboard ayrı bir süreç, veritabanını salt okunur açıyor ve yalnızca yerel adresten erişilebiliyor.

Kayıtları mini-siem de okuyabiliyor, böylece iki proje birbirine bağlanıyor.
""",
        "body_en": """\
ssh-honeypot is a fake SSH server that looks like an ordinary OpenSSH server. It listens on an idle port and records what the bots that connect to it try: usernames, passwords, client versions. If I want, it lets some attempts "log in" to a fake shell and records the commands typed there too.

## The fake shell

The shell is an imitation built entirely in Python, in memory. No command really runs and nothing is downloaded.

## What I paid attention to

A honeypot should not be the most dangerous thing on the server. So the process runs with no privileges, and every connection is limited in time, size and count. Everything an attacker can influence flows in one direction, from the socket to the recorder. There are timeouts for login and for idle sessions. The dashboard is a separate process, opens the database read-only and is reachable only from the local address.

mini-siem can read the records too, so the two projects can be connected.
""",
    },
    {
        "slug": 'async-vuln-scanner-notlari',
        "project": 'async-vuln-scanner',
        "day": 16,
        "tags": ['guvenlik', 'python', 'ag'],
        "title_tr": 'Ev ağım için bir port tarayıcı: async-vuln-scanner',
        "title_en": 'A port scanner for my home network: async-vuln-scanner',
        "summary_tr": 'Açık portları bulup servis sürümlerini çıkaran ve bilinen açıkları arayan, asyncio tabanlı bir tarayıcı yazdım.',
        "summary_en": 'I wrote an asyncio-based scanner that finds open ports, works out service versions and looks up known vulnerabilities.',
        "body_tr": """\
async-vuln-scanner, asyncio ile yazılmış bir TCP port tarayıcısı. Açık portlara bağlanıp servisin banner'ına bakıyor, hangi ürünün ve hangi sürümün çalıştığını çıkarıyor ve sonucu NVD veritabanında arıyor. Sonuçtan bir rapor üretiyor.

Yalnızca kendi ağında ya da izinli sistemlerde kullanılmak için yazıldı. Araç da bunu hatırlatıyor: herkese açık adresleri, açıkça izin verilmedikçe taramayı reddediyor. Denemek için repoda bilerek eski sürümlerle kurulmuş bir Docker laboratuvarı var.

## Aşamalara bölmek

İşlemi üç aşamaya ayırdım. Önce bütün hedeflerde ucuz olan port taraması yapılıyor. Sonra yalnızca açık çıkan portlarda servis tespiti, en son da her farklı ürün ve sürüm için tek bir NVD sorgusu. Böylece yavaş ve sınırlı olan kısım mümkün olduğunca az iş yapıyor.

## Fark çıkarmak

Tek bir taramadan çok, iki tarama arasındaki fark işe yarıyor. Bu yüzden diff komutu yeni cihazları, açılan ve kapanan portları, yeni CVE'leri listeliyor. Gece çalışan bir cron işine uygun.
""",
        "body_en": """\
async-vuln-scanner is a TCP port scanner written with asyncio. It connects to open ports, reads the service's banner, works out which product and version is running, and looks the result up in the NVD database. It turns the result into a report.

It was written to be used only on the owner's own network or on systems with permission to test. The tool enforces this too: it refuses to scan public addresses unless permission is explicitly confirmed. To try it out, the repo includes a Docker lab set up with deliberately old versions.

## Splitting it into stages

I split the work into three stages. First comes the port scan, which is cheap, over all targets. Then service detection only on the ports that turned out open, and last, one NVD query for each distinct product and version. That way the slow, rate-limited part does as little work as possible.

## Looking at the difference

A single scan matters less than the difference between two scans. So the diff command lists new devices, ports that opened or closed, and new CVEs. It suits a cron job that runs at night.
""",
    },
    {
        "slug": 'net-traffic-analyzer-notlari',
        "project": 'net-traffic-analyzer',
        "day": 17,
        "tags": ['ag', 'python', 'guvenlik'],
        "title_tr": 'Paket kayıtlarını okuyan bir araç: net-traffic-analyzer',
        "title_en": 'A tool that reads packet captures: net-traffic-analyzer',
        "summary_tr": 'Paket yakalama dosyalarını okuyup kimin kiminle konuştuğunu ve ağda nelerin şifresiz dolaştığını gösteren bir araç yazdım.',
        "summary_en": 'I wrote a tool that reads packet capture files and shows who talks to whom and what travels unencrypted on the network.',
        "body_tr": """\
net-traffic-analyzer (kısaca nta), pcap ve pcapng dosyalarını okuyan bir analiz aracı. Üç soruya cevap veriyor: kim kiminle konuşuyor, hangi protokoller kullanılıyor, ağda ne şifresiz dolaşıyor. Sonucu bir rapora yazıyor. Raporda açık metin parola ya da şifresiz MQTT gibi bulgular nedenleri ve önerileriyle listeleniyor.

## Her şeyi elle yazmak

Protokol çözücülerin hepsini elle yazdım, hazır bir paket kütüphanesi kullanmadım. Projenin asıl amacı da buydu: bir paketin içinde baytların nerede durduğunu görmek. Kayıt dosyası belleğe tamamen yüklenmiyor, çerçeveler tek tek okunuyor.

## Örnekler ve sınırlar

Repodaki örnek kayıtlar sentetik; bayt bayt elle üretildi, gerçek bir ağ dinlenmedi. Örneklerden biri, aynı sensörlerin düz MQTT ile TLS üzerinden konuştuğu iki kayıt. Birinde parola okunabiliyor, ötekinde yalnızca şifreli kayıtlar görünüyor.

Araç yalnızca kendine ait ağlar ya da izlemeye yetkili olunan ağlar için. Bulduğu gizli bilgileri de varsayılan olarak maskeliyor.
""",
        "body_en": """\
net-traffic-analyzer (nta for short) is an analysis tool that reads pcap and pcapng files. It answers three questions: who talks to whom, which protocols are in use, and what travels unencrypted on the network. It writes the result into a report. In the report, findings such as plaintext passwords or unencrypted MQTT are listed with their reasons and suggested fixes.

## Writing everything by hand

I wrote all the protocol decoders by hand and did not use a ready-made packet library. That was the real point of the project: seeing where the bytes sit inside a packet. The capture file is never loaded into memory whole; frames are read one by one.

## Samples and limits

The sample captures in the repo are synthetic; they were built byte by byte and no real network was sniffed. One of the samples is a pair of captures where the same sensors talk over plain MQTT and over TLS. In one the password is readable, in the other only encrypted records show up.

The tool is only for networks the user owns or is authorized to monitor. It also masks any secrets it finds by default.
""",
    },
    {
        "slug": 'iot-sensor-panel-notlari',
        "project": 'iot-sensor-panel',
        "day": 18,
        "tags": ['iot', 'python'],
        "title_tr": 'Sensör verisinden panele: iot-sensor-panel',
        "title_en": 'From sensor data to a dashboard: iot-sensor-panel',
        "summary_tr": "Sensör verisini MQTT ile toplayıp Grafana'da gösteren, güvenli ve güvensiz modda çalışabilen bir IoT paneli kurdum.",
        "summary_en": 'I built an IoT dashboard that collects sensor data over MQTT and shows it in Grafana, and can run in a secure and an insecure mode.',
        "body_tr": """\
iot-sensor-panel, baştan sona kurduğum bir sensör paneli. Sensör cihazları (ya da gerçek cihaz yokken bir Python simülatörü) sıcaklık, nem ve hareket verisini MQTT ile yayınlıyor. Bir Python servisi gelen okumaları doğrulayıp veritabanına yazıyor, Grafana da her cihaz için canlı bir panel gösteriyor. Eşik aşımı ve çevrimdışı kalan cihaz uyarıları Telegram'a gidiyor. Bir cihaz belli bir süre sessiz kalırsa çevrimdışı sayılıyor. Sensör kartı için ayrı bir firmware projesi de var.

## Güvenlik tarafı

En çok önem verdiğim kısım bu. Aynı yapı iki modda çalışıyor: düz MQTT ve anonim erişimle "insecure", TLS, parola ve cihaz başına yetkilerle "secure". Aradaki farkı Wireshark üzerinden anlatan bir doküman da var.

## Gelen veriye güvenmemek

Servis her okumayı kontrol ediyor. Fiziksel olarak mümkün olmayan değerler ya da konudaki cihaz adıyla uyuşmayan mesajlar kaydedilmiyor, yalnızca sayılıyor. Uyarılar eşik civarında sürekli açılıp kapanmasın diye biraz pay bırakıyor.
""",
        "body_en": """\
iot-sensor-panel is a sensor dashboard I built from start to finish. Sensor devices (or a Python simulator when there is no real device) publish temperature, humidity and motion data over MQTT. A Python service validates the incoming readings and writes them to a database, and Grafana shows a live panel for each device. Threshold and offline-device alerts go to Telegram. A device that stays silent for a set time counts as offline. There is also a separate firmware project for the sensor board.

## The security side

This is the part I care about most. The same stack runs in two modes: "insecure" with plain MQTT and anonymous access, and "secure" with TLS, passwords and per-device permissions. There is also a document that explains the difference using Wireshark.

## Not trusting incoming data

The service checks every reading. Values that are physically impossible, or messages whose device name does not match the topic, are not stored, only counted. Alerts leave some slack so they do not flip on and off around the threshold.
""",
    },
    {
        "slug": 'server-hardening-notlari',
        "project": 'server-hardening',
        "day": 19,
        "tags": ['sunucu', 'guvenlik'],
        "title_tr": 'Önce denetle, sonra değiştir: server-hardening',
        "title_en": 'Audit first, change later: server-hardening',
        "summary_tr": 'Ubuntu ve Debian sunucuları Ansible ile sıkılaştıran, varsayılanda hiçbir şeyi değiştirmeyip önce denetleyen bir proje yaptım.',
        "summary_en": 'I made a project that hardens Ubuntu and Debian servers with Ansible, and by default only audits and changes nothing.',
        "body_tr": """\
Çoğu sıkılaştırma playbook'u işe bir şeyleri değiştirerek başlıyor. server-hardening ise önce bakıyor. Varsayılanda sunucuyu yalnızca okuyor ve bilgisayarıma bir rapor yazıyor: hangi portlar dinleniyor, SSH nasıl ayarlanmış, hangi güncellemeler bekliyor. Her düzeltme ayrı bir kategori ve hepsi kapalı geliyor. Önce kuru çalıştırma yapıp birer birer açıyorum. Lynis puanı da öncesi ve sonrası olarak karşılaştırılabiliyor.

Üzerinde canlı bir web sitesi çalışan gerçek bir sunucu için yazdım. Böyle bir sunucuda dikkatsiz bir playbook insanı dışarıda bırakabiliyor.

## Kilitlenmemek

SSH ayarı yerine konmadan önce doğrulanıyor, bir hata çıkarsa eski dosya geri yükleniyor. Oturumda geçerli bir anahtar yoksa parola girişini kapatmayı reddediyor. Sonunda yeni bir bağlantı açıp girişin hâlâ çalıştığını kontrol ediyor. Bir playbook'u iki kez çalıştırınca ikinci seferde hiçbir şey değişmemeli; CI bunu da kontrol ediyor.

## Yapmadıkları

Her değişiklikten önce orijinal dosyalar yedekleniyor ve rollback ile geri alınabiliyor. Bilerek yapmadığı şeyler de var: SSH portunu değiştirmiyor, sunucuyu yeniden başlatmıyor, paket kaldırmıyor.
""",
        "body_en": """\
Most hardening playbooks start by changing things. server-hardening looks first. By default it only reads the server and writes a report to my computer: which ports are listening, how SSH is configured, which updates are pending. Every fix is its own category and they all ship turned off. I do a dry run first and enable them one by one. The Lynis score can also be compared before and after.

I wrote it for a real server that runs a live website. On a server like that, a careless playbook can lock the owner out.

## Not locking yourself out

The SSH setting is validated before it is put in place, and if anything fails the old file is restored. If the session has no valid key, it refuses to turn off password login. At the end it opens a new connection to check that login still works. Running a playbook twice should change nothing the second time, and CI checks that too.

## What it does not do

Original files are backed up before every change and can be restored with the rollback playbook. There are also things it deliberately does not do: it does not change the SSH port, does not reboot the server, and does not remove packages.
""",
    },
    {
        "slug": 'homelab-security-panel-notlari',
        "project": 'homelab-security-panel',
        "day": 20,
        "tags": ['guvenlik', 'ag', 'iot'],
        "title_tr": 'Ev ağı için tek bir güvenlik paneli: homelab-security-panel',
        "title_en": 'One security panel for my home network: homelab-security-panel',
        "summary_tr": 'Önceki projelerimi birleştirip küçük bir bilgisayarda ya da eski bir laptopta çalışabilen bir ev ağı güvenlik paneli yaptım.',
        "summary_en": 'I combined my earlier projects into a home network security panel that can run on a small computer or an old laptop.',
        "body_tr": """\
homelab-security-panel, daha önce yaptığım üç projeyi tek kurulumda birleştiriyor: port tarayıcı, mini-siem ve sensör paneli. Aralarında eksik olan parçayı da bu proje ekliyor. Küçük bir bilgisayarda ya da eski bir laptopta çalışabiliyor.

## Ne ekliyor

Yerel ağdaki cihazları bir envantere kaydediyor ve ağa bilinmeyen bir cihaz girince Telegram'a mesaj gönderiyor. Haftada bir envanterdeki cihazları tarayıp sonucu bir önceki haftayla karşılaştırıyor: yeni açılan portlar, değişen sürümler. İlk tarama başlangıç referansı oluyor, sonrasında yalnızca değişiklikler bildiriliyor. Router'ın SSH olayları da mini-siem'e aktarılıyor. Hepsi tek bir Grafana panosunda toplanıyor.

## Neye dikkat ettim

İlk açılışta bulunan her cihaz için ayrı uyarı göndermek yerine tek bir özet mesaj gönderiliyor. Her şey varsayılan olarak yalnızca yerel adreste dinliyor.

Bu panel cihazları kaydediyor ve tarıyor. Bu yüzden yalnızca kendi ev ağı için tasarlandı; işyeri ya da kafe gibi başkasına ait ağlar için değil.
""",
        "body_en": """\
homelab-security-panel combines three projects I built earlier into one setup: the port scanner, mini-siem and the sensor dashboard. This project adds the missing piece between them. It can run on a small computer or an old laptop.

## What it adds

It records the devices on the local network in an inventory and sends a Telegram message when an unknown device joins. Once a week it scans the devices in the inventory and compares the result with the previous week: newly opened ports, changed versions. The first scan becomes the baseline, and after that only changes are reported. The router's SSH events are also fed into mini-siem. Everything comes together in a single Grafana dashboard.

## What I paid attention to

On first start it sends one summary message instead of a separate alert for every device it finds. Everything listens only on the local address by default.

This panel records and scans devices. So it was designed only for the owner's own home network, not for networks that belong to someone else, such as a workplace or a cafe.
""",
    },
]


def published_at(day):
    return datetime.datetime(2026, 11, day, 18, 0, tzinfo=datetime.timezone.utc)


def seed(apps, schema_editor):
    from blog.markdown import render  # geçmiş modellerde save() yok; HTML'i burada üret

    Tag = apps.get_model("blog", "Tag")
    Post = apps.get_model("blog", "Post")
    Project = apps.get_model("projects", "Project")
    for data in POSTS:
        if Post.objects.filter(slug=data["slug"]).exists():
            continue
        tags = [
            Tag.objects.get_or_create(slug=s, defaults={"name_tr": TAGS[s][0], "name_en": TAGS[s][1]})[0]
            for s in data["tags"]
        ]
        post = Post.objects.create(
            slug=data["slug"],
            title_tr=data["title_tr"],
            title_en=data["title_en"],
            summary_tr=data["summary_tr"],
            summary_en=data["summary_en"],
            body_tr=data["body_tr"],
            body_en=data["body_en"],
            body_html_tr=render(data["body_tr"]),
            body_html_en=render(data["body_en"]),
            status="published",
            published_at=published_at(data["day"]),
            related_project=Project.objects.filter(slug=data["project"]).first(),
        )
        post.tags.set(tags)


def unseed(apps, schema_editor):
    Tag = apps.get_model("blog", "Tag")
    Post = apps.get_model("blog", "Post")
    Post.objects.filter(slug__in=[d["slug"] for d in POSTS]).delete()
    for slug in NEW_TAGS:
        Tag.objects.filter(slug=slug, posts__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0002_ilk_yazi"),
        ("projects", "0005_yeni_projeler"),
    ]
    operations = [migrations.RunPython(seed, unseed)]
