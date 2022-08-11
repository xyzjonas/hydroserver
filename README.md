# Hydroserver #

![image](https://user-images.githubusercontent.com/10963153/133970728-844e82bf-ca50-44b0-8436-8051c48ecda5.png)

Flask based backend service for an automated hydroponics system. The entire system consists
of this backend service, [an Arduino client](https://github.com/jonasbrauer/hydro-client) and a
[Vue.JS based web interface (SPA)](https://github.com/jonasbrauer/hydroweb).

***

### Main features
* Register multiple clients (different systems - clients).
* Extendable client types/protocols (supported: Serial/USB, HTTP).
* Each device/client has its own:
  * **Sensors** (input) - e.g.: remaining tank capacity, pH levels,...
  * **Controls** (output) - e.g.: pump pumping power, light switches,...
  * **Tasks** (logic) - arbitrary logic scheduled/executed based on a CRON value.
* Tasks can be completely customized - system is easily extendable with a plugin system.
* Sensor values are tracked and their history is stored.

***

### How do I get set up? ###

Set up a development environment with a simple:

```sh
pip install -r requirements.txt
flask run
```

A simple deployment can be achieved with a supplied unit file and a web server as reverse proxy.
