# pysimepar

This a is python package to retrieve forecast data from Simepar (www.simepar.br). Since this package
tries to webscrape information from simepar webpage, small changes to that webpage may
break the parsing.


## Install

You may install it using pip:

    pip install pysimepar

## Usage

Import the packge in your code and instantiate the PySimepar class with your city code:

    from pysimepar import PySimepar
    s = PySimepar(4106902)

To retrieve the forecast data, just call the update method. The current condition, hourly_forecast and daily 
forecast will be at the class data dictionary:

    s.update()
    print(s.data)