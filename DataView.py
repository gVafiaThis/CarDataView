import base64
import sys
import os
import io
import bokeh
from bokeh.models import ColumnDataSource,FileInput,TextInput, MultiChoice, Panel,Tabs, CheckboxGroup, Button,CrosshairTool,HoverTool,PreText,Toggle, Slider, RangeSlider
from bokeh.plotting import curdoc
from bokeh.layouts import layout,Spacer,row
from bokeh.palettes import Category10_10
from bokeh.server.server import Server
import pandas as pd
from functionsNew_v8 import MapChart_new,DatachartList_new,dataimport_filename,dataimport,datachart_new,inf_colorpick,plot_map,plot_chart,SimpleDataTab,datatransform_rotate
import numpy as np
import statistics
import re #for regex recognision in text input

#0.2 Changelog-> Make MultiChoice for plots appering/disappearing.
#0.3 Changelog-> Add your data with Fileinput - On Open, Loads Lap1.
#0.35 Changelog-> Start with blank page. Import file and then stuff appears in tabs. Major Redisign. Addeed the concept of current_sources(active source)
#0.36 Changelog -> Step to add Capability to use multiple sources on a tab. Added the concept of many current_sources on current Tab. 
#0.37 Changelog -> Change of basic functions in New functions v2 to support multiple sources on a tab. Current_source became Current_sources and now is a list.
#                  Changed names in multi select to be the first source's column names 
#0.371 Changelog -> Redisign. Sources,ChartIDs,MapIDs are saved on dict tabs_contents. DataTab now takes a source as input. 
#0.38 Changelog -> Add Checkbox group to hide plots in the same tab. Add Comments. Hide map with checkbox also
#0.39 Changelog -> imports cleanup
#0.4 Changelog -> add colors to plots. Works finally. Got Hide/Show Checkbox to the right of everythin
#0.5 Changelog -> Using functionsNew_v4 -> Plots on add source happen with new functions. 
#0.6 Changelog -> Starts from python file
#0.7 Changelog -> Try to close. Failed. wasted time. starts with bokeh serve again
#0.8 Changelog ->Layout made a bit better. Add common croshair and (not common)tooltip to all plots. add linked zooming
#0.85 Changelog ->cosmetic stuff. Remove ticks from map. Added Datetimeimport option
#0.86 Changelog -> toggle for datetime import. Removed Tooltip. Was now working proprely. Is Slow in add_source, have to find why
#0.87 Changelog -> Left it here. Didnt do Delete Tab
#0.88 Changelog -> Add Delete Tab. Added map plot hide functionality if map has a tile renderer in it
#0.9 Changelog -> FunctionsNew_v6 with simple visualization function. Restructure the way code is written with regions. Add Data Slicer. Add Misalignment Correction
#0.91 Changelog -> FunctionsNew_v7 add datatransform_rotate function and implement into misalignment functions here. 
#0.915 Changelog -> HUGE CHANGE: Save unchanged to mercator Lat&Long to source. The lats&longs you plot are now Lat_converted,Long_converted
#                   Add Lap_Splitter with written time in seconds. 
#0.916 Changelog -> Standalone Document,  
#0.917 Changelog -> Read csv from wherever. Change in DataTab to include fileinput ID in tabs_contents to find fileinput.value.
#0.92 Changelog -> Fixing bugs. 
#                   Removed og read_csv from all assistant functionalities because we now read files from everyhere in the system. 
#0.921              Misalignment LongVert gives opposite longitudinal data to Misalignment ALL. Changed it so that right hand rule is followed, x - lateral, y-longitudinal, z- vertical(lookingDown). added a minus to np.cross.


#-----------------------------------Functions For Tab Layouts-----------------------------------
def DataTab(source):
    #Creates the layout of a DataTab.
    #source is columndatasource
    default_plots = ['gFx','gFy']
    
    #\\\\\\Create Map Chart with plotted data - Figure
    map = MapChart_new(source,10.0)#MapChart_new works with columndatasources. Creates a Map with the car route plotted

    #\\\\\\Create DataCharts with plotted data - Column (bokeh figure Container)    
    charts = DatachartList_new(default_plots,[source])#Datachartlist_new works with lists. #Creates the Data Chart container and some default charts
    for chart in charts.children: #add the common croshair& hover tip?
        chart.add_tools(crosshair)
        if chart != charts.children[0]:
            chart.x_range = charts.children[0].x_range #Linked zooming and panning 
    global x_range 
    x_range = charts.children[0].x_range
    #\\\\\\Multi Selector - Widget
    #Choose which data charts to show. 
    #The data charts available for all sources in the tab are only the ones available in the first source, that is plotted here.
    multioptions = [opt for opt in source.column_names if not 'Unnamed' or not 'time' or not 'index' in opt] #Names of data chart options to plot. Taken from Data source column names.  
    multi = MultiChoice(value = default_plots, options = multioptions, height = 100) #Create Widget
    multi.on_change('value',updateplots) #Create Callback 
    
    #\\\\\\File Input: Add source data to tab for comparison - Widget
    add = FileInput( height = 100) #Create Widget
    add.on_change('filename',add_source_to_tab) #Create Callback

    #\\\\\\Add CheckboxGroup to show/hide source data in plots in tab
    cbut = CheckboxGroup(labels = [source.name[:-4]+' time:'+str(round(source.data['time'][-1],2))], active = [0], width = 60, sizing_mode = 'stretch_height') #Create Widget
    cbut.on_change('active',hider) #Create Callback

    #\\\\\\Add Delete Tab Button
    delbut = Button(label = 'X',width = 10, height = 40,sizing_mode = 'fixed',button_type = "danger")
    delbut.on_click(delete_tab)

    #\\\\\\Spacer for Layout
    spaceright = Spacer(width = 10, sizing_mode = 'fixed')

    #\\\\\\Create Layout
    rosw = row([map,charts,cbut,spaceright])
    lay = layout([add,toggle_datetime,multi,delbut,spaceright],rosw,name = 'mainLayout',sizing_mode = 'stretch_width')

    #\\\\\\Return Layout and layout children's IDs, to easilly find them later if needed.
    return lay,charts.id,map.id,cbut.id,add.id

