"""
cwantic_computer module
"""

from . import cwantic_core as _core

__all__ = [
    "CwanticModule",
    "setup_cwantic_computer",
    "load_dll",
    "loadMetal",
    "saveMetal",
    "getMetal",
    "createPipingMetal",
    "createStructureMetal",
    "solve",
    "solvePipingModel",
    "solveStructureModel",
    "disposeSolution",
    "inspectClass",
    "findNameSpaceAndAssembly",
    "copyDirectoryToTemp",
    "createCommand",
    "executeCommand",
    "addProjectFolder",
    "removeProjectFolder",
    "addPipingProject",
    "addStructureProject",
    "removeProject",
    "addPipingStudy",
    "addStructureStudy",
    "removeStudy",
    "duplicateStudy"
]

from typing import Optional, Any

CwanticModule = _core.CwanticModule

def setup_cwantic_computer(
    metapiping_installation_directory: str,
    cwanticModule: CwanticModule
) -> bool:
    """
    Setup the Cwantic Computer by defining its installation directory and module to use.

    Parameters
    ----------
    metapiping_installation_directory : str
        Path to MetaPiping installation directory.
    cwanticModule : CwanticModule
        Module to enable: CwanticModule.All, CwanticModule.MetaPiping, or CwanticModule.MetaStructure.

    Returns
    -------
    bool
        True if the setup is valid and the license for the module is available; False otherwise.

    Raises
    ------
    FileNotFoundError
        If the installation directory, settings, or data sources paths do not exist.
    EnvironmentError
        If loading required DLLs fails or the license is invalid.
    """
    return _core.setup_cwantic_computer(metapiping_installation_directory, cwanticModule)

def load_dll(dllname: str) -> None:
    """
    Load a .NET DLL from assembly name.

    Parameters
    ----------
    dllname : str
        Name of the DLL file to load.

    Raises
    ------
    EnvironmentError
        If the setup has not been done.
    FileNotFoundError
        If the DLL cannot be found in installation directories.
    """
    return _core.load_dll(dllname)


def loadMetal(metalFilename: str) -> Optional[Any]:
    """
    Load a MetaL model from file.

    Parameters
    ----------
    metalFilename : str
        Path to the .metal file.

    Returns
    -------
    Any
        Loaded MetaL object if successful, None otherwise.

    Raises
    ------
    EnvironmentError
        If the setup has not been completed.
    """
    return _core.loadMetal(metalFilename)


def saveMetal(metal: Any, metalFilename: str) -> None:
    """
    Save a MetaL model to file, including associated .fre file.

    Parameters
    ----------
    metal : Any
        MetaL object to save.
    metalFilename : str
        Path to save the metal file.

    Raises
    ------
    EnvironmentError
        If the setup has not been completed.
    """
    return _core.saveMetal(metal, metalFilename)


def getMetal(directory: str) -> str:
    """
    Return the first MetaL filename in the directory.

    Parameters
    ----------
    directory : str
        Directory to search for .metal files.

    Returns
    -------
    str
        Full path of the first .metal file found, or empty string if none.

    Raises
    ------
    EnvironmentError
        If the setup has not been completed.
    """
    return _core.getMetal(directory)


def createPipingMetal() -> Any:
    """
    Create an empty piping MetaL model with a layer 0.

    Returns
    -------
    Any
        Empty piping MetaL object.

    Raises
    ------
    EnvironmentError
        If setup has not been completed or MetaPiping module is invalid.
    """
    return _core.createPipingMetal()


def createStructureMetal() -> Any:
    """
    Create an empty structure MetaL model with a layer 0.

    Returns
    -------
    Any
        Empty structure MetaL object.

    Raises
    ------
    EnvironmentError
        If setup has not been completed or MetaStructure module is invalid.
    """
    return _core.createStructureMetal()


def solve(filename: str, solvername: str, sandbox: bool) -> Optional[Any]:
    """
    Solve a piping or structure MetaL model.

    Parameters
    ----------
    filename : str
        Path to the .metal file.
    solvername : str
        'Aster' or 'PipeStress'.
    sandbox : bool
        True to run in a temporary directory, False to run in place.

    Returns
    -------
    Any
        Solution object if solved successfully, None otherwise.

    Raises
    ------
    EnvironmentError
        If setup has not been completed.
    """
    return _core.solve(filename, solvername, sandbox)


