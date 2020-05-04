## Interactive COVID-19 App

### URL
[hbap-analytics.com](https://hbap-analytics.com)

### Maps

---

Map section is an interactive US map showing COVID-19 cases by US County.

<img src="images/maps.PNG" width="500" alt="Maps"/>


### Trends

---

Trends section include interactive line graphs showing COVID-19 cases and deaths by State. In addition, it shows predicted cases and deaths for the next 15 days based on previous data for each State. You can select one or multiple States from the selection list on the left to compare trends.

<img src="images/trends.PNG" width="500" alt="Trends"/>

### Histograms

---

Histograms section is based on data released by the State of Florida Division of Emergency Management. It explores distributions of COVID-19 cases and deaths in different age and gender groups.

<img src="images/histograms.PNG" width="500" alt="Histograms"/>


### Models

---

Models section explores Florida COVID-19 death correlation with age, county density population, county land area, county water area, and county population using multiple classification models.

<img src="images/models.PNG" width="500" alt="Models"/>

### Running App Locally

1. Clone or download source files
2. From the *covid-master* directory, install required Python packages:
```
pip install -r requirements.txt
```
3. From the *app* directory, run app:
```
bokeh serve --show covid
```

### Data Sources

* [New York Times](https://www.nytimes.com/)
* [Florida Division of Emergency Management](https://floridadisaster.org/covid19/)
* [US Census Bureau](https://www.census.gov/)


### Technologies

* Python
* Python Packages
* Bokeh
* HTML
* JavaScript
* AJAX
* AI and ML
