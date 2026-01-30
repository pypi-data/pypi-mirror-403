# ExSource-Tools

An experimental Python library for validating and using the [ExSource Specification](https://gitlab.com/gitbuilding/exsourcespec) which is in the early stage of development.

## Commands

### Make

This packages adds the following command:

    exsource-make

This will attempt to process `exsource-def.yml` to create inputs. The first instance of this proof of principle implementation supports OpenSCAD, FreeCAD, CadQuery, and EngScript files. Each of these must be installed separately if they are to be used.

***FreeCAD***  
By default FreeCAD exporter will expect there to be a PartDesign Body called `Body`, it can export this to STEP and/or STL. The body to export can be changed by specifying the label of the object with `object-selected` as a parameter. For example:
```yaml
frame:
    name: Main frame
    description: >
        This frame holds the shelf brackets and shelves.
    output-files:
        - output/frame.step
        - output/frame.stl
    source-files:
        - assets/frame.FCStd
    parameters:
        object-selected: "Frame"
    application: freecad
```

***CadQuery***  
The CardQuery export is performed via [cq-cli](https://github.com/CadQuery/cq-cli)

### Check

You can also use the command:

    exsource-check

This will specify what would happen if `exsource-make` was run.

**EngScript**  
EngScript export is performed with the `engscript` cli tool added in EngScript 0.0.2. All files must supply a `generate()` method.