def disposeSolution() -> None:
    """
    Close the solution and free associated memory and temporary files.

    Raises
    ------
    None
    """
    return _core.disposeSolution()


def solvePipingModel(metal: Any, metalFilename: str, solvername: str, directory: str) -> Optional[Any]:
    """
    Solve a piping MetaL using specified solver.

    Parameters
    ----------
    metal : Any
        Piping MetaL object.
    metalFilename : str
        Path to the metal file.
    solvername : str
        Solver name ('Aster' or 'PipeStress').
    directory : str
        Directory to execute the solver in.

    Returns
    -------
    Any
        Solution object or None if failure.

    Raises
    ------
    EnvironmentError
        If setup or module is invalid.
    """
    return _core.solvePipingModel(metal, metalFilename, solvername, directory)


def solveStructureModel(metal: Any, metalFilename: str, directory: str) -> Optional[Any]:
    """
    Solve a structure MetaL using Aster solver.

    Parameters
    ----------
    metal : Any
        Structure MetaL object.
    metalFilename : str
        Path to the metal file.
    directory : str
        Directory to execute the solver in.

    Returns
    -------
    Any
        Solution object or None if failure.

    Raises
    ------
    EnvironmentError
        If setup or module is invalid.
    """
    return _core.solveStructureModel(metal, metalFilename, directory)


def inspectClass(instance: Any, indent: bool = False) -> str:
    """
    Export a class or instance as a JSON structure listing properties and public methods.

    Parameters
    ----------
    instance : Any
        The class or instance to inspect.
    indent : bool
        True to pretty-print JSON with indentation.

    Returns
    -------
    str
        JSON string representing the object.

    Raises
    ------
    EnvironmentError
        If setup has not been completed.
    """
    return _core.inspectClass(instance, indent)


def findNameSpaceAndAssembly(className: str) -> tuple[str, str]:
    """
    Return the namespace and assembly of a class in MetaPiping.

    Parameters
    ----------
    className : str
        Name of the class.

    Returns
    -------
    tuple[str, str]
        Namespace and assembly name, or (None, None) if not found.

    Raises
    ------
    EnvironmentError
        If setup has not been completed.
    """
    return _core.findNameSpaceAndAssembly(className)


def copyDirectoryToTemp(directory: str) -> str:
    """
    Copy a directory to a unique temporary folder.

    Parameters
    ----------
    directory : str
        Directory to copy.

    Returns
    -------
    str
        Path to temporary directory or empty string on failure.
    """
    return _core.copyDirectoryToTemp(directory)


def createCommand(commandName: str, metal: Any) -> Any:
    """
    Create a custom command for the MetaL.

    Parameters
    ----------
    commandName : str
        Name of the custom command.
    metal : Any
        MetaL object the command applies to.

    Returns
    -------
    Any
        Command object ready to execute.

    Raises
    ------
    EnvironmentError
        If setup has not been completed.
    """
    return _core.createCommand(commandName, metal)


def executeCommand(command: Any) -> None:
    """
    Execute a previously created custom command.

    Parameters
    ----------
    command : Any
        Command object returned by createCommand.

    Raises
    ------
    EnvironmentError
        If setup has not been completed.
    """
    return _core.executeCommand(command)


def addProjectFolder(directory: str, folderName: str) -> str:
    """
    Add a new folder for a project.

    Parameters
    ----------
    directory : str
        Parent directory where folder will be created.
    folderName : str
        Name of the folder to create.

    Returns
    -------
    str
        Full path of created folder, empty string if folder already exists.

    Raises
    ------
    EnvironmentError
        If setup has not been completed.
    """
    return _core.addProjectFolder(directory, folderName)


def removeProjectFolder(folderDirectory: str) -> None:
    """
    Remove a project folder.

    Parameters
    ----------
    folderDirectory : str
        Path of the folder to remove.

    Raises
    ------
    EnvironmentError
        If setup has not been completed.
    """
    return _core.removeProjectFolder(folderDirectory)


