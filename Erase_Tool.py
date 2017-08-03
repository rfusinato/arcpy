import arcpy
##--------------------------------------------------------------------
## Name:     Erase_Tool.py
## Purpose:  Erase an overlapping feature from an input feature class.
##
##
## Author:   Robbie Fusinato
## Created:  12/08/2016
##
##--------------------------------------------------------------------

try:

        arcpy.env.workspace = 'in_memory'
        arcpy.env.overwriteOutput = True

        fcInput = r'C:\...'     # Filepath for Input Featureclass
        fcErase = r'C:\...'     # Filepath for Erase Featureclass
        fcOutput = r'C:\...'    # Filepath for Output Featureclass

        arcpy.Union_analysis([fcInput,fcErase],'tempUnion')

        # Remove features from the union dataset that were in the overlapping Erase Featureclass.
        idFld = arcpy.ListFields('tempUnion','FID*')[1].name
        cursor = arcpy.UpdateCursor('tempUnion')
        for row in cursor:
            if not(row.getValue(idFld) == -1):
                cursor.deleteRow(row)
        del cursor, row, idFld

        # Retreive a list of field names from the Input Featureclass
        fcInputList = []
        for f in arcpy.ListFields(fcInput):
            fcInputList.append(f.name)

        # Retreive a list of field names from the Union Featureclass
        fcOutputList = []
        for f in arcpy.ListFields('tempUnion'):
            fcOutputList.append(f.name)

        # Create a list of field names that are in the Union Featureclass but are not in the Input Featureclass
        fList = []
        for f in fcOutputList:
            if not(f in fcInputList):
                fList.append(f)

        # Delete the fields not in the Input Featureclass from the Union Featureclass
        arcpy.DeleteField_management('tempUnion',fList)
        del fList, fcInputList, fcOutputList, f

        # Copy the updated Featureclass from the memory workspace to the output location.
        arcpy.CopyFeatures_management('tempUnion', fcOutput)
        if arcpy.Exists('tempUnion'):
            arcpy.Delete_management('tempUnion')


except Exception as e:
        arcpy.AddMessage(e)
