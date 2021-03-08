# <img align="center" src="https://github.com/dmslabsbr/smsUps/raw/master/hass.io.png" alt="" width="60" />  smsUPS Home Assistant add-on instructions 

## 1 - Add a new repository

#### a) Inside *supervisor* tab, choice *Add-on store*.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/hass1.png" alt="Hass.io screen Add a new repository." width="500" /> 

#### b) Add the **URL** (https://github.com/dmslabsbr/smsUps) of the repository and then press "**Add**". 

<img src="https://github.com/dmslabsbr/smsUps/raw/master/hass2.png" alt="Hass.io screen Add a new repository." width="500" /> 

#### c) A new card for the repository will appear.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/hass3.png" alt="Hass.io screen Add a new repository." width="400" /> 

#### d) Click on the repository and proceed with add-on installation.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/hass4.png" alt="Hass.io screen Add a new repository." width="200" /> 

#### e) Before the 1st use you must configure the add-on, in the Configuration tab. Where:


- In MQTT_HOST, MQTT_USER and MQTT_PASS fields you need to enter your MQTT server access data.

- UPS_NAME and UPS_ID it is just a reference, if you have more than one UPS.
  
- SMSUPS_SERVER, set to true if your UPS was connected to the same machine as the Home Assistant.
  
- SMSUPS_CLIENTE, set it as true for the add-on to monitor the MQTT server and shut down the machine if necessary.
 
- PORTA, standard USB device port, usually **/dev/ttyUSB0**

- Allow_shutdown, Automatic shutdown the host when battery level drop by 30%.

- SHUTDOWN_CMD, commands used to shutdown the equipment. As there are differences between the systems, the add-on will try several options.

- USE_SECRETS, setting it to **false**, the add-on will use this setting, if set to **true** it will use the setting in the *secrets.ini* file.

- Long_lived_access_token, **optional** parameter. You need to use if you like to receive notifications on Home Assistant web interface.  ([How to get Long Lived Access Token](https://github.com/dmslabsbr/smsUps/raw/master/longlived.md)).

### Don't forget to connect your UPS's USB port to the computer's USB port where the Home Assistant is running.

## Example:


<img src="https://github.com/dmslabsbr/smsUps/raw/master/hass5.png" alt="Hass.io screen Add a new repository." width="200" /> 

<img src="https://github.com/dmslabsbr/smsUps/raw/master/hass6.png" alt="Hass.io screen Add a new repository." width="200" /> 

You can now use your UPS data in your Home Assistant.