def addPipingProject(
    directory: str,
    projectName: str,
    studyName: str,
    screenWidth: int,
    screenheight: int
) -> str:
    """
    Add a new project containing a piping study.

    Parameters
    ----------
    directory : str
        Path to the parent directory where the project folder will be created.
    projectName : str
        Name of the new project folder.
    studyName : str
        Name of the piping study to create inside the project.
    screenWidth : int
        Width of the window used to initialize the study (used for UI positioning).
    screenheight : int
        Height of the window used to initialize the study (used for UI positioning).

    Returns
    -------
    str
        Full path of the created project directory if successful; empty string if the project
        folder already exists or creation failed.

    Raises
    ------
    EnvironmentError
        If the setup has not been completed or MetaPiping module is not valid.
    """
    return _core.addPipingProject(directory, projectName, studyName, screenWidth, screenheight)


def addStructureProject(
    directory: str,
    projectName: str,
    studyName: str,
    screenWidth: int,
    screenheight: int
) -> str:
    """
    Add a new project containing a structure study.

    Parameters
    ----------
    directory : str
        Path to the parent directory where the project folder will be created.
    projectName : str
        Name of the new project folder.
    studyName : str
        Name of the structure study to create inside the project.
    screenWidth : int
        Width of the window used to initialize the study (used for UI positioning).
    screenheight : int
        Height of the window used to initialize the study (used for UI positioning).

    Returns
    -------
    str
        Full path of the created project directory if successful; empty string if the project
        folder already exists or creation failed.

    Raises
    ------
    EnvironmentError
        If the setup has not been completed or MetaStructure module is not valid.
    """
    return _core.addStructureProject(directory, projectName, studyName, screenWidth, screenheight)


def removeProject(projectDirectory: str) -> None:
    """
    Remove a project by path.

    Parameters
    ----------
    projectDirectory : str
        Path of the project folder to remove.

    Raises
    ------
    EnvironmentError
        If the setup has not been completed.
    """
    return _core.removeProject(projectDirectory)


def addPipingStudy(
    projectDirectory: str,
    studyName: str,
    screenWidth: int,
    screenheight: int
) -> Optional[Any]:
    """
    Add a piping study to an existing project.

    Parameters
    ----------
    projectDirectory : str
        Path to the project folder.
    studyName : str
        Name of the new study.
    screenWidth : int
        Width of the window used to initialize the study.
    screenheight : int
        Height of the window used to initialize the study.

    Returns
    -------
    Any
        Study object if added successfully, None otherwise.

    Raises
    ------
    EnvironmentError
        If setup or MetaPiping module is invalid.
    """
    return _core.addPipingStudy(projectDirectory, studyName, screenWidth, screenheight)


def addStructureStudy(
    projectDirectory: str,
    studyName: str,
    screenWidth: int,
    screenheight: int
) -> Optional[Any]:
    """
    Add a structure study to an existing project.

    Parameters
    ----------
    projectDirectory : str
        Path to the project folder.
    studyName : str
        Name of the new study.
    screenWidth : int
        Width of the window used to initialize the study.
    screenheight : int
        Height of the window used to initialize the study.

    Returns
    -------
    Any
        Study object if added successfully, None otherwise.

    Raises
    ------
    EnvironmentError
        If setup or MetaStructure module is invalid.
    """
    return _core.addStructureStudy(projectDirectory, studyName, screenWidth, screenheight)


def removeStudy(projectDirectory: str, studyName: str) -> None:
    """
    Remove a study from a project.

    Parameters
    ----------
    projectDirectory : str
        Path to the project folder.
    studyName : str
        Name of the study to remove.

    Raises
    ------
    EnvironmentError
        If setup has not been completed.
    """
    return _core.removeStudy(projectDirectory, studyName)


def duplicateStudy(projectDirectory: str, studyName: str, copyStudyName: str) -> None:
    """
    Duplicate a study in a project.

    Parameters
    ----------
    projectDirectory : str
        Path to the project folder.
    studyName : str
        Name of the study to duplicate.
    copyStudyName : str
        Name for the duplicated study.

    Raises
    ------
    EnvironmentError
        If setup has not been completed.
    """
    return _core.duplicateStudy(projectDirectory, studyName, copyStudyName)
