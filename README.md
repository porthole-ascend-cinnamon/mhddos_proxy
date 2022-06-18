## IT Army of Ukraine Official Tool 

### [English Version](/README-EN.md)

- Вбудована база проксі з величезною кількістю IP по всьому світу
- Можливість задавати багато цілей з автоматичним балансуванням навантаження
- Безліч різноманітних методів
- Ефективне використання ресурсів завдяки асихронній архітектурі

### ⏱ Останні оновлення
  
Оновлення версії для Windows | Mac | Linux | Android | Docker: https://telegra.ph/Onovlennya-mhddos-proxy-04-16  

- **10.06.2022** Додано зручний спосіб вказати власний проксі напряму в команді запуску (параметр `--proxy`)
- **08.06.2022** Додано налаштування `--copies auto` для автоматичного вибору значення з врахуванням доступних ресурсів
- **25.05.2022** Покращено вивід за замовчуванням - більше нема потреби в параметрі `--debug`
- **24.05.2022** Додано можливість запуску з автоматичним оновленням - див. пункт [Запуск](#2--запуск)

### 1. 💽 Встановлення

#### Розширені інструкції - [натисніть тут](/docs/installation.md) 

#### Python (якщо не працює - спробуйте `python` або `python3.10` замість `python3`)

Потребує python >= 3.8 та git

    git clone https://github.com/porthole-ascend-cinnamon/mhddos_proxy.git
    cd mhddos_proxy
    python3 -m pip install -r requirements.txt

#### Docker

Встановіть і запустіть Docker: https://docs.docker.com/desktop/#download-and-install

### 2. 🕹 Запуск

#### Python з автоматичним оновленням (якщо не працює - спробуйте `python` або `python3.10` замість `python3`)

    ./runner.sh python3 https://example.com tcp://198.18.0.123:5678
    
Для [**Termux for Android**](https://telegra.ph/mhddos-proxy-for-Android-with-Termux-03-31) ось так:
```shell
bash runner.sh python https://example.com tcp://198.18.0.123:5678 -t 1000
```

#### Python (потребує оновлення вручну) (якщо не працює - спробуйте `python` або `python3.10` замість `python3`)

    python3 runner.py https://example.com tcp://198.18.0.123:5678

#### Docker (для Linux додавайте sudo на початку команди)

    docker run -it --rm --pull always ghcr.io/porthole-ascend-cinnamon/mhddos_proxy https://example.com tcp://198.18.0.123:5678

### 3. 🛠 Налаштування (більше у розділі [CLI](#cli))

Усі параметри можна комбінувати, можна вказувати і до і після переліку цілей

- Щоб додати ваш IP/VPN до атаки (особливо актуально для виділених серверів), додайте параметр `--vpn`
- Щоб обрати цілі від IT Army of Ukraine (https://t.me/itarmyofukraine2022), додайте параметр `--itarmy`
- Кількість потоків: `-t XXXX` - за замовчуванням 8000 (або 4000 якщо на машині лише 1 CPU)
- Запуск декількох копій: `--copies X` або `--copies auto`, при наявності 4+ CPU та мережі 100+ Mb/s

### 4. 📌 Допомогти в пошуку нових проксі для mhddos_proxy
Сам скрипт та інструкції по встановленню тут: https://github.com/porthole-ascend-cinnamon/proxy_finder

### 5. 🐳 Комьюніті
- [Створення ботнету з 30+ безкоштовних та автономних(працюють навіть при вимкненому ПК) Linux-серверів](https://auto-ddos.notion.site/dd91326ed30140208383ffedd0f13e5c)
- [Детальний розбір mhddos_proxy та інструкції по встановленню](docs/installation.md)
- [Аналіз засобу mhddos_proxy](https://telegra.ph/Anal%D1%96z-zasobu-mhddos-proxy-04-01)
- [Приклад запуску через docker на OpenWRT](https://youtu.be/MlL6fuDcWlI)
- [VPN](https://auto-ddos.notion.site/VPN-5e45e0aadccc449e83fea45d56385b54)
- [Docker-image](https://github.com/alexnest-ua/auto_mhddos_alexnest/tree/docker), який запускає одночасно mhddos_proxy та [proxy_finder](https://github.com/porthole-ascend-cinnamon/proxy_finder) (для Linux / Mac додайте sudo на початку):
- [Налаштування з нотифікаціями у Телеграм](https://github.com/sadviq99/mhddos_proxy-setup)

### 6. CLI

    usage: runner.py target [target ...]
                     [-t THREADS] 
                     [-c URL]
                     [--debug]
                     [--vpn]
                     [--http-methods METHOD [METHOD ...]]
                     [--itarmy]
                     [--copies COPIES]

    positional arguments:
      targets                List of targets, separated by space
    
    optional arguments:
      -h, --help             show this help message and exit
      -c, --config URL|path  URL or local path to file with targets list
      -t, --threads 8000     Number of threads (default is 8000 if CPU > 1, 4000 otherwise)
      --vpn                  Use both my IP and proxies. Optionally, specify a chance of using my IP (default is 2%)
      --proxies URL|path     URL or local path(ex. proxies.txt) to file with proxies to use
      --proxy [PROXY ...]    List of proxies to use, separated by spaces
      --http-methods GET     List of HTTP(L7) methods to use (default is GET).
      --itarmy               Attack targets from https://t.me/itarmyofukraine2022  
      --debug                Detailed log for each target
      --copies 1             Number of copies to run (default is 1). Use "auto" to set the value automatically
      --lang {en,ua}         Select language (default is ua)

### 7. Власні проксі

#### Командний рядок

Для того щоб вказати власний проксі (або декілька) через командний рядок, використовуйте опцію `--proxy`:

    python3 runner.py --proxy socks4://114.231.123.38:3065

Можна вказати декілька проксі розділених пробілом:

    python3 runner.py --proxy socks4://114.231.123.38:3065 socks5://114.231.123.38:1080

Якщо перелік проксей занадто великий, скористайтеся опцією передачі налаштувань через файл (дивіться наступний розділ).

#### Формат файлу (будь який на вибір):

    IP:PORT
    IP:PORT:username:password
    username:password@IP:PORT
    protocol://IP:PORT
    protocol://IP:PORT:username:password
    protocol://username:password@IP:PORT

де `protocol` може бути одним з 3-ох: `http`|`socks4`|`socks5`, якщо `protocol`не вказувати, то буде обрано `http`  
наприклад для публічного проксі `socks4` формат буде таким:

    socks4://114.231.123.38:3065

а для приватного `socks4` формат може бути одним з таких:

    socks4://114.231.123.38:3065:username:password
    socks4://username:password@114.231.123.38:3065
  
**URL - Віддалений файл для Python та Docker**

    --proxies https://pastebin.com/raw/UkFWzLOt

де https://pastebin.com/raw/UkFWzLOt - ваша веб-сторінка зі списком проксі (кожен проксі з нового рядка)  
  
**path - Шлях до локального файлу, для Python**
  
Покладіть файл у папку з `runner.py` і додайте до команди наступний параметр (замініть `proxies.txt` на ім'я свого файлу)

    --proxies proxies.txt

де `proxies.txt` - ваша ваш файл зі списком проксі (кожен проксі з нового рядка)
