# DataView_car

## Premise 
This project came to be after I asked myself the question: 
What could be the cheapest possible data aquisition system for a racecar? 

The answer is a smartphone. 

It gives you access to accelerations, rates, angles and positional data just by recording the phone's sensor values.
With some creative thinking, you could say that you get all of that for free (beacuse you already have the phone).
Just mount the phone securely near the center of gravity and you can get some data from your laps (or transform the data to the center of gravity (upcoming feature) ).

Already existing solutions for viewing car lap data are either very expensive or lack functionallity that I (at least) would require. \
So,this project started out as a dashboard, built with the bokeh library of python, for viewing and manipulating that data.\
In the process of developing the dashboard, the result became an interactive dashboard with some extra functionalities, 
all wrapped in a UI. 

## Overview


The fucntionalities of the package are presented below: 

- ***Data Tab***\
  Main functionality of the package: 
    - **_Create/Delete different channels_**, from the loaded data, using the channel selector
    - **_Add multiple sources of data_**, and view them simultaneously using the file browser (Import a .csv file)
    - **_Show/Hide sources of data_**, using the source hide checkbox
  
- ***Lap Splitting***\
  2 different ways: 
    - **_Manual Lap Splitting_**, if you know laptimes _from the moment you started/stopped recodring_ 
    - **_GPS Lap Splitting_**, draw the start/finish line on the map, and times are generated automatically

- ***Corrections for Misalignment***\
  These functionalities are for cases where the phone is misaligned to the car. They work based on the fact that the phone measures the acceleration from gravity. 
    - **_Longitudinal/Vertical Misalignment_**, the phone is mounted correctly as far as the lateral forces are concerned, but its 2 other axes are misaligned. Needs data from the car being stationary. 
    - **_All Axes Misalignment_**, The phone is completely misaligned. Needs data from the car being stationary and the car accelerating in a straight line. 


The dashboard plots data from the app [Physics Toolbox Sensor Suite](https://play.google.com/store/apps/details?id=com.chrystianvieyra.physicstoolboxsuite&hl=en&gl=US) and was tested with data gathered from android phones. \
But there shouldn't be an issue with getting the data from an iphone.\
The  way to mount the phone is with the screen facing upwards, and the top of the phone facing forwards.\ 
For now, the dashboard properly works with generated using Physics Toolbox, but soon it will work with any .csv with titles.

## Detailed Description

Coming Soon...
  
