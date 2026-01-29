//Mandatory function. This configures package items.
function configure(packageFolder, packageName) {
    if (about.isStageEssentials() || about.isStageAdvanced() || about.isPaintMode() || about.isStoryboard() || about.isGameStudio())
        return;

    var startup_py = packageFolder + '/startup.py'
    MessageLog.trace(' >>> configuring' + packageName + "from" + packageFolder + ': loading ' + startup_py)
    var tgzr_startup_py = PythonManager.createPyObject(startup_py, 'tgzr_startup_py')
    tgzr_startup_py.py.startup()


    //---------------------------
    //Create Global Toolbar
    var globalToolbar = new ScriptToolbarDef({
        text: "TGZR",
        customizable: "false"
    });

    globalToolbar.addButton({
        text: translator.tr("Tools"),
        icon: "tgzr_thumbnail.png",
        action: "show_gui in ./configure.js"
    });

    ScriptManager.addToolbar(globalToolbar);
}

function show_gui() {
    var pyObjects = PythonManager.getPyObjects();
    var tgzr_startup_py = pyObjects['tgzr_startup_py'];
    tgzr_startup_py.py.show_gui();

}

exports.configure = configure;
