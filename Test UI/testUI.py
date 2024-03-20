import adsk.core, traceback

def run(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
