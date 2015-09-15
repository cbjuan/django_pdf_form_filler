# Django PDF Form filler - Private Repository #

This Git repo contains the code of the Django PDF Form filler app developed by Juan Cruz-Benito

### Why to use it? ###

This web app enables users to fill PDF forms automatically, by combining PDF Forms with data contained in a CSV file. This application is highly recommended to automate the generation of certificates, accreditations or any other batch tasks of filling PDF forms.

### Libraries used in the code ###

* [pdfjinja](https://github.com/rammie/pdfjinja)
* [django-bootstrap3](https://github.com/dyve/django-bootstrap3)

### Some functionalities ###

* Generation of PDF Forms filled using CSV data
* One PDF per CSV row (now with no limitation of PDF amount to generate)
* The application returns a .zip file with all the PDFs generated
* The CSV, PDF form, PDFs generated and other files are deleted instantaneously from the server after the zip file download.

### Deploying application on Heroku ###

* Heroku reference deploying Django application - https://devcenter.heroku.com/articles/getting-started-with-django
* Installing PDFTK to enable PDF filling options (appart from using libraries included in requirements.txt) - http://iamsonivivek-pdftk.blogspot.com.es/