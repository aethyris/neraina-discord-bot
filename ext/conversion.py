from unitconvert import digitalunits
from unitconvert import lengthunits
from unitconvert import timeunits
from unitconvert import volumeunits
from unitconvert import massunits
from unitconvert import temperatureunits
import arrow
import googlemaps

def convertunits(x, output):
    """Converts a number into a different unit.\n
    Takes two string inputs where the first contains
    the number and unit, while the second contains the unit to convert to.\n
    This returns a list containing the new number, original number, initial unit, and converted unit."""

    # Keeps track of lower case units and lists for checking if units are valid
    digital = {'b':'B', 'kb':'kB', 'mb':'MB', 'gb':'GB', 'tb':'TB', 'pb':'PB', 'eb':'EB', 'zb':'ZB', 'yb':'YB', 'kib':'KiB', 'mib':'MiB', 'gib':'GiB', 'tib':'TiB', 'pib':'PiB', 'eib':'EiB', 'zib':'ZiB', 'yib':'YiB'}
    length = {'mm', 'cm', 'in', 'ft', 'yd', 'm', 'km', 'mi'}
    time = {'ms', 'sec', 'min', 'hr', 'day', 'wk', 'yr'}
    volume = {'ml', 'l', 'tsp', 'tbsp', 'floz', 'cup', 'pt', 'qt', 'gal', 'lcup', 'in3', 'ft3'}
    mass = {'mg', 'g', 'oz', 'lb', 'kg'}
    temperature = {'f':'F', 'c':'C', 'k':'K'}

    # Splits the number and unit
    num = 0
    unit = ''
    try:
        if len(x.split()) > 1:
            num = int(x.split()[0])
            unit = x.split()[1]
        else: # if its one word (e.g. 100kg)
            for i, c in enumerate(x):
                if not c.isdigit():
                    break
            num = int(x[:i])
            unit = x[i:]
    except:
        return [0, 0, '', '']

    # Uses unit convert and checks if the two units are in the same category
    if unit in digital and output in digital:
        return [digitalunits.DigitalUnit(num, digital[unit], digital[output]).doconvert(), num, digital[unit], digital[output]]
    elif unit in length and output in length:
        return [lengthunits.LengthUnit(num, unit, output).doconvert(), num, unit, output]
    elif unit in time and output in time:
        return [timeunits.TimeUnit(num, unit, output).doconvert(), num, unit, output]
    elif unit in volume and output in volume:
        return [volumeunits.VolumeUnit(num, unit, output).doconvert(), num, unit, output]
    elif unit in mass and output in mass:
        return [massunits.MassUnit(num, unit, output).doconvert(), num, unit, output]
    elif unit in temperature and output in temperature:
        return [temperatureunits.TemperatureUnit(num, temperature[unit], temperature[output]).doconvert(), num, temperature[unit], temperature[output]]
    else:
        return [0, 0, '', '']

def converttime(input):
    """Gives the local time of a specific address\n
    Uses googlemaps geolocation and arrow."""
    gmaps = googlemaps.Client(key='')
    geocode_result = gmaps.geocode(input)[0]['geometry']['bounds']['northeast']
    timezone = gmaps.timezone(geocode_result)['timeZoneId']
    return arrow.now(timezone).format('dddd, MMMM D, YYYY h:mm A in ') + timezone

def convertparse(input_txt):
    try:
        if input_txt[6:10] == 'unit':
            a = input_txt[11:].split(", ")
            converted = convertunits(a[0], a[1])
            if converted[3] == '':
                return "You messed up your inputs."
            else:
                return "{0} {1} is equal to {2} {3}.".format(str(converted[1]), str(converted[2]), str(converted[0]), str(converted[3]))

        elif input_txt[6:10] == 'time':
            return "It's {0} right now.".format(converttime(input_txt[11:]))

        elif input_txt[6:10] == 'tlcl':
            t = arrow.utcnow().shift(hours=+9).format('h:mm A')
            return "It's {0} in Korea".format(t)

        elif input_txt[6:10] == 'date':
            t = arrow.utcnow().shift(hours=+9).format('dddd, MMMM D, YYYY')
            return "Today is {0}.".format(t)

        else:
            return "Something went wrong and it's probably your fault."
    except:
        return "Something went wrong and it's probably your fault."
