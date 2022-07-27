# DataView_car

## Premise 
This project came to be after I asked myself the question: 
What could be the cheapest possible data aquisition system for a racecar? 

The answer is a smartphone. 

It gives you access to accelerations, rates, angles and positional data just by recording the phone's sensor values.\
With some creative thinking, you could say that you get all of that for free (beacuse you already have the phone).\
Just mount the phone securely near the center of gravity and you can get some data from your laps (or transform the data to the center of gravity (upcoming feature) ).

Already existing solutions for viewing car lap data are either very expensive or lack functionallity that I (at least) would require. \
So,this project started out as a dashboard, built with the bokeh library of python, for viewing and manipulating that data.\
In the process of developing the dashboard, the result became an interactive dashboard with some extra functionalities, 
all wrapped in a UI. 

## Overview
The whole thing runs in the browser. The fucntionalities of the package are presented below: 

- ### ***Data Tab***
  Main functionality of the package: 
    - **_Create/Delete different channels_**, from the loaded data, using the channel selector
    - **_Add multiple sources of data_**, and view them simultaneously using the file browser (Import a .csv file)
    - **_Show/Hide sources of data_**, using the source hide checkbox
    - **_Linked Selection Between Channels & Map_**, so the location of where something happened in the data is easy to determine
\
 _DataTab with one source._
![DATATAB_LargeData](https://user-images.githubusercontent.com/109922381/181355522-5217d984-861e-4060-b4e6-1de6deecda06.png)
\
_DataTab with multiple sources. _
![DATATAB_Explainer where everything is](https://user-images.githubusercontent.com/109922381/181355627-1931ad1e-77e6-4c70-a961-727b91d36595.png)


- ### ***Lap Splitting***
  2 different ways: 
    - **_Manual Lap Splitting_**, if you know laptimes _from the moment you started/stopped recodring_ 
    - 
    - **_GPS Lap Splitting_**, draw the start/finish line on the map, and times are generated automatically
\
_Manual Lap Splitting_
![ManualLapSplit](https://user-images.githubusercontent.com/109922381/181355713-9e7b58c7-5e94-4a3d-988d-4eed24be78db.png)
\
_Automated GPS Lap Splitting_ 
![GPS_LapSplitter](https://user-images.githubusercontent.com/109922381/181355739-6a1887d3-6a50-40cb-a6dd-7c7ce2d4841f.png)
\
- ### ***Corrections for Misalignment***
  These functionalities are for cases where the phone is misaligned to the car. They work based on the fact that the phone measures the acceleration from gravity. 
    - **_Longitudinal/Vertical Misalignment_**, the phone is mounted correctly as far as the lateral forces are concerned, but its 2 other axes are misaligned. Needs data from the car being stationary. 
    - **_All Axes Misalignment_**, The phone is completely misaligned. Needs data from the car being stationary and the car accelerating in a straight line. 
\
![Misalignment](https://user-images.githubusercontent.com/109922381/181356072-53a00ae2-49a1-4f70-bac6-11389dfb7009.png)


The dashboard plots data from the app [Physics Toolbox Sensor Suite](https://play.google.com/store/apps/details?id=com.chrystianvieyra.physicstoolboxsuite&hl=en&gl=US) and was tested with data gathered from android phones. \
But there shouldn't be an issue with getting the data from an iphone.\
The  way to mount the phone is with the screen facing upwards, and the top of the phone facing forwards.\ 
For now, the dashboard properly works with generated using Physics Toolbox, but soon it will work with any .csv with titles.

## Detailed Description
Coming Soon...
  
## Upcoming features
Coming Soon...

## How to Run
Click Green code button and download .zip . From there, run the .exe. \
In the sample data folder there are some (slow) laps of Serres Circuit, with the phone misaligned in the Long/Vert axes.\

For running from python, a requirements.txt is coming soon :) 