def Slicer(source): #Too Slow and Cumbersome for lap splitting 
    #A double slider whose range is the time range you view data. A text next to it has the laptime.  
    #Callbacks    
    def slice_data(a,b,range):
        timerange = range[1]-range[0]
        Laptime_display.text = "TimeRange:"+str(int(timerange//60))+':'+str(float(timerange-timerange//60*60))
        afig = curdoc().get_model_by_id(charts_id).children[0]
        new = source_static[source_static['time']<range[1]]
        new = new[new['time']>range[0]]
        afig.renderers[0].data_source.data = new
        # print(range)

    def Finish_Slicer():
        
        Done()
    source_static = pd.DataFrame(source.data) #This is the original data. Seperate varible beacuse source changes\
    # print(type(source))
    #layout and setting callbacks
    
    Slicer_widget = RangeSlider(start = source_static['time'][0], end = source_static['time'].iloc[-1], step = 0.1, value = (source_static['time'][0],source_static['time'].iloc[-1]))
    Slicer_widget.on_change('value',slice_data)
    layup,charts_id,map_id,cbut_id = SimpleDataTab([source])
    Save_and_Done_Button = Button(label = 'Done')
    Save_and_Done_Button.on_click(Finish_Slicer)
    Laptime_display = PreText(text="TimeRange:"+str(2),width=500, height=100)
    lay = layout([layup],[Save_and_Done_Button],[Slicer_widget,Laptime_display])
    

    return lay

def Misalignment_All(source):#Self Contained Layout & callbacks(except tab exit) for Misalignment All Axes    
    
    #Callbacks
    def Back_callback():
        back_button = curdoc().get_model_by_name('Back')
        back_button.visible = False
        zSelect_button = curdoc().get_model_by_name('zSelect')
        zSelect_button.visible = True
        # Done_button = curdoc().get_model_by_name('Done')
        Done_button.visible = False
    def Back2_callback():
        back_button2 = curdoc().get_model_by_name('Back2')
        back_button2.visible = False
        xSelect_button = curdoc().get_model_by_name('xSelect')
        xSelect_button.visible = True
        # Done_button = curdoc().get_model_by_name('Done')
        Done_button.visible = False
    def SaveSelectedZ():

        #Click Button. Save Data
        a_figure = curdoc().get_model_by_id(charts_id).children[0] #Find the cdsource. all plots have the same so you choose the first
        source = a_figure.renderers[0].data_source
        sel_indexes = source.selected.indices 
        global dataforz
        if len(sel_indexes)>0:
            dffromsource = pd.DataFrame.from_dict(source.data) #dataframe from dict of source's data
            
            dataforz = dffromsource.loc[sel_indexes,['gFx','gFy','gFz']] #indices selection on dataframe

            #Hide Save Selected Button and show Back Button
            zSelect_button = curdoc().get_model_by_name('zSelect')
            zSelect_button.visible = False
            back_button = curdoc().get_model_by_name('Back')
            back_button.visible = True
            xSelect_button = curdoc().get_model_by_name('xSelect')
            if not xSelect_button.visible:
                # done_button = curdoc().get_model_by_name('Done')
                Done_button.visible = True
    def SaveSelectedX():
        #Click Button. Save Data
        a_figure = curdoc().get_model_by_id(charts_id).children[0] #Find the cdsource. all plots have the same so you choose the first
        source = a_figure.renderers[0].data_source
        sel_indexes = source.selected.indices 
        global datafory
        if len(sel_indexes)>0:
            dffromsource = pd.DataFrame.from_dict(source.data) #dataframe from dict of source's data
            
            datafory = dffromsource.loc[sel_indexes,['gFx','gFy','gFz']] #indices selection on dataframe

            #Hide Save Selected Button and show Back Button
            xSelect_button = curdoc().get_model_by_name('xSelect')
            xSelect_button.visible = False
            back_button2 = curdoc().get_model_by_name('Back2')
            back_button2.visible = True
            zSelect_button = curdoc().get_model_by_name('zSelect')
            if not zSelect_button.visible:
                # done_button = curdoc().get_model_by_name('Done')
                Done_button.visible = True
    def Calc_Means_Rot_Matrix():
        Save_and_Exit_Button.visible = True
        Back_button.visible = False
        Back_button2.visible = False
        dataforz_np = dataforz.to_numpy()#dataframes to numpy arrays. 
        dataforx_np = datafory.to_numpy()#dataframes to numpy arrays.
        mag_dataforz = np.array([np.linalg.norm(v) for v in dataforz_np])
        mag_dataforx = np.array([np.linalg.norm(v) for v in dataforx_np])
        #normalized values for data for misalignment calc 
        normalizedx_dataforz = [vector/magnitude for vector,magnitude in zip(dataforz['gFx'],mag_dataforz)]
        normalizedx_dataforx = [vector/magnitude for vector,magnitude in zip(datafory['gFx'],mag_dataforx)]
        normalizedy_dataforz = [vector/magnitude for vector,magnitude in zip(dataforz['gFy'],mag_dataforz)]
        normalizedy_dataforx = [vector/magnitude for vector,magnitude in zip(datafory['gFy'],mag_dataforx)]    
        normalizedz_dataforz = [vector/magnitude for vector,magnitude in zip(dataforz['gFz'],mag_dataforz)]
        normalizedz_dataforx = [vector/magnitude for vector,magnitude in zip(datafory['gFz'],mag_dataforx)]
        #the mean from the normalized values create the new z and x axis(np vectors), compensating for misalignment calibration.     
        newz = np.array([statistics.mean(normalizedx_dataforz),statistics.mean(normalizedy_dataforz),statistics.mean(normalizedz_dataforz)])
        newy = np.array([statistics.mean(normalizedx_dataforx),statistics.mean(normalizedy_dataforx),statistics.mean(normalizedz_dataforx)])
        # newx = np.array([1,0,0]) #Decided to only correct misalignment on long/vertical axes.

        #DONT FORGET that newy has the effect of 1g in newz in it at this point. So we remove
        newy = newy-newz

        #Creative mathematics. Make it perfecty perpendicular to newz
        newy = newy - np.inner(newy,newz)*newz
        #but now its magnitude is not 1 so we make it. 
        newy = (1/np.linalg.norm(newy))*newy

        #Find the new x axis. 
        newx = np.cross(newy,newz)
        # newy = newy * (1/np.linalg.norm(newy))
        #Rotation Matrix, since first Coordinate System is [[1,0,0],[0,1,0],[0,0,1]] is:
        global RotMatrix
        RotMatrix = np.array([newx,newy,newz])

        #Get source, Transform g data and plot them 
        a_figure = curdoc().get_model_by_id(charts_id).children[0] #Find the cdsource. all plots have the same so you choose the first
        source = a_figure.renderers[0].data_source #this is the data source. 
        dffromsource = pd.DataFrame.from_dict(source.data) #dataframe from dict of source's data
        g_data_array = dffromsource[['gFx','gFy','gFz']].to_numpy()
    
        rotated_gData_array = np.inner(g_data_array,RotMatrix)
        rotated_gData_df = pd.DataFrame(rotated_gData_array,columns =['gFx','gFy','gFz'] )
        rotated_gData_df['time'] = dffromsource['time']
        
        rotateddata_source = ColumnDataSource(rotated_gData_df)
        #Plot Stuff on existing figures 
        figures = curdoc().get_model_by_id(charts_id).children
        for fig,data in zip(figures,['gFx','gFy','gFz']): 
            fig.line(x = "time", y = data, source = rotateddata_source, line_width = 2.5, line_color = 'red' )
    def exit():
        # print(source.name)
        try:
            os.mkdir('./Logs/')
        except:
            pass
        df_source = pd.DataFrame(source.data)

        # og = pd.read_csv(source.name) #load original data to get original latitude longitude


        keys = [['gFx','gFy','gFz'],['Pitch','Roll','Azimuth'],['wx','wy','wz']]
        function_transformed = datatransform_rotate(df_source,RotMatrix,keys)
        function_transformed[['Speed (m/s)','Latitude','Longitude','time']] = df_source[['Speed (m/s)','Latitude','Longitude','time']]
        function_transformed.to_csv('./Logs/'+source.name[:-4]+'_Transformed_All.csv')
        Done()
    
    #Layout 
    layup,charts_id,map_id,cbut_id = SimpleDataTab([source])    
    zSelect_button = Button(label = 'Select Data - Stationary', name = 'zSelect')
    zSelect_button.on_click(SaveSelectedZ)
    Back_button = Button(label = 'ReselectZ', name = 'Back', visible = False)
    Back_button.on_click(Back_callback)
    xSelect_button = Button(label = 'Select Data - Straight', name = 'xSelect', visible = True )
    xSelect_button.on_click(SaveSelectedX)
    Back_button2 = Button(label = 'ReselectX', name = 'Back2', visible = False)
    Back_button2.on_click(Back2_callback)
    Done_button = Button(label = 'Calculate Transformation Matrix', name = 'Done', visible = False)
    Done_button.on_click(Calc_Means_Rot_Matrix)
    Save_and_Exit_Button = Button(label = 'Save as csv and exit', name = 'S&E', visible = False)
    Save_and_Exit_Button.on_click(exit)
    Cancel_Button = Button(label = 'Cancel', name = 'Cancel')
    Cancel_Button.on_click(Done)
    lay = layout([layup,zSelect_button,Back_button,xSelect_button,Back_button2,Done_button,Save_and_Exit_Button,Cancel_Button])

    return lay

def Misalignment_LongVert(source):#Self Contained Layout & callbacks(except tab exit) for Misalignment on long/vert Axes
    #Callbacks
    def Back_callback():
        back_button = curdoc().get_model_by_name('Back')
        back_button.visible = False
        zSelect_button = curdoc().get_model_by_name('zSelect')
        zSelect_button.visible = True
        Done_button.visible = False

    def SaveSelectedZ():

        #Click Button. Save Data
        a_figure = curdoc().get_model_by_id(charts_id).children[0] #Find the cdsource. all plots have the same so you choose the first
        source = a_figure.renderers[0].data_source
        sel_indexes = source.selected.indices 
        global dataforz
        if len(sel_indexes)>0:
            dffromsource = pd.DataFrame.from_dict(source.data) #dataframe from dict of source's data
            
            dataforz = dffromsource.loc[sel_indexes,['gFx','gFy','gFz']] #indices selection on dataframe

            #Hide Save Selected Button and show Back Button
            zSelect_button = curdoc().get_model_by_name('zSelect') #not needed
            zSelect_button.visible = False
            back_button = curdoc().get_model_by_name('Back') #Not Needed, since SaveSelectedZ is nested inside Misalignment_bla and Back_button is a var in Misalignment_Bla
            back_button.visible = True
            Done_button.visible = True

    def Calc_Means_Rot_Matrix():
        Save_and_Exit_Button.visible = True
        Back_button.visible = False
        dataforz_np = dataforz.to_numpy()#dataframes to numpy arrays. 
        mag_dataforz = np.array([np.linalg.norm(v) for v in dataforz_np])
        #normalized values for data for misalignment calc 
        normalizedx_dataforz = [vector/magnitude for vector,magnitude in zip(dataforz['gFx'],mag_dataforz)]
        normalizedy_dataforz = [vector/magnitude for vector,magnitude in zip(dataforz['gFy'],mag_dataforz)]
        normalizedz_dataforz = [vector/magnitude for vector,magnitude in zip(dataforz['gFz'],mag_dataforz)]
        #the mean from the normalized values create the new z and x axis(np vectors), compensating for misalignment calibration.     
        newz = np.array([statistics.mean(normalizedx_dataforz),statistics.mean(normalizedy_dataforz),statistics.mean(normalizedz_dataforz)])
        newx = np.array([1,0,0]) #Decided to only correct misalignment on long/vertical axes.

        #DONT FORGET that newy has the effect of 1g in newz in it at this point. So we remove




        #Find the new y axis. 
        newy = -np.cross(newx,newz)
        # newy = newy * (1/np.linalg.norm(newy))
        #Rotation Matrix, since first Coordinate System is [[1,0,0],[0,1,0],[0,0,1]] is:
        global RotMatrix
        RotMatrix = np.array([newx,newy,newz])

        #Get source, Transform g data and plot them 
        a_figure = curdoc().get_model_by_id(charts_id).children[0] #Find the cdsource. all plots have the same so you choose the first
        source = a_figure.renderers[0].data_source #this is the data source. 
        dffromsource = pd.DataFrame.from_dict(source.data) #dataframe from dict of source's data
        g_data_array = dffromsource[['gFx','gFy','gFz']].to_numpy()
    
        rotated_gData_array = np.inner(g_data_array,RotMatrix)
        rotated_gData_df = pd.DataFrame(rotated_gData_array,columns =['gFx','gFy','gFz'] )
        rotated_gData_df['time'] = dffromsource['time']
        
        rotateddata_source = ColumnDataSource(rotated_gData_df)
        #Plot Stuff on existing figures 
        figures = curdoc().get_model_by_id(charts_id).children
        for fig,data in zip(figures,['gFx','gFy','gFz']): 
            fig.line(x = "time", y = data, source = rotateddata_source, line_width = 2.5, line_color = 'red' )
    
    def exit():
        # print(source.name)
        try:
            os.mkdir('./Logs/')
        except:
            pass
        df_source = pd.DataFrame(source.data)

        # og = pd.read_csv(source.name) #load original data to get original latitude longitude

        keys = [['gFx','gFy','gFz'],['Pitch','Roll','Azimuth'],['wx','wy','wz']]
        function_transformed = datatransform_rotate(df_source,RotMatrix,keys)
        function_transformed[['Speed (m/s)','Latitude','Longitude','time']] = df_source[['Speed (m/s)','Latitude','Longitude','time']]
        function_transformed.to_csv('./Logs/'+source.name[:-4]+'_Transformed_Long-Vert.csv')

        Done()
    
    #Layout 
    layup,charts_id,map_id,cbut_id = SimpleDataTab([source])    
    zSelect_button = Button(label = 'Select Data - Stationary', name = 'zSelect')
    zSelect_button.on_click(SaveSelectedZ)
    Back_button = Button(label = 'ReselectZ', name = 'Back', visible = False)
    Back_button.on_click(Back_callback)
    Done_button = Button(label = 'Calculate Transformation Matrix', name = 'Done', visible = False)
    Done_button.on_click(Calc_Means_Rot_Matrix)
    Save_and_Exit_Button = Button(label = 'Save as csv and exit', name = 'S&E', visible = False)
    Save_and_Exit_Button.on_click(exit)
    Cancel_Button = Button(label = 'Cancel', name = 'Cancel')
    Cancel_Button.on_click(Done)
    lay = layout([layup,zSelect_button,Back_button,Done_button,Save_and_Exit_Button,Cancel_Button])

    return lay

def Lap_Splitter(source): #Self Contained Layout & Callbacks(except tab exit( Done() )) for Lap splitter with text input. 
    #Set up contained Callbacks
    def Laptime_Create(a,b,laptime_input):
        list_of_matches = re.findall("\d\d\:\d\d\.\d\d\d", laptime_input)
        list_of_matches2 = re.findall("\d\d\d\.\d\d\d", laptime_input)
        global laptime
        if  len(list_of_matches)>0:
            Wrong_Input.text = """           """
            laptime = 60*float(list_of_matches[0][0:2]) + float(list_of_matches[0][3:])
            Split_Button.visible = True
        
           
            
        elif len(list_of_matches2)>0:
            Wrong_Input.text = """           """            
            laptime = float(list_of_matches2[0])
            Split_Button.visible = True
        

        else:
            Wrong_Input.text = """Wrong Input"""
            laptime = 0
            Split_Button.visible = False
    def Lap_Slice():
        global counter
        a_figure = curdoc().get_model_by_id(charts_id).children[0] #Find the cdsource. all plots have the same so you choose the first
        plotsource = a_figure.renderers[0].data_source #this is the data source. 
        
        #Make Dir to Sava Lap Files 
        try:
            os.mkdir('./Logs')
            os.mkdir('./Logs/'+source.name[:-4]+'-Laps')
        except:
            print('Dir Not created')
            pass        
         
        #set Lap Data to save & remaining data
        source_remaining = pd.DataFrame(plotsource.data) #Get remaining data
        if Cut_From_Back.active == True:
            to_save = source_remaining[source_remaining['time']>source_remaining['time'].iloc[-1]-laptime]
            #Set to_save time data to start from 0 
            del to_save['index']
            to_save.index = range(len(to_save.index))
            newtime = to_save['time']-to_save['time'].loc[1] #Must Make new var. 
            to_save['time'] = newtime
            
            source_remaining = source_remaining[source_remaining['time']<=source_remaining['time'].iloc[-1]-laptime]
        else:
            to_save = source_remaining[source_remaining['time']<=laptime]
            source_remaining = source_remaining[source_remaining['time']>laptime]
        
        #Save Data to be saved
        to_save.to_csv('./Logs/'+source.name[:-4]+'-Laps/'+source.name[:-4]+'-Lap'+str(counter)+'.csv')

        #Reformat remaining data for correct index         
        del source_remaining['index']
        source_remaining.index = range(len(source_remaining.index))        
        

        #Offset time for remaining data so it starts from 0 
        newtime = source_remaining['time']-source_remaining['time'].loc[1] #Must Make new var. 
        source_remaining['time'] = newtime     

        #Update Lap Counter
        counter = counter + 1


        
        #Update Plots
        plotsource.data = source_remaining
        Split_Button.visible = False

    def Finish_Slicing():
        try:
            os.mkdir('./Logs/'+source.name[:-4]+'-Laps')
        except:
            pass   
        a_figure = curdoc().get_model_by_id(charts_id).children[0] #Find the cdsource. all plots have the same so you choose the first
        plotsource = a_figure.renderers[0].data_source #this is the data source.
        plotsource_df = pd.DataFrame(plotsource.data)
        plotsource_df.to_csv('./Logs/'+source.name[:-4]+'-Laps/'+source.name[:-4]+'-Remaining.csv')
        Done()
    
    #Create dfs of data.
    source_static_all = pd.DataFrame(source.data) #Dataframe of All Data
    # source_remaining = pd.DataFrame(source.data)
     #Dataframe of remaining data, after removal of Laps you splitted. 
    
    #Lap Counter
    global counter
    counter = 1
    #Create widgets & Data 
    layup,charts_id,map_id,cbut_id = SimpleDataTab([source])
    Done_Button = Button(label = 'Done')
    Done_Button.on_click(Finish_Slicing)
    Cut_From_Back = Toggle(label = 'Toggle to Split lap from the end')
    Split_Button = Button(label = 'Split Lap', visible = False)
    Split_Button.on_click(Lap_Slice)
    LapTime_input = TextInput(title = "Insert Laptime in seconds (e.g. 432.111) OR in mm:ss.sss format. (e.g 01:37.500)")
    LapTime_input.on_change('value',Laptime_Create)
    Wrong_Input = PreText(text = """           """)
    Cancel_Button = Button(label = 'Cancel')
    Cancel_Button.on_click(Done)
    lay = layout([layup],[LapTime_input],[row(Done_Button,Cut_From_Back,Split_Button,Wrong_Input)],[Cancel_Button])
    return lay


#--------------------------------Callback Functions for Widgets-----------------------------------
#Callback functions triggered on_change of a widget must have (attr,old,new) style inputs.
#old is before the change, new is new data of widget(e.g. a filename in a FileInput)

#region Start Page & General Callbacks
def input_file_newdatatab(attrname,old,name): 
    #CallBack to StartTab File Input. 
    #Creates a DataTab with some new data.
    #------------------------------------------------------------------
    file_bytes = base64.b64decode(fileinput.value)
    file = io.BytesIO(file_bytes)
    if toggle_datetime.active == True:
        source = dataimport(file,name,'DateTIMMMEEEE~')
    else:
        source = dataimport(file,name)
    layout,chartID,mapID,toggleID,fileinputID = DataTab(source) #Get the layout for the new tab
    TabsModel = curdoc().get_model_by_name('Tabs')#Get the Tabs object

    NewTab_name = "Tab "+str(len(TabsModel.tabs))#New Tab Name     
    NewTab = Panel(child = layout, title = NewTab_name)#Make the New Tab with the Layout from DataTab    
    TabsModel.tabs.append(NewTab) #Add New Tab To Tabs' object tabs list
    tabs_contents[NewTab_name] = {'sources': [source],'chartID': chartID,'mapID': mapID,'toggleID': toggleID, 'fileinputID': fileinputID} #INDEX for everything on every tab.
    TabsModel.active = (len(TabsModel.tabs)-1) #switch Tab to New One
    
def tabchange_setcurrents(attr,old,new): 
    #Callback to Tab change in UI.
    #Set current_tab global variable when switching to a tab. 
    #Is the basis for finding objects. Works in conjucntion with tabs_contents dict. 
    #------------------------------------------------------------------
    global current_tab
    current_tab = new  #Variable to know which Plots to Delete/Create in updateplots
    TabsModel = curdoc().get_model_by_name('Tabs')
    TabName = TabsModel.tabs[new].title

def delete_tab():
    TabName = TabsModel.tabs[current_tab]
    TabsModel.active = 0
    TabsModel.tabs.remove(TabName)

def dt_toggle(a,s,d):
    pass
#endregion

#region DataTab Callbacks
def updateplots(attrname,old,new): 
    #CallBack to Multi Selector in DataTab
    #Deletes ands creates plots in Data Chart Container in current tab. 
    #------------------------------------------------------------------
    TabName = TabsModel.tabs[current_tab].title #Find current tab name to get object IDs
    if len(old)<len(new): #Addition of plot       
        newlabel = new[-1] #new is a list with the new plot names. Find the latest addition (str) 
        charts_column = curdoc().get_model_by_id(tabs_contents[TabName]['chartID']) #Get column(bokeh figure container) that datacharts belong to
        newchart = datachart_new(newlabel,tabs_contents[TabName]['sources'],x_range)
        charts_column.children.append(newchart) #Add new plot to the datachart column
        newchart.add_tools(crosshair)


    elif len(old)>len(new):
        labeltoremove = list(set(old).difference(new))[0] #a way to get the diferent string in 2 lists that only have 1 different string 
        charts_column = curdoc().get_model_by_id(tabs_contents[TabName]['chartID']) #Get column(bokeh plot container) that dataplots belong to 
        for plot in charts_column.children: #find plot with label you want to remove. charts_column.children are figures. 
            if plot.name == labeltoremove:
                charts_column.children.remove(plot)#remove it

def add_source_to_tab(attrname,old,name):
    #Callback to Fileinput in DataTab
    #Adds another source's data to current tab. 
    #------------------------------------------------------------------
    TabName = TabsModel.tabs[current_tab].title #Find current tab name to get object IDs

    #\\\\\\Import New Data and Add it to tab contents
    TabFileInput = curdoc().get_model_by_id(tabs_contents[TabName]['fileinputID'])
    file_bytes = base64.b64decode(TabFileInput.value)
    file = io.BytesIO(file_bytes)

    if toggle_datetime.active == True:
        source = dataimport(file,name,'DateTIMMMEEEE~')
    else:
        source = dataimport(file,name)
    #import new data (new is a filename in python path)
    tabs_contents[TabName]['sources'].append(source) #Add the new data source to the INDEX for tab contents.
    #This enables the creation and deletion of plots with updateplots() that have the new data.

    #\\\\\\Find Colors for selection and nonselection
    line_color,selection_color = inf_colorpick(len(tabs_contents[TabName]['sources']),Category10_10)
    

    #\\\\\\Plot new data on current tab's Map
    TabMap = curdoc().get_model_by_id(tabs_contents[TabName]['mapID']) #Find Map Opject for current tab
    plot_map(TabMap,source,line_color,selection_color)

    #\\\\\\Plot new data on current tab's existing charts 
    #For charts to be created later, the new data will be plotted from updateplots() because the new source has benn added to the tab's sources in th INDEX
    column = curdoc().get_model_by_id(tabs_contents[TabName]['chartID']) #Get Chart List Container from its id (stored in tabs_contents INDEX)
    for chart in column.children:
        plot_chart(chart,chart.name,source,line_color,selection_color) #slow ???<-----------------

    #\\\\\\Add New Source to the Show/Hide Checkbox Group
    cbox = curdoc().get_model_by_id(tabs_contents[TabName]['toggleID']) # Get CheckboxGroup Object
    cbox.labels.append(source.name[:-4]+' time:'+str(round(source.data['time'][-1],2))) #add a button with the name of the new source(added to the columndatasource in dataimport)
    cbox.active.append(len(cbox.labels)-1)

def hider(a,old,new): 
    #Callback to CheckboxGroup in DataTab.
    #Hide a source's data from Chart List on current Tab. A toggle button corresponds to each source 
    #new is a list with the currently pressed(active) toggle button indexes
    #------------------------------------------------------------------
    #Each source creates 2 renderers(line,circle) in each figure. So the index of the active button(new) has to be 2 indexes:
    #e.g. : First source's toggle is active and has index [0]. This corresponds to renderers [0]&[1] in each chart.
    #      Second source's toggle is active and has index [1]. This corresponds to renderers [2]&[3] in each chart e.t.c.
    visible_renderer_indexes = [2*x for x in new]+[2*x+1 for x in new] #Active toggle index -> Visible renderer indexes in each chart. 

    TabName = TabsModel.tabs[current_tab].title #Find current tab name to get IDs

    #\\\\\\Hide Chart plots 
    ChartList = curdoc().get_model_by_id(tabs_contents[TabName]['chartID']) #Find Chart List (bokehColumn) in Current Tab         
    for figure in ChartList.children: #For each figure(chart) in the Data Chart Container
        visible_renderers = [figure.renderers[x] for x in visible_renderer_indexes] #visible renderers = the ones whose toggle is active 
        hidden_renderers = list(set(figure.renderers).difference(visible_renderers)) #hidden renderers = the rest of the figure's renderers
        for renderers in visible_renderers:
                renderers.visible = True
        for renderers in hidden_renderers:
                renderers.visible = False
    
    #\\\\\\Hide Map Plots 
    MapFig = curdoc().get_model_by_id(tabs_contents[TabName]['mapID']) #Find Map Figure in current tab
    # This is a figure that has one plot for each source. So its simpler than the charts. 
    #check if there is a tile on the map. It should be the first of the renderers
    if isinstance(MapFig.renderers[0], bokeh.models.renderers.TileRenderer):
        visible_maprenderers = [MapFig.renderers[x+1] for x in new] #renderer[0] is tile so we hide and show renderers [1:] (new[0] is renderer[1])
        visible_maprenderers.append(MapFig.renderers[0]) #Add tile renderer to the visible ones
    else:
        visible_maprenderers = [MapFig.renderers[x] for x in new] #one plot-one source. plot[0] - source[0]. new has active sources(buttons)
    
    
    hidden_maprenderers =list(set(MapFig.renderers).difference(visible_maprenderers))
    for renderers in visible_maprenderers:
            renderers.visible = True
    for renderers in hidden_maprenderers:
            renderers.visible = False   
#endregion

# region Popup Tab Callbacks.
def Misalignment_All_Popup(): #Enter a Popup tab you cant exit, unless you press done button
    def inputfile_callback(a,b,name):
        file_bytes = base64.b64decode(inputfile.value)
        file = io.BytesIO(file_bytes)
        if toggle_datetime.active == True:
            source = dataimport(file,name,'DateTIMMMEEEE~')
        else:
            source = dataimport(file,name)
        lay = Misalignment_All(source)
        NewTab = Panel(child = lay ,title = 'HAHAHA')
        TabsModel.tabs[-1] = NewTab

    inputfile = FileInput(width = 230)
    inputfile.on_change('filename',inputfile_callback)
    Cancel_Button = Button(label = 'Cancel')
    Cancel_Button.on_click(Done)
    NewTab = Panel(child = row([inputfile,toggle_datetime,Cancel_Button]) ,title = 'HAHAHA')
    TabsModel.tabs.append(NewTab)
    old_activeTab = TabsModel.active
    TabsModel.active = (len(TabsModel.tabs)-1) #switch Tab to New One
    TabsModel.disabled = True

def Misalignment_LongVert_Popup(): #Enter a Popup tab you cant exit, unless you press done button
    def inputfile_callback(a,b,name):
        file_bytes = base64.b64decode(inputfile.value)
        file = io.BytesIO(file_bytes)
        if toggle_datetime.active == True:
            source = dataimport(file,name,'DateTIMMMEEEE~')
        else:
            source = dataimport(file,name)
        lay = Misalignment_LongVert(source)
        NewTab = Panel(child = lay ,title = 'HAHAHA')
        TabsModel.tabs[-1] = NewTab
    Cancel_Button = Button(label = 'Cancel')
    Cancel_Button.on_click(Done)    
    inputfile = FileInput(width = 230)
    inputfile.on_change('filename',inputfile_callback)
    NewTab = Panel(child = row([inputfile,toggle_datetime,Cancel_Button]) ,title = 'HAHAHA')
    TabsModel.tabs.append(NewTab)
    old_activeTab = TabsModel.active
    TabsModel.active = (len(TabsModel.tabs)-1) #switch Tab to New One
    TabsModel.disabled = True

def Slicer_Popup(): #Callback for Slicer Popup tab.

    if toggle_datetime.active == True:
        source = dataimport_filename('migelser.csv','DateTIMMMEEEE~')
    else:
        source = dataimport_filename('migelser.csv')
    Slicer_widget = Slider(start = 0, end = 10)
    layup = Slicer(source)
    lay = layout([layup])
    NewTab = Panel(child = lay,title = 'HAHAHA')
    TabsModel.tabs.append(NewTab)
    old_activeTab = TabsModel.active
    TabsModel.active = (len(TabsModel.tabs)-1) #switch Tab to New One
    TabsModel.disabled = True

def LapSplitter_Popup():
    def inputfile_callback(a,b,name):
        file_bytes = base64.b64decode(inputfile.value)
        file = io.BytesIO(file_bytes)
        if toggle_datetime.active == True:
            source = dataimport(file,name,'DateTIMMMEEEE~')
        else:
            source = dataimport(file,name)
        lay = Lap_Splitter(source)
        NewTab = Panel(child = lay ,title = 'HAHAHA')
        TabsModel.tabs[-1] = NewTab
    Cancel_Button = Button(label = 'Cancel')
    Cancel_Button.on_click(Done)
    inputfile = FileInput(width = 230)
    inputfile.on_change('filename',inputfile_callback)
    NewTab = Panel(child = row([inputfile,toggle_datetime,Cancel_Button]) ,title = 'HAHAHA')
    TabsModel.tabs.append(NewTab)
    old_activeTab = TabsModel.active
    TabsModel.active = (len(TabsModel.tabs)-1) #switch Tab to New One
    TabsModel.disabled = True

def NewTab_Popup(): #Enter a Popup tab you cant exit, unless you press done button
    a = Button(label = 'Return')
    a.on_click(Done)
    lay = layout([a])
    NewTab = Panel(child = lay,title = 'HAHAHA')
    TabsModel.tabs.append(NewTab)
    old_activeTab = TabsModel.active
    TabsModel.active = (len(TabsModel.tabs)-1) #switch Tab to New One
    TabsModel.disabled = True

def Done(): #Exit Popup
    TabsModel.disabled = False
    TabsModel.active = 0
    TabsModel.tabs.remove(TabsModel.tabs[-1])


#endregion

#-----------------------------------START&INPUTS-----------------------------------

tabs_contents = {} #INDEX for data sources and object ids(figures,figure containers,widgets) used in each tab.
                   #A dictionary that contains dictionaries
                   #For each tab{'sources': [source],'chartID': chartID,'mapID': mapID,'toggleID': toggleID,'FileInputID': FileInputID} 
#Universal Tools and Widgets 
crosshair = CrosshairTool(dimensions="height") # Common Croshair tool. Shared with Functions
toggle_datetime = Toggle(sizing_mode = 'fixed', label = 'DateTime Import Toggle') #Toggle for importing datetime files 
toggle_datetime.on_change('active',dt_toggle)


#-----------------------------------Create Start Page-----------------------------------
#Main Menu. Not in a function because some objects and variables are passed to the callback functions.
  
#region Main Menu Widgets and layout
#\\\\\\File Input
fileinput = FileInput(width = 230) #Create FileInput Widget
fileinput.on_change('filename',input_file_newdatatab)#Callback for FileInput - Creates new DataTab. 
pre = PreText(text="""This inputs files that have seconds as their time stamps""",
width=500, height=100)

#explainer for Datetime Toggle Button
predt = PreText(text="""Toggle this to input files that have datetime as their time stamps. Converts to seconds.
Accepts %H:%M:%S:%milisecond""",
width=500, height=100)

but_LapSplit = Button(label = 'Manual Lap Splitter')
but_LapSplit.on_click(LapSplitter_Popup)
but_Misalignment_ALL = Button(label = 'Misalignment Correction - All axes')
but_Misalignment_ALL.on_click(Misalignment_All_Popup)
but_Misalignment_longvert = Button(label = 'Misalignment Correction - Long-Vert axes')
but_Misalignment_longvert.on_click(Misalignment_LongVert_Popup)

SPlay = layout([fileinput,pre],[toggle_datetime,predt],[but_LapSplit,but_Misalignment_ALL,but_Misalignment_longvert])

StartTab = Panel(child = SPlay,title = "StartTab")#Create StartTab tab
TabsModel = Tabs(tabs = [StartTab] ,name = 'Tabs') #Create bokeh Tabs object -> Shared with functions
TabsModel.on_change('active',tabchange_setcurrents) #whenever you change a tab, the sources used in that tab become active(so you can change stuff)
#endregion

#Server Functions
def bkapp(doc):
    doc.add_root(TabsModel) # The Tabs are the root of the document.
    def cleanup_session(session_context):
    # This function executes when the user closes the session.
        print('Session Closed. Excecuting Server Shutdown')
        sys.exit()
    doc.on_session_destroyed(cleanup_session)


if __name__ == '__main__':
    server = Server({'/': bkapp}, num_procs=1)
    server.start()
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

#-----------------------------------Random Things For Testing-----------------------------------

# TabsModel.children.append(NewTab)
# print(TabsModel.active)
# print(tabs_contents)
# tabs_contents['NewTab_name'] = {'sources': [1]}
# print(len(tabs_contents['NewTab_name']['sources']))
# show(lay)
# def Closer():
#     print()
# doc.add_periodic_callback(Closer,2000)
# def cleanup_session(session_context):
#     # This function executes when the user closes the session.
#     pass

# doc.on_session_destroyed(cleanup_session)

#----------------------------------------- TO DO LIST -------------------------------------------------
#TO-DO: -(in each DataTab)Different colors for different plots in same tab - recolor visible? DONE
#       -datetime to time translator. DONE
#       -Phone misalignment correction. DONE
#       -Lap Splitting (from: Gps,Known Lap Times(known time starts at start/known time stops at end))
#       -(in each DataTab) Maths between channels
#       -Filter Data Dashboard with sliders and shit(like Origin).(learn FFT LowPass)
#       -All Data same sampling(do we have this?)
#       -OFFLINE version. DONE
#       -Save Document??(if you did maths for example)
#       -UpSample/DownSample 
#       -OpenGL&not OpenGL choice for rendering plots DONE - Non webGL SUCKS BALLS(slow)
#       -(in each DataTab)Map circles are colormapped to speed
#       -Rename csv Column names Dashboard(Idea: Give me existing names, I type the names i want. OR/AND Give me the names i want(default), i give existing csv's names that correspond to my defaults)
#       -Add Default maths(azimuth for example.)
#       -LiveStream Data
#       -(in each DataTab)Remove plot from DataTab
#       -https://github.com/bokeh/bokeh/blob/2.4.3/examples/howto/server_embed/standalone_embed.py
#       -G data for global coordinate system(remove roll,pitch rotations) & Path(or Distance) from accelerations
#
# TO-DO for V1:  -Lap splitting (Gps,WrittenLapTimesDone)
#               DONE-Phone Misalignment - File input 
#               DONE - Read files from anywhere
# TO DO soon: -Azimuth - handle it somehow. 
#            - G data for global coordinate system(remove roll,pitch rotations) 
#            - Labels: Have a config file that correlates custom labels to the ones used in the program. Maybe set gLateral,gLong etc for the labels and keys used in the program, and correlate these to the ones from the data csv with a config file that is loaded in dataimport. 
#            - on_event for plots in chart. Pan shows only peaks and valleys to speed up scrolling. Same for zoom. 
#            - Text somewhere that says values of plots in the point you are with the mouse. Like custom tooltip. Maybe CustomJS, Check customJS examples on bokeh site. 
# To do in time: -re write in holoviews for no lag with huge amounts of data. Sad... 
#                - Add track layout on map and save it. Turns, Straights etc like motec. Maybe do the track analysis thing with the speeds in each corner. 