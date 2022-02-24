
Before starting the Home Assistant installation, connect the your UPS USB port to the computer/hardware USB port  where Home Assistant is running.


To get started, go to **Settings**, click on **Add-ons, Backups and Supervisor**.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/i1.png" alt="Hass.io screen Add a new repository." width="700" /> 

Go to “**Add-on Store**” in the lower right corner.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/i2.png" alt="Hass.io screen Add a new repository." width="700" /> 

In the upper right corner menu choice **Repositories**.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/i3.png" alt="Hass.io screen Add a new repository." width="700" /> 

Fill with the *SmsUps* github address: https://github.com/dmslabsbr/smsUps/ and click **Add**.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/i4.png" alt="Hass.io screen Add a new repository." width="700" /> 

A new add-on will appear. Click on it.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/i5.png" alt="Hass.io screen Add a new repository." width="400" /> 

Click **Install**.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/i6.png" alt="Hass.io screen Add a new repository." width="600" /> 

After installation, if everything goes well, go to the **Configuration** option to configure before starting.



<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/i7.png" alt="Hass.io screen Add a new repository." width="600" /> 

**Before the 1st use you must configure the add-on, in the Configuration tab.**

- UPS_NAME and UPS_ID it is just a reference, if you have more than one UPS.
  
- SMSUPS_SERVER, set to true if your UPS was connected to the same machine as the Home Assistant.
  
- SMSUPS_CLIENTE, set it as true for the add-on to monitor the MQTT server and shut down the machine if necessary.
 
- PORTA, standard USB device port, usually **/dev/ttyUSB0**

- Allow_shutdown, Automatic shutdown the host when battery level drop by 30%.

- SHUTDOWN_CMD, commands used to shutdown the equipment. As there are differences between the systems, the add-on will try several options.


<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/i8.png" alt="Hass.io screen Add a new repository." width="600" /> 

- USE_SECRETS, setting it to **false**, the add-on will use this setting, if set to **true** it will use the setting in the *secrets.ini* file.

- Long_lived_access_token, **optional** parameter. You need to use if you like to receive notifications on Home Assistant web interface.  ([How to get Long Lived Access Token](https://github.com/dmslabsbr/smsUps/raw/master/longlived.md)).


### Don't forget to connect your UPS's USB port to the computer's USB port where the Home Assistant is running.

With everything configured and filled in, click Save.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/i9.png" alt="Hass.io screen Add a new repository." width="600" /> 

So, click on **Start**.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/ia1.png" alt="Hass.io screen Add a new repository." width="600" /> 

## Example:

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/hass5.png" alt="Hass.io screen Add a new repository." width="300" /> 

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/hass6.png" alt="Hass.io screen Add a new repository." width="300" /> 


### You can now use your UPS data in your Home Assistant.