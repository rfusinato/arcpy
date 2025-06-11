import arcpy

##  This tool calculates service line connections for meters by finding the closest main line within a specified search distance.
##  The tool performs spatial analysis by selecting nearby mains, calculating the perpendicular point, and then creating service
##  lines between meters and mains. The tool processes data in memory to avoid modifying the original meter feature class and
##  preserves the OBJECTID field for linking results back to the original data. The results are output as a line feature class,
##  with each line representing a service connection between a meter and its nearest main.

class Toolbox(object):
    def __init__(self):
        self.label = "Service Connection Toolbox"
        self.alias = "ServiceConnection"
        self.tools = [ServiceConnectionTool]

class ServiceConnectionTool(object):
    def __init__(self):
        self.label = "Generate Service Connections"
        self.description = "Creates service connection lines from meters to nearby main lines."
        self.canRunInBackground = False

    def getParameterInfo(self):
        params = [
            arcpy.Parameter(
                displayName="Meter Layer",
                name="meter_layer",
                datatype="Feature Layer",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Main Line Layer",
                name="main_layer",
                datatype="Feature Layer",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Search Distance (e.g., '500 Feet')",
                name="search_distance",
                datatype="String",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Output Line Feature Class",
                name="output_fc",
                datatype="DEFeatureClass",
                parameterType="Required",
                direction="Output"
            ),
        ]
        # Set default value for Search Distance
        params[2].value = '500 Feet'  # Set '500 Feet' as the default
        return params

    def execute(self, parameters, messages):
        meter_fc = parameters[0].valueAsText  # Input Meter layer
        main_fc = parameters[1].valueAsText  # Input Main line layer
        search_distance = parameters[2].valueAsText  # Search distance
        output_fc = parameters[3].valueAsText  # Output feature class

        # Create an in-memory point feature class to store the temporary Meter data
        temp_meter_fc = "in_memory\\temp_meter_fc"

        # Create a point feature class with the same spatial reference as the input Meter layer
        spatial_ref = arcpy.Describe(meter_fc).spatialReference
        arcpy.management.CreateFeatureclass("in_memory", "temp_meter_fc", "POINT", spatial_reference=spatial_ref)

        # Add necessary fields for start_x, start_y, end_x, end_y to the temporary point feature class
        arcpy.management.AddField(temp_meter_fc, "start_x", "DOUBLE")
        arcpy.management.AddField(temp_meter_fc, "start_y", "DOUBLE")
        arcpy.management.AddField(temp_meter_fc, "end_x", "DOUBLE")
        arcpy.management.AddField(temp_meter_fc, "end_y", "DOUBLE")
        arcpy.management.AddField(temp_meter_fc, "ORIG_FID", "LONG")

        # Insert data from the original Meter layer into the temporary point feature class
        with arcpy.da.InsertCursor(temp_meter_fc, ['ORIG_FID', 'SHAPE@']) as insert_cursor:
            with arcpy.da.SearchCursor(meter_fc, ['OBJECTID', 'SHAPE@']) as meter_cursor:
                for meter_row in meter_cursor:
                    insert_cursor.insertRow([meter_row[0], meter_row[1]])

        # Create an in-memory layer for the mains
        main_layer = "main_layer_mem"
        if arcpy.Exists(main_layer):
            arcpy.Delete_management(main_layer)
        arcpy.MakeFeatureLayer_management(main_fc, main_layer)

        # Perform the calculations on the in-memory point feature class
        with arcpy.da.UpdateCursor(temp_meter_fc, ['ORIG_FID', 'SHAPE@', 'start_x', 'start_y', 'end_x', 'end_y']) as meter_cursor:
            for meter_row in meter_cursor:
                meter_geom = meter_row[1]
                meter_row[2] = meter_geom.centroid.X
                meter_row[3] = meter_geom.centroid.Y

                # Select features in memory — don't affect map display
                arcpy.SelectLayerByLocation_management(
                    in_layer=main_layer,
                    overlap_type="WITHIN_A_DISTANCE_GEODESIC",
                    select_features=meter_geom,
                    search_distance=search_distance,
                    selection_type="NEW_SELECTION"
                )

                if int(arcpy.management.GetCount(main_layer)[0]):
                    # Find nearest line in selected mains
                    min_distance = float('inf')
                    nearest_line = None
                    with arcpy.da.SearchCursor(main_layer, ['SHAPE@']) as line_cursor:
                        for line_row in line_cursor:
                            line_geom = line_row[0]
                            distance = meter_geom.distanceTo(line_geom)
                            if distance < min_distance:
                                min_distance = distance
                                nearest_line = line_geom

                    if nearest_line:
                        closest_point = nearest_line.queryPointAndDistance(meter_geom)[0]
                        meter_row[4] = closest_point.centroid.X
                        meter_row[5] = closest_point.centroid.Y
                        meter_cursor.updateRow(meter_row)

        # Create service line connections using XYToLine, preserving the OBJECTID
        arcpy.management.XYToLine(
            in_table=temp_meter_fc,
            out_featureclass=output_fc,
            startx_field="start_x",
            starty_field="start_y",
            endx_field="end_x",
            endy_field="end_y",
            line_type="GEODESIC",
            spatial_reference=spatial_ref,
            attributes="ATTRIBUTES"
        )

        arcpy.management.DeleteField(
            in_table=output_fc,
            drop_field="ORIG_FID_1",
            method="DELETE_FIELDS"
        )

        # Optionally, delete the in-memory point feature class after processing
        arcpy.Delete_management(temp_meter_fc)
