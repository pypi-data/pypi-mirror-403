def startup():
    # Ok... soooooo....
    # The python interpretor in harmony is not set up correctly and does not
    # process the .pth file in ITS OWN VENV ! -__________-
    # So we need to re-install the SAME venv site AGAIN...
    # In order to get the site path, I could use an env var set before launching
    # harmony, but that would work only in controled environment. So I am 
    # builing the path from one of the package I know is in the venv and not in 
    # harmony internal: rich (it is a direct dependency of tgzr.hosts.harmony)
    # I hear you say "that too will only work in your controled environment!"
    # and I would answer that installing rich should be easy enough...
    print("Patching Harmony's wonky python site...")
    from pathlib import Path
    import rich
    import site
    site_packages_path = Path(rich.__path__[0]).parent
    print(f'  Adding site {site_packages_path}')
    site.addsitedir(site_packages_path)
    
    # -- now we can import package even if installed in editable mode --

    # But.... -____-
    # Harmony is not settings up python correctly, we need to add
    # our python install (not our venv) DLLs folder to the path or 
    # none of the python extension (compiled packages) loads :[
    # Symptom: " ModuleNotFoundError: No module named '_socket' "
    import sys
    from pathlib import Path
    for i in sys.path:
        if i.endswith("zip"):
            dll_path = Path(i).parent / "DLLs"
            if dll_path not in sys.path:
                print(" Adding missing DLLs folder to sys.path:", dll_path)
                sys.path.append(str(dll_path))


    # -- now we can import compiled packages
    import tgzr.hosts.harmony.startup
    tgzr.hosts.harmony.startup.startup_gui()

def show_gui():
    startup()
    print("Generic GUI not yet implemented :/")
