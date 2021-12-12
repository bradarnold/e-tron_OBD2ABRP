# e-tron_OBD2ABRP
Rough (around the edges) python script to connect a 2019 Audi e-tron to APRP.

**Note** Integration with ABRP not currently present :)

See https://abetterrouteplanner.com/

Leverages work from:
* EVNotify e-golf integration https://github.com/EVNotify/EVNotify/blob/master/app/www/components/cars/E_GOLF.vue
* List of OBD2 codes for the e-up https://www.goingelectric.de/wiki/Liste-der-OBD2-Codes/
* And hands-on work to determine the correct bytes and scaling values for the Audi e-tron

Tested with:
* 2019 Audi e-tron sold in the US market
* ODBLink MX paired with a Windows laptop
