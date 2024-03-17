import adsk.core, adsk.fusion, traceback
from fractions import Fraction

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        rootComp = design.rootComponent
        title = 'Bounding Box'
        if not design:
            ui.messageBox('No active design', title)
            return

        def getSelectedObjects(selectionInput):
            objects = []
            for i in range(0, selectionInput.selectionCount):
                selection = selectionInput.selection(i)
                selectedObj = selection.entity
                if type(selectedObj) is adsk.fusion.BRepBody or \
                        type(selectedObj) is adsk.fusion.BRepFace or \
                        type(selectedObj) is adsk.fusion.Occurrence:
                    objects.append(selectedObj)
            return objects

        def dec_to_proper_frac(dec):
            sign = "-" if dec < 0 else ""
            frac = Fraction(abs(dec))
            return (f"{sign}{frac.numerator // frac.denominator} "
                    f"{frac.numerator % frac.denominator}/{frac.denominator}")

        def roundPartial(value, resolution):
            return round(value / resolution) * resolution


        selected = ui.selectEntity("Select a body", 'SolidBodies').entity
        min_box = selected.orientedMinimumBoundingBox

        length, width, height = str(dec_to_proper_frac(roundPartial(min_box.length/2.54, 0.25))) + '"',\
                                str(dec_to_proper_frac(roundPartial(min_box.width/2.54, 0.25))) + '"',\
                                str(dec_to_proper_frac(roundPartial(min_box.height/2.54, 0.25))) + '"'

        ui.messageBox(str((length, width, height)))


    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
