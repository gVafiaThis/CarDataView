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
from bokeh.events import DoubleTap



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
            print('Logs Dir Created')
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
            print('Logs Dir Created')
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
            print('Logs Dir created')
        except:
            
            pass        
        try:
            os.mkdir('./Logs/'+source.name[:-4]+'-Laps')
            print('Laps Dir created')
        except:
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

def GPS_LapSplitter(source):
    """_----------------------------------------------------_CALLBACKS_----------------------------------------------------_"""
    def make2Points(event):
        Coords=[event.x,event.y]
        pointlist.append(Coords)
        MapGlyphs = mapPlot.renderers
        source_GPS = MapGlyphs[1].data_source# The source(ColumnDataSource) that contains the gps data. 
        dict_GPS = source_GPS.data #Get the dict of the data 
        df_GPS = pd.DataFrame.from_dict(dict_GPS)#Make Data a DataFrame
        if len(MapGlyphs)<3: #map should have 2 glyphs. Tile and a scatter plot. If it has only these create a new source and a new glyph. 
            source2 = ColumnDataSource(dict(x=[i[0] for i in pointlist], y=[i[1] for i in pointlist]), name = 'LineForGPS')#Create a new source
            mapPlot.scatter(x = 'x', y = 'y',source = source2, color = 'red')

            #PlotGps points that are included in the selection. 
            point1 = np.array(pointlist[0])
            ClosePoints = findClosePoints(df_GPS,point1)
            source3 = ColumnDataSource(ClosePoints) #ClosePoints Source
            plot_map(mapPlot,source3,'black','black')
        else: #if it has at least 1 point that was created already
            #Get Data
            source2 = MapGlyphs[2].data_source #the source for the last renderer, which is the points you make renderer.


            #Plot Line
            toplot = pointlist[-2:]
            source2.data = dict(x=[i[0] for i in toplot], y=[i[1] for i in toplot])        
            mapPlot.line(x = 'x',y = 'y',source = source2,color = 'red')

            #Plot GPS points that are included in the selection
            point1 = np.array(toplot[0])
            ClosePoints = findClosePoints(df_GPS,point1)
            source3 = MapGlyphs[3].data_source #ClosePoints Source
            source3.data = ClosePoints
            #ShowSplitLap Button
            Split_button.visible = True
        
    def LapTimes_GPS():
        #Input is the 2 points that make the line where you count the laps from. 
        #Gives laptimes. Must have access to the Map Figure object, to get the GPS Data. 

        #Load GPS Data
        MapGlyphs = mapPlot.renderers 
        source_GPS = MapGlyphs[1].data_source# The source(ColumnDataSource) that contains the gps data. 
        dict_GPS = source_GPS.data #Get the dict of the data 
        df_GPS = pd.DataFrame.from_dict(dict_GPS)#Make Data a DataFrame

        #Make arrays of the points of the lap line, calculate its vector, with the origin on Point1
        source_line = MapGlyphs[2].data_source #Line source is the last added to the map. 
        dict_line = source_line.data
        line_points = [[dict_line['x'][0],dict_line['y'][0]],[dict_line['x'][1],dict_line['y'][1]]]

        point1 = np.array(line_points[0])
        point2 = np.array(line_points[1])
        linevector = point2-point1
        
        #Find Close Points to line
        ClosePoints = findClosePoints(df_GPS,point1)

        #Plot all the points that are considered Close to the line with Black dots. 
        plot_map(mapPlot,ColumnDataSource(ClosePoints),'black','red')

        #While Setup
        while_counter = 1
        laptimes = []

        #While there are remaining Close Points, keep goint. 
        while while_counter < 1000: 
            ClosePoints1Lap = ClosePoints[ClosePoints['time']-ClosePoints['time'].loc[0] < 10] #Get The points for 1 lap. These are points that are within 10 seconds of the first close point
            ClosePoints = ClosePoints[ClosePoints['time']-ClosePoints['time'].loc[0] >= 10]# Remove points for 1 lap from Close points. The first close point becomes the first point for the next lap etc

            #Re index both DataFrames
            ClosePoints.index = range(len(ClosePoints.index)) 
            ClosePoints1Lap.index = range(len(ClosePoints1Lap.index))        
            #While Stop Condition
            if len(ClosePoints) < 2: #if you finish the list of close points. 
                while_counter = 10000
            #Make an array of the mercator Coordinates for the Points close to the line for one lap.   
            ClosePointsLap1_array = ClosePoints1Lap[['Longitude_converted','Latitude_converted']].to_numpy()
            #Calculate vectors from lap close points with point1 of the lapline as the origin. 
            ClosePointsLap1_vectors =np.array([i-point1 for i in ClosePointsLap1_array])
            #Calculate the projection vectors from the lap close point vectors (point1 of the lapline as the origin.)
            ClosePointsLap1_projection_vectors = np.array([ i/np.inner(linevector,linevector)*linevector for i in np.inner(ClosePointsLap1_vectors,linevector)])
            #Calculte the distance vectors from the lap close points to the line(vertical to line, point1 of the lapline as the origin.)
            ClosePointsLap1_distance_vectors = ClosePointsLap1_projection_vectors-ClosePointsLap1_vectors
            #Calculate the distances(magnitude of vectors) from the lap close points to the line(vertical to line, point1 of the lapline as the origin.)
            ClosePointsLap1_distances= [np.linalg.norm(i) for i in ClosePointsLap1_distance_vectors]

            #Add the distances & distance vectors, with origin the 1rst point of the lapline to the lap close points df
            ClosePoints1Lap[['Distance-X_origin@point1_of_line','Distance-Y_origin@point1_of_line']]  = pd.DataFrame(ClosePointsLap1_distance_vectors, columns = ['Distance-X','Distance-Y'])
            ClosePoints1Lap['Distance_Magnitude'] = pd.DataFrame(ClosePointsLap1_distances, columns=['Distance_Magnitude'])


            try:
                #The Last point that has a negative Y coordinate, with respect to the CS based at point1
                #is the last point before the line.     
                p_bf = ClosePoints1Lap.loc[len(ClosePoints1Lap[ClosePoints1Lap['Distance-Y_origin@point1_of_line']<=0])-1] #PointJustBeforeTheLine
                #The next point from the last point before the line is the point just after the line.
                p_af = ClosePoints1Lap.loc[len(ClosePoints1Lap[ClosePoints1Lap['Distance-Y_origin@point1_of_line']<=0])] #PointJustAfterTheLine
            
                #Time and distance between the points before and after the line. 
                p_dt = p_af['time']-p_bf['time'] #Time between PointJustBeforeTheLine & PointJustAfterTheLine
                p_ddist = p_af['Distance_Magnitude']+p_bf['Distance_Magnitude'] #distance between PointJustBeforeTheLine & PointJustAfterTheLine
                
                #Calculate Laptime. depending on how close each point is to the line, you add(or remove) a fraction of the time between the points. 
                laptime1 = p_bf['time'] + p_bf['Distance_Magnitude']/p_ddist*p_dt #Calculate laptime by adding to the time of point before the line
                laptime2 = p_af['time'] - p_af['Distance_Magnitude']/p_ddist*p_dt #Calculate laptime by subtracting from time of point after the line
                
                #Random plot with red dots for the data you have processed
                plot_map(mapPlot,ColumnDataSource(ClosePoints1Lap),'red','red')

                #Add the laptime to the laptimes list. Because you work with total times, remove the previous laptimes 
                laptimes.append((laptime1+laptime2)/2-sum(laptimes))
            except:
                while_counter = 10000
                print("Not All Points close to LapLine were used. Check that the laptimes make sense.")
                print("To redo, pick a LapLine where in the black points, the car is not stationary or very slow")

            while_counter = while_counter + 1
        
        #region LapSplitter
        counter = 1
        plotsource = source_GPS 
        for laptime in laptimes:
            
            #Make Dir to Sava Lap Files 
            try:
                os.mkdir('./Logs')
                print('Logs Dir created')
            except:
                pass

            try:
                os.mkdir('./Logs/'+source.name[:-4]+'-GPSLaps')
                print('GPSLaps Dir created')
            except:
                pass
                                
            #set Lap Data to save & remaining data
            source_remaining = pd.DataFrame(plotsource.data) #Get remaining data

            to_save = source_remaining[source_remaining['time']<=laptime]
            source_remaining = source_remaining[source_remaining['time']>laptime]
            
            #Save Data to be saved
            to_save.to_csv('./Logs/'+source.name[:-4]+'-GPSLaps/'+source.name[:-4]+'-Lap'+str(counter)+'.csv')

            #Reformat remaining data for correct index 
            try:        
                del source_remaining['index']
            except:
                pass
            source_remaining.index = range(len(source_remaining.index))        
            
            #Offset time for remaining data so it starts from 0 
            newtime = source_remaining['time']-source_remaining['time'].loc[1] #Must Make new var. 
            source_remaining['time'] = newtime     

            #Progress text 
            LoadingDonetext.text = LoadingDonetext.text + ' | Lap'+str(counter)+' Saved. Time(sec): '+str(round(laptimes[counter-1],2))
            #Update Lap Counter
            counter = counter + 1

            #Update Plots
            plotsource.data = source_remaining    
        
        plotsource_df = pd.DataFrame(plotsource.data)
        plotsource_df.to_csv('./Logs/'+source.name[:-4]+'-GPSLaps/'+source.name[:-4]+'-Remaining.csv')
        LoadingDonetext.text = LoadingDonetext.text +  ' | Done!'
        Done_Button.label = 'Done'
        Done_Button.visible = True

    def quickhideSplitLapsBut():
        Split_button.visible = False
        LoadingDonetext.visible = True
        Done_Button.visible = False
        LapTimes_GPS()

    def findClosePoints(df_GPS,point1):
        #Give Pandas DataFrame and first line point, Return Close points dataframe, with ordered index 
        #Remove Duplicate Coordinate Points. There is a slight difference in the laptimes 
        #if you keep the first or the last occurence of the coordinate points in the data.  
        NoDuplicatsGPSpoints = df_GPS.drop_duplicates(subset=['Latitude_converted', 'Longitude_converted'], keep='first')

        #Get All The GPS Points that are close to point1 of the line. 
        ClosePoints = NoDuplicatsGPSpoints[abs(NoDuplicatsGPSpoints['Latitude_converted']-point1[1])<100] #100 is arbitrary, just because its big. 
        ClosePoints = ClosePoints[abs(ClosePoints['Longitude_converted']-point1[0])<100]
        ClosePoints = ClosePoints[ClosePoints['Speed (kph)'] > 20] #Limit Speed. 
        #Re index Close Points DataFrame
        del ClosePoints['index']
        ClosePoints.index = range(len(ClosePoints.index)) 
        return ClosePoints

    #__________________________________ LAYOUT_____________________________________


    #endregion
    #region: LAYOUT
    Split_button = Button(label = 'Split Laps', name = 'SplitLap', visible = False)
    Split_button.on_click(quickhideSplitLapsBut)
    guidetext = PreText(text = 'Double Click sequentially on the map to create the LapLine, to split the laps. \nThe black points are computed to be the closest points to the LapLine where the car is not stationary or very slow. Check if they make sense, and then click Split Laps once.It takes some time. \nThe Laps are in ./Logs/[filename]-GPSLaps', sizing_mode = 'stretch_width')
    LoadingDonetext = PreText(text = 'Wait...', visible = False, sizing_mode = 'stretch_height')
    pointlist = []
    Done_Button = Button(label = 'Exit', name = 'DoneGPSSplitLap', visible = True)
    Done_Button.on_click(Done)
    mapPlot = MapChart_new(source,10)
    mapPlot.sizing_mode = 'stretch_both'

    mapPlot.on_event(DoubleTap, make2Points)
    lay = layout([[guidetext],[mapPlot],[Split_button,LoadingDonetext],[Done_Button]])
    #endregion
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
        NewTab = Panel(child = lay ,title = 'Misalign_All')
        TabsModel.tabs[-1] = NewTab
    #File Choice Layout.
    inputfile = FileInput(width = 230)
    inputfile.on_change('filename',inputfile_callback)
    Cancel_Button = Button(label = 'Cancel')
    Cancel_Button.on_click(Done)
    NewTab = Panel(child = row([inputfile,toggle_datetime,Cancel_Button]) ,title = 'Misalign_All')
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
        NewTab = Panel(child = lay ,title = 'Misalign_LongVert')
        TabsModel.tabs[-1] = NewTab
    #File Choice Layout.
    Cancel_Button = Button(label = 'Cancel')
    Cancel_Button.on_click(Done)    
    inputfile = FileInput(width = 230)
    inputfile.on_change('filename',inputfile_callback)
    NewTab = Panel(child = row([inputfile,toggle_datetime,Cancel_Button]) ,title = 'Misalign_LongVert')
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
        NewTab = Panel(child = lay ,title = 'Manual_LapSplit')
        TabsModel.tabs[-1] = NewTab
    #File Choice Layout.
    Cancel_Button = Button(label = 'Cancel')
    Cancel_Button.on_click(Done)
    inputfile = FileInput(width = 230)
    inputfile.on_change('filename',inputfile_callback)
    NewTab = Panel(child = row([inputfile,toggle_datetime,Cancel_Button]) ,title = 'Manual_LapSplit')
    TabsModel.tabs.append(NewTab)
    old_activeTab = TabsModel.active
    TabsModel.active = (len(TabsModel.tabs)-1) #switch Tab to New One
    TabsModel.disabled = True

