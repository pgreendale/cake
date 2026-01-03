#Experiences with Heltec ESP32 V3, Remote GPIO
Setup of dev environment is done by following [this](https://meshtastic.org/docs/development/firmware/build/) manual by meshtastic, easy done on mac. 
Settings in the source for remote GPIO access are provided within the [Meshtastic Manual](https://meshtastic.org/docs/configuration/module/remote-hardware/). <br>

Additionally, I set 

```C
#define MESHTASTIC_EXCLUDE_REMOTEHARDWARE 0
``` 

in the <i>variants.h</i> in the variants subdirectory according to my device (esp32s3/heltec_v3) because as far as I (better VS Code) did find references, where the remote hardware is deactivated on minimal configuration but not where it is activated by default. 
## Electrical Connections 
* Telemetry: BME280 Temp+Pressur
	* SDA -> GPIO 41 
	* SCL -> GPIO 42 
* Relais_Control Card: 
	* 1 -> GPIO 34 
	* 2 -> GPIO 33
	* 3 -> GPIO 47
	* 4 -> GPIO 48 

The relais card is a cheap one from china with 5V support. The 3.3V output from the ESP32 is enough to set a H level. <br>


<b>Attention!</b> Some of these relais cards can be set for L active input by some jumpers. These would activate a 5V pullup on the input pins. Afaik is the esp not rated for 5V, so you <i>may</i> damage your ESP32. Please check before connecting the board to your Lora device.  
##Telemetry weirdness 
First, GPIOS doesnt seem to work, even with custom firmware. <br>
Using the meshtastic python module from console with directly attached node 

```console
foo@bar:~$ meshtastic --info
```

returns 

```json
  "remoteHardware":{
    "enabled": true,
    "allowUndefinedPinAccess": false,
    "availablePins": []
  }
```
revealed that <i>no</i> available pins are defined. I did check the configuration files but got no clue how to actually define available pins within a short glance. I set allowUndefinedPinAccess to <b>true</b> to cicumvent that with the node in question connected directly to the computer: 

```console
foo@bar:~$ meshtastic  --set remote_hardware.allowUndefinedPinAccess true
```
Disconnect the node from the computer and connect it to some other power source, like an USB charger.
<br>
###Testing
The local control node provides the <i>gpio</i> channel which is subscripted by the remote controlled node whose pins shall be remotely controlled. <br>

To test it, I am sending commands to the control node with the python module. The command node is directly attached to the computer via usb now: 

```console
foo@bar:~$ meshtastic  --gpio-wr 33 1 --dest <yournodeID>
```

```console
foo@bar:~$ meshtastic  --gpio-wr 33 0 --dest <yournodeID>
```

Switches a connected LED or relay driver (active H) on  and off again. 

### Test for connection: read metrics<br> 
An easy test if the node is connected is requesting its metrics. The destination node has a BME280 connected and telemetry [enabled](https://meshtastic.org/docs/configuration/module/telemetry/). 
The type of telemetry is not the default one, checking the [src](https://github.com/meshtastic/python/blob/master/meshtastic/__main__.py#L291) for meshtastic reveals 

```python
if checkChannel(interface, channelIndex):
                telemMap = {
                    "device": "device_metrics",
                    "environment": "environment_metrics",
                    "air_quality": "air_quality_metrics",
                    "airquality": "air_quality_metrics",
                    "power": "power_metrics",
                    "localstats": "local_stats",
                    "local_stats": "local_stats",
                }
``` 
as possible parameter names for \[Type\], so the used command is : 

```console
foo@bar:~$ meshtastic  --gpio-wr 33 1 --dest <yournodeID> 
```
I got something like this back : 

```console
Connected to radio
Sending environment_metrics telemetry request to <yournodeID> on channelIndex:0 (this could take a while)
Telemetry received:
environmentMetrics:
  temperature: 18.94
  barometricPressure: 987.247
```


