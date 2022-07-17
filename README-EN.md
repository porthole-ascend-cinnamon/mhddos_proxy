## IT Army of Ukraine Official Tool

### ⚠️ Attention
From now on, for easy installation and protection against unauthorized use, mhddos_proxy will be distributed as an executable file.  
[Follow the link to get the instructions and download](https://github.com/porthole-ascend-cinnamon/mhddos_proxy_releases)    
All updates and access to the full proxy database will be available only in the new version.  
The public version (this repository) remains available, but will not receive new updates, except the critical.  
Additional explanations in the official IT Army channel: https://t.me/itarmyofukraine2022/479  
This step is necessary for our Victory. Glory to Ukraine!  

### Use flag `--lang en` to enable English translation

- Built-in proxy server database with a wide range of IPs around the world
- Possibility to set a huge number of targets with automatic load balancing
- A variety of different load-testing methods
- Effective utilization of your resources due to the asynchronous architecture

### ⏱ Recent updates

- **27.06.2022** Added Spanish localization - use flag `--lang es`
- **22.06.2022** Performance improvements. The `--debug` option is deprecated to avoid negative impact on performance
- **10.06.2022** Introduced `--proxy` option for providing custom proxies directly from command args
- **08.06.2022** Added `--copies auto` option to set the value automatically based on the resources available

### 1. 💽 Installation options

#### A) Windows installer https://itarmy.com.ua/instruction/#mhddos/#windows

#### B) Python (if it doesn't work, try `python` or `python3.10` instead of `python3`)

Requires [Python](https://www.python.org/downloads/) and [Git](https://git-scm.com/download/)

    git clone https://github.com/porthole-ascend-cinnamon/mhddos_proxy.git
    cd mhddos_proxy
    python3 -m pip install -r requirements.txt

#### C) Docker

Install and start Docker: https://docs.docker.com/desktop/#download-and-install

### 2. 🕹 Running

#### Python with automatic updates (if it doesn't work, try `python` or `python3.10` instead of `python3`)

    ./runner.sh python3 --itarmy

For [**Termux for Android**](https://telegra.ph/mhddos-proxy-for-Android-with-Termux-03-31) use:

    TERMUX=1 bash runner.sh python --itarmy -t 1000

#### Python (manual updates required) (if it doesn't work, try `python` or `python3.10` instead of `python3`)

    python3 runner.py --itarmy

#### Docker (for Linux, add sudo in front of the command)

    docker run -it --rm --pull always ghcr.io/porthole-ascend-cinnamon/mhddos_proxy:old --itarmy

#### Special considerations while running application under macOS

Running application under macOS, you may face system restriction, that looks like that
```
The total number of threads has been reduced to 206 due to the limitations of your system
```

In order to increase the number of allowed file handles, and number of threads, 
you should use the following commands from the root directory of a project:
(all commands under `sudo`)
```
sysctl -w kern.maxfiles=65536
sysctl -w kern.maxfilesperproc=65536
cp doc/limit.maxfiles.plist /Library/LaunchDaemons
chown root:wheel /Library/LaunchDaemons/limit.maxfiles.plist
launchctl load -w /Library/LaunchDaemons/limit.maxfiles.plist
launchctl limit maxfiles
```
and restart the system. After that, limitations will be removed.

### 3. 🛠 Configuration and options

All options can be combined and specified in any order

- Consider adding your IP/VPN to the attack (especially when running on dedicated server), add flag `--vpn`
- To use targets provided by IT Army of Ukraine (https://itarmy.com.ua/), add the `--itarmy` flag  
- Number of threads: `-t XXXX` - the default is 8000 (or 4000 if the machine has only one CPU).
- Number of copies: `--copies X` or `--copies auto` - in case you have 4+ CPU and stable network 100+ Mb/s

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

#### Application config file

For some users application configuration file is more comfortable to handle options.

Application config is usually located in the user home directory, full name `$HOME/.mhddos.json`. 
If present, the config overrides command-line defaults, but itself is overwritten by command-line params.
If does not exist, it does not affect application whatsoever.

For example, if our app config looks like
```json
{
  "itarmy": true,
  "lang": "UA",
  "threads": 2000
}
```
but if we call the runner with the keys 
```
python3 runner.py --itarmy --table --http-methods GET STRESS --threads 4000
```
command-line param `--threads` overrides config, and we start with 4000 threads.

For easy creation of the application config file, you can use `--save-config` option. 
If the user adds it in the command line (usually in the first run), the config file `$HOME/.mhddos.json` 
would be created with exactly the same parameters user launched the application with.

### 4. 🐳 Community (mostly in Ukrainian)
- [Detailed (unofficial) installation instructions](docs/installation.md)
- [Create a botnet of 30+ free and standalone Linux servers](https://auto-ddos.notion.site/dd91326ed30140208383ffedd0f13e5c)
- [Scripts with automatic install](https://t.me/ddos_separ/1126)
- [Analysis of mhddos_proxy](https://telegra.ph/Anal%D1%96z-zasobu-mhddos-proxy-04-01)
- [Example of running via docker on OpenWRT](https://youtu.be/MlL6fuDcWlI)
- [VPN](https://auto-ddos.notion.site/VPN-5e45e0aadccc449e83fea45d56385b54)
- [Setup with Telegram notifications](https://github.com/sadviq99/mhddos_proxy-setup)

### 5. Custom proxies

#### Command line

To specify custom proxy use `--proxy` option:

    python3 runner.py --proxy socks4://114.231.123.38:3065

Multiple proxies are allowed (space separated):

    python3 runner.py --proxy socks4://114.231.123.38:3065 socks5://114.231.123.38:1080

If the list of custom proxies gets too long, consider switching to file-based configuration (see the next section).

#### File format (any of the following):

    IP:PORT
    IP:PORT:username:password
    username:password@IP:PORT
    protocol://IP:PORT
    protocol://IP:PORT:username:password

where `protocol` can be one of 3 options: `http`|`socks4`|`socks5`. 
If `protocol` is not specified, default value `http` is used.
For example, for a public `socks4` proxy the format will be fhe following:

    socks4://114.231.123.38:3065

and for the private `socks4` proxy format can be one of the following:

    socks4://114.231.123.38:3065:username:password
    socks4://username:password@114.231.123.38:3065

**URL of the remote file for Python and Docker**

    --proxies https://pastebin.com/raw/UkFWzLOt

where https://pastebin.com/raw/UkFWzLOt is your web page with a list of proxies (each proxy should be on a new line)  

**Path for the local file for Python**  
  
Put the file in the folder with `runner.py` and add the following option to the command (replace `proxies.txt` with the name of your file)

    --proxies proxies.txt

where `proxies.txt` is your proxy list file (each proxy should be on a new line)
