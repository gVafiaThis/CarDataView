import bokeh
from bokeh.models import ColumnDataSource,CrosshairTool,CheckboxGroup,Spacer
from bokeh.plotting import figure,curdoc
from bokeh.layouts import column,row,layout
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
import pandas as pd
from bokeh.palettes import Category10_10
import numpy as np
#Changelog v2 -> Added Multiple sources support for datachart_new and MapChart.Now they can take lists as sources input and plot
#                data from multiple sources on the same figure. 
#Changelog v3 -> Added Colors. Changed MapChart for starter colors of palette. Changed datachart_new to  change color depending on how many sources it gets
#Changelog v4 -> Created function for plotting in figures to clean up the mess.Add ToolTips to plots for Hovertool
#Changelog v5 -> Change datachart_new to use common X_range. Added datatime to time in dataimport. 
#Changelog v6 -> Add simple DataTab  function for easy visualization in testing. Correct Azimuth Stuff in dataimport
#Changelog v7 -> datatransform_rotate function. Save original lat&long data. The lat&longs plotted are [lat/long]_converted. Map positioning in mapchart ignores first 10 numbers. So you dont have zooming issue 
#Changelog v8 -> Change dataimport to get a name input also. To support Reading files from wherever. 
def inf_colorpick(number_sources,colors): #Color picker infinite. 
    #Find the color of the next plot, when you know how many sources are in the chart, together with the next plot source(the source you're adding).  
    #Each source requires 2 colors. Below we find the index of the color pallete depending on how many sources there are on the tab.
    #Num_sources = 2 -> source1_color_index = [0]&[1], source2_color_index = [2]&[3]
    #Indexes = [(Num_sources-1)*2] + [(Num_sources-1)*2+1]
    color_index = [(number_sources-1)*2,(number_sources-1)*2+1]
    color_num = len(colors)

    color_index[0] = color_index[0] - (color_index[0]//color_num)*color_num #upoloipo 
    color_index[1] = color_index[1] - (color_index[1]//color_num)*color_num #upoloipo 
       
    return colors[color_index[0]],colors[color_index[1]]
    
def latlon2yx(lo,la):
    # derived from the Java version explained here: http://wiki.openstreetmap.org/wiki/Mercator
    # Translate GPS data from phone to mercator latitude and logitude. These are plottable in Bokeh. 
    #-------------------------------------------------------------------------------------------------------------------
    y =  np.log(np.tan(np.pi / 4 + np.radians(la) / 2)) * 6378137.0
    x = np.radians(lo) * 6378137.0
    return x,y

def dataimport(file,name,*args):
    #import csv and return a ColumnDataSource with its name
    #name = str : Name of the csv file
    #file: Decoded byte64 file, after io.BytesIO use
    #-------------------------------------------------------------------------------------------------------------------
    df = pd.read_csv(file)
    if len(args)>0:
        df['time'] =  pd.to_datetime(df['time'], format='%H:%M:%S:%f').dt.strftime('%H:%M:%S.%f')
        df['time'] = pd.to_timedelta(df['time'])
        df['time'] = df['time'].dt.total_seconds()
        df['time'] = df['time'].subtract(df['time'][0])
    LonX,LatY = latlon2yx(df["Longitude"],df["Latitude"])
    df["Latitude_converted"] = LatY
    df["Longitude_converted"]= LonX
    df["Speed (kph)"] = df["Speed (m/s)"]*3.6
    # df['Azimuth'] = [x if x<180 else x-360 for x in df['Azimuth']]
    source = ColumnDataSource(df,name = name)
    return source

def dataimport_filename(name,*args):
    #OLD VERSION, works with a directory, filename, whatever. import csv and return a ColumnDataSource with its name
    #name = str : Directory of csv file with data
    #-------------------------------------------------------------------------------------------------------------------
    df = pd.read_csv(name)
    if len(args)>0:
        df['time'] =  pd.to_datetime(df['time'], format='%H:%M:%S:%f').dt.strftime('%H:%M:%S.%f')
        df['time'] = pd.to_timedelta(df['time'])
        df['time'] = df['time'].dt.total_seconds()
        df['time'] = df['time'].subtract(df['time'][0])
    LonX,LatY = latlon2yx(df["Longitude"],df["Latitude"])
    df["Latitude_converted"] = LatY
    df["Longitude_converted"]= LonX
    df["Speed (kph)"] = df["Speed (m/s)"]*3.6
    # df['Azimuth'] = [x if x<180 else x-360 for x in df['Azimuth']]
    source = ColumnDataSource(df,name = name)
    return source

def plot_map(mapfig,source,color,selection_color,*args):
    mapfig.circle(x = "Longitude_converted",y = "Latitude_converted",source = source, selection_color=selection_color, color = color  )

def plot_chart(chartfig,data,source,color,selection_color):
    # alpha=1, nonselection_alpha=0.01, selection_alpha=1
    chartfig.line(x = "time", y = data, source = source, line_width = 2.5, line_color = color )
    chartfig.circle(x = "time", y = data, source = source,selection_color=selection_color, alpha=0, nonselection_alpha=0, selection_alpha=0.2)
   
def MapChart_new(source,GPSoffset):
    #Create a Map Figure and populate it with a plot.
    #source = columndatasource with map data you will plot. Must have "Latitude","Longitude" columns    
    #GPSoffset = Poso xwro dineis deksia aristera sto map apo tis times sou 
    #-------------------------------------------------------------------------------------------------------------------
    LatY = source.data["Latitude_converted"][10:]
    LonX = source.data["Longitude_converted"][10:]
    map = figure(x_range=(min(LonX)-GPSoffset, max(LonX)+GPSoffset), y_range=(min(LatY)-GPSoffset, max(LatY)+GPSoffset),
           x_axis_type="mercator", y_axis_type="mercator",output_backend="webgl",title = "    ",width = 400, height = 380, tools =['pan','box_select','wheel_zoom','box_zoom'])
    map.xaxis.visible = False
    map.yaxis.visible = False
    #------------------COMMENT BELOW 2 LINES FOR OFFLINE USE--------------------
    tile_provider = get_provider(CARTODBPOSITRON)
    map.add_tile(tile_provider)
    
    plot_map(map,source,Category10_10[0],Category10_10[1])
    map.name = 'MapFig'
    return map

def datachart_new(data,sources,*args):
    #Create a datachart(figure)
    #Name it with its data label(for identification)
    #Populate it with data from a number of sources and return it.
    #data = str (name of columndatasource to plot)
    #sources = list of bokeh columndatasources
    #-------------------------------------------------------------------------------------------------------------------
    title = data
    #plot path
    i = 1 #couter for colors

    if len(args)>0:
        dataplot = figure( title = title, tools = ['box_select','xpan','reset','xwheel_zoom'],active_scroll = 'xwheel_zoom',active_drag = 'xpan',output_backend="webgl", name = data,height = 150,sizing_mode = 'stretch_width',min_border=0,x_range=args[0])
    else:
        dataplot = figure( title = title, tools = ['box_select','xpan','reset','xwheel_zoom'],active_scroll = 'xwheel_zoom',active_drag = 'xpan',output_backend="webgl", name = data,height = 150,sizing_mode = 'stretch_width',min_border=0)

    for source in sources:
        line_color,selection_color = inf_colorpick(i,Category10_10) 
        plot_chart(dataplot,data,source,line_color,selection_color)
        i = i + 1
    return dataplot

def DatachartList_new(datalist,source):

    #Returns a list of datacharts with the data in datalist
    #datalist = List of Strings!
    #source = ColumnDataSource of data. 
    plotlist = [] #empty list
    # print(datalist)
    for dataname in datalist:
        # print(dataname)
        plot = datachart_new(dataname,source)
        plotlist.append(plot) #Append a plot object to the list
        

    plotcolumn = column(plotlist,name = 'DataPlots',sizing_mode='stretch_width')
    return plotcolumn

def SimpleDataTab(sources,**kwargs): #Simple Data Visualisation for Test Purposes
    #Returns a Bokeh document with the plots as in normal DataTab. should be run in a server. 
    #Sources should be a list of columndatasources
    #defaut_plots should be a list of the tags of the plots 
    #nomap is boolean. Default = False , so there is a map

    
    #//////Check for default_plots input arg. Deault default_plots is empty
    try:
        default_plots = kwargs['default_plots']
        assert type(default_plots)==type([]),"Not a List"
        assert type(default_plots[0])==type('string'),"Not a list of Strings"  
    except:
        default_plots = ['gFx','gFy','gFz']
        # print('no default_plots')

    #//////Check for nomap input arg. Deault nomap is False
    try:
        nomap = kwargs['nomap']
        assert type(nomap)==type(True),"Not a boolean"    
    except:
        nomap = False
        # print('There is a map')
      
    #//////Callback function for hiding
    def sDT_hider(a,b,new):
        #for charts plots
        visible_renderer_indexes = [2*x for x in new]+[2*x+1 for x in new] #check DataView hider function for how this works.
        for figure in charts.children: #For each figure(chart) in the Data Chart Container
            visible_renderers = [figure.renderers[x] for x in visible_renderer_indexes] #visible renderers = the ones whose toggle is active 
            hidden_renderers = list(set(figure.renderers).difference(visible_renderers)) #hidden renderers = the rest of the figure's renderers
            for renderers in visible_renderers:
                    renderers.visible = True
            for renderers in hidden_renderers:
                    renderers.visible = False
        #Check if the map has a tile renderer. only works if tile renderer is renderers[0]
        if isinstance(map.renderers[0], bokeh.models.renderers.TileRenderer):
            visible_maprenderers = [map.renderers[x+1] for x in new] #one plot-one source. plot[0] - source[0]. new has active sources(buttons)
            visible_maprenderers.append(map.renderers[0])
        else:
            visible_maprenderers = [map.renderers[x] for x in new]
        #For Map plot
        hidden_maprenderers =list(set(map.renderers).difference(visible_maprenderers))
        for renderers in visible_maprenderers:
                renderers.visible = True
        for renderers in hidden_maprenderers:
                renderers.visible = False   

    #\\\\\\first source creates all the plots and stuff.
    source = sources[0]

    #\\\\\\Create Map Chart with plotted data - Figure   
    map = MapChart_new(source,10.0) #MapChart_new works with columndatasources. Creates a Map with the car route plotted

    #\\\\\\Create DataCharts with plotted data - Column (bokeh figure Container)    
    charts = DatachartList_new(default_plots,[source]) #Datachartlist_new works with lists. #Creates the Data Chart container and some default charts
    for chart in charts.children: #add Linked zooming and panning    
        if chart != charts.children[0]:
            chart.x_range = charts.children[0].x_range #Linked zooming and panning 
    
    #\\\\\\Add other sources data
    if len(sources)>1:
        i = 2
        for source in sources[1:]: #for all other sources. 
            #color of plot 
            line_color,selection_color = inf_colorpick(i,Category10_10)
            #Add to map
            TabMap = curdoc().get_model_by_id(map.id)
            plot_map(map,source,line_color,selection_color)
            #Add to Charts
            # column = curdoc().get_model_by_id(charts.id) #Get Chart List Container from its id (stored in tabs_contents INDEX)
            for chart in charts.children:
                plot_chart(chart,chart.name,source,line_color,selection_color) 
    
#    \\\\\\Add CheckboxGroup to show/hide source data in plots in tab
    cbut = CheckboxGroup(labels = [x.name for x in sources], active = [0], width = 60, sizing_mode = 'stretch_height') #Create Widget
    cbut.on_change('active',sDT_hider) #Create Callback

    #\\\\\\Spacer for Layout
    spaceright = Spacer(width = 10, height = 10, sizing_mode = 'fixed')

    #\\\\\\Create Layout
    if not nomap:
        rosw = row([map,charts,cbut,spaceright])
    else:
        rosw = row([charts,cbut,spaceright])
    lay = layout(rosw,name = 'mainLayout',sizing_mode = 'stretch_width')

    
    #\\\\\\Return Layout 
    return lay,charts.id,map.id,cbut.id

def datatransform_rotate(data_df,RotMatrix,keys):
    #Take a dataframe and a rotation matrix and rotate some data of the dataframe, indicated by the labels in keys. 
    #data_df - pandas dataframe 
    #RotMatrix - np.array
    #keys = list of list of 3 strings.Has to be 3. its the labels of the dataframe that are gonna be rotated
    transformed_data_df = pd.DataFrame()
    for df_3labels in keys:
        #df_3labels format- ['gFx','gFy','gFz']
        data_3rows_array = data_df[df_3labels].to_numpy()
        rotated_data_3rows_array = np.inner(data_3rows_array,RotMatrix)
        rotated_data_3rows_df = pd.DataFrame(rotated_data_3rows_array,columns =df_3labels)
        transformed_data_df[df_3labels] = rotated_data_3rows_df[df_3labels] #join didnt work 
    return transformed_data_df

    

# def splitter():