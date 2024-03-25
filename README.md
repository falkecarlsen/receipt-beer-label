# Homebrewed beer label generator
Using a Samsung SRP-350G thermal receipt printer this project intends to generate and print a number of labels to be stuck to bottles of homebrewed beer.

Utilising `escpos` to interface with thermal receipt printers alongside `PIL` and `tabulate` to generate the label to be printed, this is achieved. 

Required is a 700x320px logo, a dict of descriptions of the beer, and the desired number of labels.
