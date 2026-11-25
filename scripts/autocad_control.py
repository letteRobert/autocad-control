"""Operate a running Autodesk AutoCAD document through Windows ActiveX."""

import argparse
import json
import math
import os
import sys
from pathlib import Path

import pythoncom
from win32com.client import GetActiveObject, VARIANT


def coordinates(values, size):
    if (not isinstance(values, (list, tuple)) or len(values) != size
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in values)):
        raise ValueError(f"Expected {size} finite coordinates")
    return tuple(map(float, values))


def doubles(values):
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, tuple(values))


def point(values):
    return doubles(coordinates(values, 3))


def positive(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError("Expected a positive finite number")
    return float(value)


def active_application(progid):
    try:
        return GetActiveObject(progid)
    except pythoncom.com_error as error:
        raise RuntimeError("No accessible running AutoCAD session. Open a drawing and retry.") from error


def same_path(first, second):
    return os.path.normcase(os.path.abspath(first)) == os.path.normcase(os.path.abspath(second))


def check_document(doc, expected):
    if not isinstance(expected, str) or not expected.strip():
        raise ValueError("Specify the target drawing")
    full_name = doc.FullName
    if full_name and Path(full_name).is_absolute():
        if Path(expected).is_absolute() and same_path(full_name, expected):
            return
    elif expected.casefold() == doc.Name.casefold():
        return
    raise ValueError(f"Target mismatch: active drawing is {doc.FullName!r}")


def summary(doc):
    variables = ("INSUNITS", "UCSNAME", "UCSORG", "UCSXDIR", "UCSYDIR", "CMDACTIVE")
    return {
        "name": doc.Name, "path": doc.FullName, "saved": bool(doc.Saved),
        "active_layout": doc.ActiveLayout.Name, "model_count": doc.ModelSpace.Count,
        "layouts": [item.Name for item in doc.Layouts],
        "layers": [item.Name for item in doc.Layers],
        "variables": {name: doc.GetVariable(name) for name in variables},
    }


def entity_info(doc, entity):
    kind = entity.ObjectName
    result = {"handle": entity.Handle, "type": kind, "layer": entity.Layer}
    if kind == "AcDbLine":
        result.update(start_wcs=entity.StartPoint, end_wcs=entity.EndPoint, length=entity.Length)
    elif kind == "AcDbCircle":
        result.update(center_wcs=entity.Center, radius=entity.Radius, area=entity.Area)
    elif kind == "AcDbPolyline":
        xy = entity.Coordinates
        normal = doubles(entity.Normal)
        # acOCS = 4, acWorld = 0. LWPolyline coordinates are stored in OCS.
        vertices = [doc.Utility.TranslateCoordinates(
            point((x, y, entity.Elevation)), 4, 0, False, normal
        ) for x, y in zip(xy[::2], xy[1::2])]
        result.update(vertices_wcs=vertices, closed=bool(entity.Closed), length=entity.Length)
        if result["closed"]:
            result["area"] = entity.Area
    elif kind in ("AcDbText", "AcDbMText", "AcDbAttributeReference"):
        result.update(text=entity.TextString, insertion_wcs=entity.InsertionPoint)
    elif kind == "AcDbBlockReference":
        result.update(name=entity.EffectiveName, insertion_wcs=entity.InsertionPoint)
    return result


def draw(doc, spec):
    space = doc.Layouts.Item(spec["layout"]).Block if "layout" in spec else doc.ModelSpace
    layer = doc.Layers.Item(spec["layer"]) if "layer" in spec else doc.ActiveLayer
    if layer.Lock:
        raise ValueError(f"Layer is locked: {layer.Name}")
    kind = spec["type"]
    if kind == "line":
        entity = space.AddLine(point(spec["start"]), point(spec["end"]))
    elif kind == "circle":
        entity = space.AddCircle(point(spec["center"]), positive(spec["radius"]))
    elif kind == "text":
        value = spec["text"]
        if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
            raise ValueError("Expected nonempty single-line text")
        entity = space.AddText(value, point(spec["at"]), positive(spec["height"]))
    elif kind == "polyline":
        vertices = [coordinates(vertex, 2) for vertex in spec["vertices"]]
        closed = spec.get("closed", False)
        if not isinstance(closed, bool) or len(set(vertices)) < (3 if closed else 2):
            raise ValueError("Polyline needs distinct vertices and a Boolean closed flag")
        if (any(a == b for a, b in zip(vertices, vertices[1:]))
                or (closed and vertices[0] == vertices[-1])):
            raise ValueError("Remove repeated consecutive vertices and omit the closing duplicate")
        entity = space.AddLightWeightPolyline(doubles(v for vertex in vertices for v in vertex))
    else:
        raise ValueError(f"Unsupported draw type: {kind}")
    try:
        if kind == "polyline":
            entity.Normal = point((0, 0, 1))
            entity.Elevation = 0.0
            entity.Coordinates = doubles(v for vertex in vertices for v in vertex)
            entity.Closed = closed
        entity.Layer = layer.Name
        return entity_info(doc, entity)
    except Exception:
        entity.Delete()
        raise


def move(doc, spec):
    handles = spec["handles"]
    if not isinstance(handles, list) or not handles or any(not isinstance(h, str) for h in handles):
        raise ValueError("Provide a nonempty list of verified entity handles")
    if len({handle.upper() for handle in handles}) != len(handles):
        raise ValueError("Duplicate handle in move selection")
    source, target = point(spec["from"]), point(spec["to"])
    entities = [doc.HandleToObject(handle) for handle in handles]
    for entity in entities:
        if not entity.ObjectName.startswith("AcDb") or doc.Layers.Item(entity.Layer).Lock:
            raise ValueError(f"Entity is locked or unsupported: {entity.Handle}")
    moved = []
    try:
        for entity in entities:
            entity.Move(source, target)
            moved.append(entity.Handle)
    except Exception as error:
        raise RuntimeError(f"Move interrupted; confirmed moved handles: {moved}. Inspect drawing.") from error
    return {"moved": moved}


def save(doc, spec):
    if "path" in spec:
        path = Path(spec["path"])
        if not path.is_absolute() or path.suffix.lower() != ".dwg" or path.exists() or not path.parent.is_dir():
            raise ValueError("SaveAs requires a new absolute .dwg path in an existing directory")
        doc.SaveAs(str(path))
    else:
        if not Path(doc.FullName).is_absolute() or not Path(doc.FullName).is_file():
            raise ValueError("Unsaved drawing requires a new absolute path")
        path = Path(doc.FullName)
        doc.Save()
    if not same_path(doc.FullName, path) or not doc.Saved or path.stat().st_size <= 0:
        raise RuntimeError("AutoCAD or disk did not confirm the save; check both before retrying")
    return {"path": str(path), "bytes": path.stat().st_size}


def query(doc, spec):
    limit = spec.get("limit", 200)
    if type(limit) is not int or not 1 <= limit <= 10000:
        raise ValueError("limit must be an integer between 1 and 10000")
    kind = spec.get("type")
    space = doc.Layouts.Item(spec["layout"]).Block if "layout" in spec else doc.ModelSpace
    items, total = [], 0
    for entity in space:
        if kind and entity.ObjectName != kind:
            continue
        total += 1
        if len(items) < limit:
            items.append(entity_info(doc, entity))
    return {"space": spec.get("layout", "Model"), "total": total, "truncated": total > limit, "items": items}


def convert(doc, spec):
    systems = {"wcs": 0, "ucs": 1}
    source, target = spec["from"], spec["to"]
    if source not in systems or target not in systems:
        raise ValueError("Coordinate conversion supports wcs and ucs")
    values = coordinates(spec["point"], 3)
    if source != target:
        values = doc.Utility.TranslateCoordinates(point(values), systems[source], systems[target], False)
    return {"point": values, "system": target}


def execute(doc, expected, spec):
    if not isinstance(spec, dict):
        raise ValueError("Request must be one JSON object")
    operation = spec["op"]
    check_document(doc, expected)
    if operation in {"draw", "move", "save"} and (doc.ReadOnly or doc.GetVariable("CMDACTIVE")):
        raise ValueError("Drawing is read-only or AutoCAD has an active command")
    if operation == "entity":
        return entity_info(doc, doc.HandleToObject(spec["handle"]))
    handlers = {"query": query, "draw": draw, "move": move, "save": save, "convert": convert}
    if operation not in handlers:
        raise ValueError(f"Unknown operation: {operation}")
    return handlers[operation](doc, spec)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progid", default="AutoCAD.Application")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Read active drawing identity and settings")
    call = sub.add_parser("call", help="Run one JSON request in a confirmed drawing")
    call.add_argument("--document", required=True)
    call.add_argument("--json-file", required=True, type=Path)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    pythoncom.CoInitialize()
    try:
        request = json.loads(args.json_file.read_text(encoding="utf-8-sig")) if args.command == "call" else None
        app = active_application(args.progid)
        if app.Documents.Count == 0:
            raise RuntimeError("AutoCAD has no open drawing")
        doc = app.ActiveDocument
        result = summary(doc) if args.command == "check" else execute(doc, args.document, request)
        print(json.dumps({"ok": True, "version": app.Version, "result": result}, ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    raise SystemExit(main())
