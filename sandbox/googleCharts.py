#!/usr/bin/env python
# coding=utf-8

""" Python wrapper for the Google chart API """

"""note: The largest possible area for all charts except maps is 300,000 pixels. 
As the maximum height or width is 1000 pixels, examples of maximum sizes are 
1000x300, 300x1000, 600x500, 500x600, 800x375, and 375x800."""

"""
cht - chart type specification
chco - chart colors
chs - bar chart size
chd - chart data
chdl - chart legend
chds - data scaling parameter
chxt - axis specification
chxl - specify labels on axis
chbh - bar thickness and spacing
"""

def pie_chart(values, labels=None, colors=None, size=(400,200), in_3d=False):
	"""returns a string of the url for the generated pie graph via google"""
	valueList = []; labelList = []; colorList = []
	#lambda functions to check params, convert and format strings
	param3D = lambda x: ["p3","p"][x==False]
	paramColors = lambda x: [''.join([z for z in colorList]),'None'][x==None]
	paramLabels = lambda x: [labelList[0:len(labelList)-3],''][x==None]
	if colors != None: 
		for x in colors: colorList.append("%s%%7C" % x.strip("#")) #format values for colors
		colorList[len(colorList)-1] = colorList[len(colorList)-1].strip('%7C') #remove last seperatng value
	if labels != None:
		for y in labels: labelList.append(("%s%%7c" % y).replace(" ", "%20")) #add seperating values, remove spaces
	total = sum(values)
	valueList = map(lambda x: (float(x)/float(total)*100.0), values) #normalize data values
	valueList = ''.join(["%3.2f," % s for s in valueList]) #float values to two significant figures
	labelList = ''.join([z for z in labelList]) #list contents to a string value
	return "http://chart.apis.google.com/chart?chco=%s&chd=t:%s&chs=%s&cht=%s&chl=%s" % \
		(paramColors(colors), valueList[0:len(valueList)-1], ("%sx%s" % (size[0], size[1])), param3D(in_3d), paramLabels(labels))
		
def bar_chart(values, labels=None, colors=None, size=(400,200)):
	"""returns a string of the url for the generated bar chart via google"""
	valueList = []; labelList = []; colorList = []
	paramColors = lambda x: [''.join([z for z in colorList]),'None'][x==None]
	paramLabels = lambda x: [''.join([z for z in labelList]),''][x==None]
	chdlBool = lambda x: ["&chdl=",''][x==None] #check if the chart legend needs to be included in the graph
	valueList = ''.join(['%i,' % s for s in values]) #convert numerical list to string seperated by commas
	chxlFormat = lambda x: "0:%%7c0%%7c%s%%7c%s%%7c%s%%7c%s" % (max(x)/4, max(x)/2, max(x)*0.75, max(x)) #0:|0|(max/4)|(max/2)|(max*0.75)|(max)
	if colors != None: 
		for x in colors: colorList.append("%s%%7C" % x.strip("#"))
		colorList[len(colorList)-1] = colorList[len(colorList)-1].strip('%7C')
	if labels != None:
		for y in labels: labelList.append(("%s%%7c" % y).replace(" ", "%20")) #
		labelList[len(labelList)-1] = labelList[len(labelList)-1].strip('%7c') #remove last seperatng value from labelList
	return "http://chart.apis.google.com/chart?cht=bvs&chs=%s%s%s&chd=t:%s&chco=%s&chds=0,%s&chxt=y&chxl=%s&chbh=a" % \
		(("%sx%s" % (size[0], size[1])), chdlBool(labels), paramLabels(labels), valueList[0:len(valueList)-1], paramColors(colors), max(values), chxlFormat(values))
	
def grouped_bar_chart(values_a, values_b, labels=None, colors_a=None, colors_b=None, size=(400,200)):
	"""returns a string of the url for the generated grouped bar chart via google"""
	valueListA = []; valueListB = []; labelListA = []; labelListB = []; colorListA = []; colorListB = []
	paramColors = lambda x: [''.join([z for z in colorList]),'None'][x==None]
	paramLabels = lambda x: [''.join([z for z in labelList]),''][x==None]
	return "http://chart.apis.google.com/chart?cht=bvg&chs=%s&chd=t:%s&chdl=%s&chco=%s&chds=%s&chxt=%s&chxl=%s&chbh=a,1,20" % \
		()

# Run a test to see if this script is being executed from the command-line.
if __name__ == "__main__":
    values = [1000,2340,88,792,1985,234]
    values_b = [792,1234,1985,8468,213,99]
    labels = ["White","Black","Native American","Asian","Pacific Islander","Other"]
    colors = ["#0000FF","#5555FF","#999911","#00FF00","#FF00FF","#FFFF00"]
    colors_b = ["#668CFF","#8C66FF","#D966FF","#FF668C","#8CFF66","#FF8C66"]
    print "values=%s\nvalues_b=%s\nlabels=%scolors=%s\ncolors_b=%s\n" % (values,values_b,labels,colors,colors_b)
    print "*"*10 + " pie chart " + "*"*10
    print pie_chart(values,in_3d=True)
    print pie_chart(values,labels,colors)
    print "*"*10 + " bar chart " + "*"*10
    print bar_chart(values,labels,colors)
    print bar_chart(values)
    print "*"*10 + " grouped bar chart " + "*"*10
    #print grouped_bar_chart(values, values_b, labels, colors, colors_b)

