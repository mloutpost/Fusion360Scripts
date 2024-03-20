import adsk.core, adsk.fusion, traceback, csv
from fractions import Fraction

app = None
ui = None
commandId = 'MinimalBoundingBoxesToCSV'
commandName = 'MinimalBoundingBoxes'
commandDescription = 'Export Timber List as CSV'
dialogTitle = "Create BOM"

# global set of event handlers to keep them referenced for the duration of the command
handlers = []
appearancesMap = {}


def getSelectedObjects(selectionInput):
    objects = []
    for i in range(0, selectionInput.selectionCount):
        selection = selectionInput.selection(i)
        selectedObj = selection.entity
        if type(selectedObj) is adsk.fusion.BRepBody or \
                type(selectedObj) is adsk.fusion.Occurrence:
            objects.append(selectedObj)
    return objects


def dec_to_proper_frac(dec):
    sign = "-" if dec < 0 else ""
    frac = Fraction(abs(dec))
    if frac.numerator % frac.denominator == 0:
        output = f"{sign}{frac.numerator // frac.denominator}"
    else:
        output = (f"{sign}{frac.numerator // frac.denominator} "
                  f"{frac.numerator % frac.denominator}/{frac.denominator}")
    return output


def roundPartial(value, resolution):
    return round(value / resolution) * resolution


class TimberData:
    def __init__(self, fusionObject):
        self.fusionObject = fusionObject

    def timberProperties(self):
        sel_prop = {}

        if type(self.fusionObject) is adsk.fusion.BRepBody or \
                type(self.fusionObject) is adsk.fusion.Occurrence:
            min_box = self.fusionObject.orientedMinimumBoundingBox
            dimensions = [min_box.length, min_box.width, min_box.height] # access raw output from minimum bounding box object, names don't matter yet
            dim_sorted = sorted(dimensions, reverse=True)
            length, width, height = str(dec_to_proper_frac(roundPartial((dim_sorted[0]+(12*2.54)) / 2.54, 0.25))) + '"', \
                                    str(dec_to_proper_frac(roundPartial(dim_sorted[1] / 2.54, 0.25))) + '"', \
                                    str(dec_to_proper_frac(roundPartial(dim_sorted[2] / 2.54, 0.25))) + '"'
            sel_prop["name"] = self.fusionObject.name
            sel_prop["length"], sel_prop["width"], sel_prop["height"] = length, width, height
        return sel_prop


class SelectionHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):

        global dialogTitle

        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs
            selectionInput = None
            for inputI in inputs:
                global commandId
                if inputI.id == commandId + '_selection':
                    selectionInput = inputI

            objects = getSelectedObjects(selectionInput)
            obj_properties = []
            for obj in objects:
                obj_properties.append(obj)

            if not objects or len(objects) == 0:
                return

            fileDialog = ui.createFileDialog()
            fileDialog.isMultiSelectEnabled = False
            fileDialog.title = dialogTitle + " filename"
            fileDialog.filter = 'CSV (*.csv);;TXT (*.txt);;All Files (*.*)'
            fileDialog.filterIndex = 0
            dialogResult = fileDialog.showSave()
            if dialogResult == adsk.core.DialogResults.DialogOK:
                filename = fileDialog.filename
            else:
                return
            with open(filename, 'w', newline='') as csvfile:
                for obj in obj_properties:
                    fieldnames = ['name', 'length', 'width', 'height']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow(TimberData(obj).timberProperties())

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class DestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class GUICommandBoxHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = SelectionHandler()
            cmd.execute.add(onExecute)

            # This is where I can add additional drop down features and buttons to export to csv file with various properties

            onDestroy = DestroyHandler()
            cmd.destroy.add(onDestroy)
            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onDestroy)
            inputs = cmd.commandInputs
            global commandId
            selectionInput = inputs.addSelectionInput(commandId + '_selection', 'Select',
                                                      'Select bodies or occurrences')
            selectionInput.setSelectionLimits(1)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def run(context):
    try:
        global app
        app = adsk.core.Application.get()
        global ui
        ui = app.userInterface

        global commandId
        global commandName
        global commandDescription

        cmdDef = ui.commandDefinitions.itemById(commandId)
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(commandId, commandName,
                                                               commandDescription)  # no resource folder is specified, the default one will be used

        onCommandCreated = GUICommandBoxHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)

        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