def GPS_LapSplitter_Popup():
    def inputfile_callback(a,b,name):
        file_bytes = base64.b64decode(inputfile.value)
        file = io.BytesIO(file_bytes)
        if toggle_datetime.active == True:
            source = dataimport(file,name,'DateTIMMMEEEE~')
        else:
            source = dataimport(file,name)
        lay = GPS_LapSplitter(source)
        NewTab = Panel(child = lay ,title = 'GPS_LapSplit')
        TabsModel.tabs[-1] = NewTab
    #File Choice Layout.
    Cancel_Button = Button(label = 'Cancel')
    Cancel_Button.on_click(Done)
    inputfile = FileInput(width = 230)
    inputfile.on_change('filename',inputfile_callback)
    NewTab = Panel(child = row([inputfile,toggle_datetime,Cancel_Button]) ,title = 'GPS_LapSplit')
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
but_GPSLapSplit = Button(label = 'GPS Lap Splitter')
but_GPSLapSplit.on_click(GPS_LapSplitter_Popup)
but_Misalignment_ALL = Button(label = 'Misalignment Correction - All axes')
but_Misalignment_ALL.on_click(Misalignment_All_Popup)
but_Misalignment_longvert = Button(label = 'Misalignment Correction - Long-Vert axes')
but_Misalignment_longvert.on_click(Misalignment_LongVert_Popup)

SPlay = layout([fileinput,pre],[toggle_datetime,predt],[but_LapSplit,but_GPSLapSplit,but_Misalignment_ALL,but_Misalignment_longvert])

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