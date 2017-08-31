import arcpy
##--------------------------------------------------------------------
## Name:     ExtentToPolygon.py
## Purpose:  Creates a polygon featureclass using the current map extent
##           to be used as a page marker with DataDriven pages.  The polygon
##           will also store the current map scale to be used with a DataDriven
##           scale.  After creating all of your page markers you can use the
##           Merge_management tool to combine them into a single index featureclass.
##
## Author:   Robbie Fusinato
## Created:  08/31/2017
##
##--------------------------------------------------------------------

try:
        outFtr = r"C\..."
        mxd = arcpy.mapping.MapDocument("CURRENT")
        arcpy.Select_analysis(mxd.activeDataFrame.extent.polygon,outFtr)
        arcpy.AddField_management(outFtr,"SCALE","DOUBLE")
        arcpy.CalculateField_management(outFtr,"SCALE",str(int(mxd.activeDataFrame.scale)))

except Exception as e:
        arcpy.AddMessage(e)
return
