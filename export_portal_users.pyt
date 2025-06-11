# -*- coding: utf-8 -*-
import arcpy
import csv
from arcgis.gis import GIS

class Toolbox(object):
    def __init__(self):
        self.label = "Export Portal Users"
        self.alias = "exportportalusers"
        self.tools = [ExportUsersToCSV]

class ExportUsersToCSV(object):
    def __init__(self):
        self.label = "Export Portal Users to CSV"
        self.description = "Exports usernames and full names from the signed-in ArcGIS Pro portal to a CSV file."

    def getParameterInfo(self):
        params = []

        output_csv = arcpy.Parameter(
            displayName="Output CSV File",
            name="output_csv",
            datatype="DEFile",
            parameterType="Required",
            direction="Output"
        )
        output_csv.filter.list = ["csv"]
        params.append(output_csv)

        max_users = arcpy.Parameter(
            displayName="Maximum Users to Export",
            name="max_users",
            datatype="Long",
            parameterType="Optional",
            direction="Input"
        )
        max_users.value = 100
        max_users.filter.type = "Range"
        max_users.filter.list = [1, 10000]
        params.append(max_users)

        return params

    def isLicensed(self):
        return True  # Or check for ArcGIS Pro license level if needed

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        output_csv = parameters[0].valueAsText
        max_users = parameters[1].value or 100

        gis = GIS("pro")  # Uses currently signed-in ArcGIS Pro user
        users = gis.users.search(query="", max_users=max_users)

        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["name", "label", "username"])
            for user in users:
                writer.writerow([user.username, user.fullName, user.username])

        arcpy.AddMessage(f"User information exported to {output_csv}")
