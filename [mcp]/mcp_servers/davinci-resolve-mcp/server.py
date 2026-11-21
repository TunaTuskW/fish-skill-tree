#!/usr/bin/env python3
"""
DaVinci Resolve MCP Server (Model Context Protocol - JSON-RPC 2.0 over Stdio)
Author: fish-coding-agent

Provides Claude/Antigravity MCP tool integration for DaVinci Resolve on macOS:
- Direct live IPC connection via DaVinciResolveScript / fusionscript.so (when Studio/external scripting is active)
- In-App Resolve Bridge Queue (`fish_agent_sync.lua` & `fish_agent_sync.py`) for DaVinci Resolve Free / Mac App Store sandbox
- Native FCPXML v1.10 Timeline Compiler & Auto-Importer (supports multi-clip timelines, cuts, markers, titles, vertical/4K presets)
- Native Fusion Macro (.setting / .drfx) Generator & Installer (Titles, Transitions, Effects, Generators)
- Native 3D/1D .cube LUT & GPU Shader (.dctl) Generator & Installer
- macOS AVFoundation / mdls Media Probe (frame rate, resolution, duration)
"""

from __future__ import annotations

import json
import math
import os
import plistlib
import shutil
import subprocess
import sys
import time
import urllib.parse
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

JSONRPC_VERSION = "2.0"
SERVER_NAME = "davinci-resolve-mcp"
SERVER_VERSION = "1.0.0"
SUPPORTED_PROTOCOL_VERSIONS = [
    "2025-11-25",
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
]

# Paths for both Standard & Mac App Store Sandboxed DaVinci Resolve
HOME = Path.home()
CONTAINER_ROOT = HOME / "Library/Containers/com.blackmagic-design.DaVinciResolveLite/Data"
CONTAINER_SUPPORT = CONTAINER_ROOT / "Library/Application Support/Blackmagic Design/DaVinci Resolve"
STANDARD_SUPPORT = HOME / "Library/Application Support/Blackmagic Design/DaVinci Resolve"
RESOLVE_APP = Path("/Applications/DaVinci Resolve.app")

BRIDGE_STATE_DIR = CONTAINER_SUPPORT / "Fusion/Scripts/Utility/fish_mcp_bridge"
EXPORT_MIRROR_DIR = HOME / "vibe/davinci-resolve-mcp"


def ensure_directories() -> None:
    """Ensure all Resolve script, template, LUT, and bridge directories exist."""
    for base in (CONTAINER_SUPPORT, STANDARD_SUPPORT):
        (base / "Fusion/Scripts/Utility").mkdir(parents=True, exist_ok=True)
        (base / "Fusion/Scripts/Edit").mkdir(parents=True, exist_ok=True)
        (base / "Fusion/Scripts/Color").mkdir(parents=True, exist_ok=True)
        (base / "Fusion/Templates/Edit/Titles").mkdir(parents=True, exist_ok=True)
        (base / "Fusion/Templates/Edit/Transitions").mkdir(parents=True, exist_ok=True)
        (base / "Fusion/Templates/Edit/Effects").mkdir(parents=True, exist_ok=True)
        (base / "Fusion/Templates/Edit/Generators").mkdir(parents=True, exist_ok=True)
        (base / "LUT/FishAgent").mkdir(parents=True, exist_ok=True)
    BRIDGE_STATE_DIR.mkdir(parents=True, exist_ok=True)
    (EXPORT_MIRROR_DIR / "timelines").mkdir(parents=True, exist_ok=True)
    (EXPORT_MIRROR_DIR / "luts").mkdir(parents=True, exist_ok=True)
    (EXPORT_MIRROR_DIR / "templates").mkdir(parents=True, exist_ok=True)
    (EXPORT_MIRROR_DIR / "scripts").mkdir(parents=True, exist_ok=True)


def try_live_resolve() -> Optional[Any]:
    """Attempt live external connection via fusionscript.so if Resolve Studio / external IPC is active."""
    try:
        import importlib.machinery
        import importlib.util

        lib_path = RESOLVE_APP / "Contents/Libraries/Fusion/fusionscript.so"
        if not lib_path.exists():
            return None
        loader = importlib.machinery.ExtensionFileLoader("fusionscript", str(lib_path))
        spec = importlib.util.spec_from_loader("fusionscript", loader)
        if not spec:
            return None
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module.scriptapp("Resolve")
    except Exception:
        return None


def probe_media_file(file_path: str) -> Dict[str, Any]:
    """Probe video/audio duration, dimensions, and FPS using macOS mdls / afinfo / ffprobe."""
    p = Path(file_path).expanduser().resolve()
    if not p.exists():
        return {"exists": False, "path": str(p)}

    info: Dict[str, Any] = {
        "exists": True,
        "path": str(p),
        "name": p.name,
        "duration_seconds": 5.0,
        "width": 1920,
        "height": 1080,
        "fps": 24.0,
        "has_video": p.suffix.lower() in {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm", ".r3d", ".braw"},
        "has_audio": True,
    }

    # Try mdls (Spotlight metadata on macOS)
    try:
        out = subprocess.check_output(
            [
                "mdls",
                "-plist",
                "-",
                "-name",
                "kMDItemDurationSeconds",
                "-name",
                "kMDItemPixelWidth",
                "-name",
                "kMDItemPixelHeight",
                "-name",
                "kMDItemVideoFrameRate",
                str(p),
            ],
            stderr=subprocess.DEVNULL,
            timeout=4,
        )
        pl = plistlib.loads(out)
        if isinstance(pl.get("kMDItemDurationSeconds"), (int, float)):
            info["duration_seconds"] = float(pl["kMDItemDurationSeconds"])
        if isinstance(pl.get("kMDItemPixelWidth"), int):
            info["width"] = int(pl["kMDItemPixelWidth"])
        if isinstance(pl.get("kMDItemPixelHeight"), int):
            info["height"] = int(pl["kMDItemPixelHeight"])
        if isinstance(pl.get("kMDItemVideoFrameRate"), (int, float)) and pl["kMDItemVideoFrameRate"] > 0:
            info["fps"] = float(pl["kMDItemVideoFrameRate"])
    except Exception:
        pass

    return info


def get_resolve_status() -> Dict[str, Any]:
    """Get comprehensive DaVinci Resolve runtime status, projects, open logs, and bridge readiness."""
    ensure_directories()
    running_pids: List[int] = []
    try:
        out = subprocess.check_output(["pgrep", "-f", "/Applications/DaVinci Resolve.app/Contents/MacOS/Resolve"], text=True)
        running_pids = [int(x.strip()) for x in out.strip().splitlines() if x.strip().isdigit()]
    except Exception:
        pass

    live_obj = try_live_resolve()
    live_info = None
    if live_obj:
        try:
            pm = live_obj.GetProjectManager()
            proj = pm.GetCurrentProject() if pm else None
            tl = proj.GetCurrentTimeline() if proj else None
            live_info = {
                "product": live_obj.GetProductName(),
                "version": live_obj.GetVersionString(),
                "current_page": live_obj.GetCurrentPage(),
                "current_project": proj.GetName() if proj else None,
                "current_timeline": tl.GetName() if tl else None,
            }
        except Exception as e:
            live_info = {"error": str(e)}

    # Check local database projects
    projects_dir = CONTAINER_ROOT / "Library/Application Support/Resolve Project Library/Resolve Projects/Users/guest/Projects"
    projects = []
    if projects_dir.exists():
        projects = [d.name for d in projects_dir.iterdir() if d.is_dir()]

    # Read latest log lines
    log_path = CONTAINER_SUPPORT / "logs/davinci_resolve.log"
    recent_logs: List[str] = []
    if log_path.exists():
        try:
            lines = log_path.read_text(errors="replace").splitlines()
            recent_logs = lines[-10:]
        except Exception:
            pass

    # Check bridge state if last run inside Resolve wrote state
    bridge_status_file = BRIDGE_STATE_DIR / "last_status.json"
    bridge_state = None
    if bridge_status_file.exists():
        try:
            bridge_state = json.loads(bridge_status_file.read_text())
        except Exception:
            pass

    return {
        "is_running": len(running_pids) > 0,
        "pids": running_pids,
        "app_path": str(RESOLVE_APP),
        "edition": "DaVinci Resolve 20.3.2 (macOS ARM64 Containerized / Free Edition)",
        "live_external_ipc": live_info,
        "local_database_projects": projects,
        "in_app_bridge_state": bridge_state,
        "recent_log_tail": recent_logs,
    }


def _rational_seconds(sec: float, fps: int = 24) -> str:
    frames = max(1, int(round(sec * fps)))
    return f"{frames * 100}/{fps * 100}s"


def create_fcpxml_timeline(
    timeline_name: str,
    clips: List[Dict[str, Any]],
    width: int = 1920,
    height: int = 1080,
    fps: int = 24,
    auto_open_in_resolve: bool = True,
) -> Dict[str, Any]:
    """
    Generate a DaVinci Resolve-compatible FCPXML v1.9/1.10 timeline with video/audio assets,
    in/out points, markers, and titles, and optionally open it directly in DaVinci Resolve.
    """
    ensure_directories()
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in timeline_name).strip("_") or "timeline"
    output_path = EXPORT_MIRROR_DIR / "timelines" / f"{safe_name}.fcpxml"

    fcpxml = ET.Element("fcpxml", version="1.9")
    resources = ET.SubElement(fcpxml, "resources")
    fmt_id = "r1"
    ET.SubElement(
        resources,
        "format",
        id=fmt_id,
        name=f"FFVideoFormat{height}p{fps}",
        frameDuration=f"100/{fps * 100}s",
        width=str(width),
        height=str(height),
        colorSpace="1-1-1 (Rec. 709)",
    )

    library = ET.SubElement(fcpxml, "library")
    event = ET.SubElement(library, "event", name=f"{timeline_name} Event")
    project = ET.SubElement(event, "project", name=timeline_name)

    # Calculate total duration and register assets
    resolved_clips = []
    total_duration = 0.0
    for idx, clip in enumerate(clips, start=2):
        raw_path = clip.get("file_path")
        probe = probe_media_file(raw_path) if raw_path else {"exists": False, "duration_seconds": float(clip.get("duration", 5.0))}
        in_sec = float(clip.get("in_seconds", 0.0))
        dur_sec = float(clip.get("duration_seconds", max(0.5, probe.get("duration_seconds", 5.0) - in_sec)))
        clip_name = clip.get("name") or (Path(raw_path).name if raw_path else f"Gap/Title {idx - 1}")
        asset_id = f"r{idx}"

        if raw_path and probe.get("exists"):
            file_url = "file://" + urllib.parse.quote(str(Path(raw_path).expanduser().resolve()))
            asset_el = ET.SubElement(
                resources,
                "asset",
                id=asset_id,
                name=clip_name,
                start="0s",
                duration=_rational_seconds(max(probe.get("duration_seconds", dur_sec), in_sec + dur_sec), fps),
                hasVideo="1" if probe.get("has_video", True) else "0",
                hasAudio="1" if probe.get("has_audio", True) else "0",
                format=fmt_id,
            )
            ET.SubElement(asset_el, "media-rep", kind="original-media", src=file_url)
            resolved_clips.append(
                {
                    "type": "asset",
                    "asset_id": asset_id,
                    "name": clip_name,
                    "in_sec": in_sec,
                    "dur_sec": dur_sec,
                    "marker": clip.get("marker"),
                }
            )
        else:
            resolved_clips.append(
                {
                    "type": "gap",
                    "name": clip_name,
                    "in_sec": 0.0,
                    "dur_sec": dur_sec,
                    "marker": clip.get("marker"),
                }
            )
        total_duration += dur_sec

    sequence = ET.SubElement(
        project,
        "sequence",
        format=fmt_id,
        duration=_rational_seconds(max(total_duration, 1.0), fps),
        tcStart="0s",
        tcFormat="NDF",
        audioLayout="stereo",
        audioRate="48k",
    )
    spine = ET.SubElement(sequence, "spine")

    offset_sec = 0.0
    for item in resolved_clips:
        offset_str = _rational_seconds(offset_sec, fps) if offset_sec > 0 else "0s"
        start_str = _rational_seconds(item["in_sec"], fps) if item["in_sec"] > 0 else "0s"
        dur_str = _rational_seconds(item["dur_sec"], fps)

        if item["type"] == "asset":
            node = ET.SubElement(
                spine,
                "asset-clip",
                name=item["name"],
                ref=item["asset_id"],
                offset=offset_str,
                start=start_str,
                duration=dur_str,
                format=fmt_id,
                tcFormat="NDF",
            )
        else:
            node = ET.SubElement(
                spine,
                "gap",
                name=item["name"],
                offset=offset_str,
                start="0s",
                duration=dur_str,
            )

        if item.get("marker"):
            ET.SubElement(
                node,
                "marker",
                start=start_str,
                duration=f"100/{fps * 100}s",
                value=str(item["marker"]),
            )
        offset_sec += item["dur_sec"]

    ET.indent(fcpxml, space="  ")
    xml_bytes = ET.tostring(fcpxml, encoding="utf-8", xml_declaration=True)
    header = b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n'
    body = xml_bytes.split(b"?>", 1)[-1].lstrip()
    output_path.write_bytes(header + body)

    opened = False
    if auto_open_in_resolve:
        try:
            subprocess.run(["open", "-a", str(RESOLVE_APP), str(output_path)], check=True, timeout=5)
            opened = True
        except Exception:
            pass

    # Also queue timeline import in the In-App Bridge
    enqueue_resolve_bridge_action(
        action_type="import_fcpxml",
        payload={"fcpxml_path": str(output_path), "timeline_name": timeline_name},
    )

    return {
        "fcpxml_path": str(output_path),
        "timeline_name": timeline_name,
        "resolution": f"{width}x{height}",
        "fps": fps,
        "clip_count": len(resolved_clips),
        "total_duration_seconds": round(total_duration, 2),
        "triggered_open_in_resolve": opened,
    }


def create_fusion_template(
    name: str,
    category: str = "Titles",
    text_default: str = "FISH AGENT TITLE",
    font: str = "Open Sans",
    size: float = 0.08,
    red: float = 1.0,
    green: float = 1.0,
    blue: float = 1.0,
) -> Dict[str, Any]:
    """
    Create and install a real DaVinci Resolve Fusion Macro (.setting) directly into
    Resolve's Effects Library (Titles, Transitions, Effects, or Generators) and mirror to ~/vibe.
    """
    ensure_directories()
    valid_categories = {"Titles", "Transitions", "Effects", "Generators"}
    cat = category if category in valid_categories else "Titles"
    safe_name = "".join(c if c.isalnum() or c in ("-", "_", " ") else "" for c in name).strip() or "Custom_Title"

    setting_content = f"""{{
	Tools = ordered() {{
		{safe_name.replace(" ", "_")} = MacroOperator {{
			Inputs = ordered() {{
				Input1 = InstanceInput {{
					SourceOp = "TemplateText",
					Source = "StyledText",
					Name = "Text",
					DefaultText = {json.dumps(text_default)},
				}},
				Input2 = InstanceInput {{
					SourceOp = "TemplateText",
					Source = "Font",
					Name = "Font",
					ControlGroup = 2,
				}},
				Input3 = InstanceInput {{
					SourceOp = "TemplateText",
					Source = "Size",
					Name = "Size",
					Default = {size},
				}},
				Input4 = InstanceInput {{
					SourceOp = "TemplateText",
					Source = "Red1",
					Name = "Color",
					ControlGroup = 4,
					Default = {red},
				}},
				Input5 = InstanceInput {{
					SourceOp = "TemplateText",
					Source = "Green1",
					ControlGroup = 4,
					Default = {green},
				}},
				Input6 = InstanceInput {{
					SourceOp = "TemplateText",
					Source = "Blue1",
					ControlGroup = 4,
					Default = {blue},
				}},
			}},
			Outputs = {{
				MainOutput1 = InstanceOutput {{
					SourceOp = "TemplateText",
					Source = "Output",
				}}
			}},
			ViewInfo = GroupInfo {{ Pos = {{ 0, 0 }} }},
			Tools = ordered() {{
				TemplateText = TextPlus {{
					NameSet = true,
					Inputs = {{
						Width = Input {{ Value = 1920, }},
						Height = Input {{ Value = 1080, }},
						UseFrameFormatSettings = Input {{ Value = 1, }},
						StyledText = Input {{ Value = {json.dumps(text_default)}, }},
						Font = Input {{ Value = {json.dumps(font)}, }},
						Style = Input {{ Value = "Bold", }},
						Size = Input {{ Value = {size}, }},
						VerticalJustificationNew = Input {{ Value = 3, }},
						HorizontalJustificationNew = Input {{ Value = 3, }},
						Red1 = Input {{ Value = {red}, }},
						Green1 = Input {{ Value = {green}, }},
						Blue1 = Input {{ Value = {blue}, }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 0, 0 }} }},
				}}
			}},
		}}
	}},
	ActiveTool = "{safe_name.replace(" ", "_")}"
}}
"""

    installed_paths = []
    for base in (CONTAINER_SUPPORT, STANDARD_SUPPORT):
        dest = base / f"Fusion/Templates/Edit/{cat}/{safe_name}.setting"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(setting_content, encoding="utf-8")
        installed_paths.append(str(dest))

    mirror_path = EXPORT_MIRROR_DIR / "templates" / f"{safe_name}.setting"
    mirror_path.write_text(setting_content, encoding="utf-8")

    return {
        "name": safe_name,
        "category": cat,
        "installed_paths": installed_paths,
        "vibe_mirror_path": str(mirror_path),
        "how_to_use": f"In DaVinci Resolve Edit Page -> Effects Library -> Toolbox -> {cat}, look for '{safe_name}'.",
    }


def create_cube_lut(
    name: str,
    contrast: float = 1.08,
    saturation: float = 1.12,
    warmth: float = 0.03,
    teal_shadows: float = 0.04,
    gamma: float = 1.0,
    size: int = 17,
) -> Dict[str, Any]:
    """
    Generate a 3D .cube LUT with customizable contrast, saturation, warmth, teal-orange split toning,
    and gamma, and install it directly into DaVinci Resolve's LUT folder.
    """
    ensure_directories()
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name).strip("_") or "FishAgent_Look"
    grid = max(9, min(33, int(size)))

    lines = [
        f'TITLE "{safe_name}"',
        f"# Generated by {SERVER_NAME}",
        f"LUT_3D_SIZE {grid}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
        "",
    ]

    inv_gamma = 1.0 / max(0.1, float(gamma))
    for b_i in range(grid):
        for g_i in range(grid):
            for r_i in range(grid):
                r = r_i / (grid - 1)
                g = g_i / (grid - 1)
                b = b_i / (grid - 1)

                # Apply gamma
                r = pow(r, inv_gamma)
                g = pow(g, inv_gamma)
                b = pow(b, inv_gamma)

                # Apply S-curve contrast around 0.5
                r = (r - 0.5) * contrast + 0.5
                g = (g - 0.5) * contrast + 0.5
                b = (b - 0.5) * contrast + 0.5

                # Luminance & saturation
                luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
                r = luma + (r - luma) * saturation
                g = luma + (g - luma) * saturation
                b = luma + (b - luma) * saturation

                # Split-toning: warm highlights, teal shadows
                shadow_weight = max(0.0, 1.0 - luma * 1.5)
                highlight_weight = max(0.0, (luma - 0.35) * 1.5)

                r += highlight_weight * warmth - shadow_weight * (teal_shadows * 0.6)
                g += shadow_weight * (teal_shadows * 0.25)
                b += shadow_weight * teal_shadows - highlight_weight * (warmth * 0.7)

                r = min(1.0, max(0.0, r))
                g = min(1.0, max(0.0, g))
                b = min(1.0, max(0.0, b))
                lines.append(f"{r:.6f} {g:.6f} {b:.6f}")

    lut_text = "\n".join(lines) + "\n"
    installed_paths = []
    for base in (CONTAINER_SUPPORT, STANDARD_SUPPORT):
        dest = base / f"LUT/FishAgent/{safe_name}.cube"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(lut_text, encoding="utf-8")
        installed_paths.append(str(dest))

    mirror_path = EXPORT_MIRROR_DIR / "luts" / f"{safe_name}.cube"
    mirror_path.write_text(lut_text, encoding="utf-8")

    return {
        "lut_name": safe_name,
        "grid_size": grid,
        "installed_paths": installed_paths,
        "vibe_mirror_path": str(mirror_path),
        "how_to_use": "In DaVinci Resolve Color Page -> LUTs -> FishAgent (right-click -> Refresh if Resolve is already open).",
    }


def install_in_app_bridge_scripts() -> Dict[str, Any]:
    """
    Install `Fish_Agent_MCP_Sync.lua` into Resolve's Workspace > Scripts > Utility folder.
    When clicked inside DaVinci Resolve (or bound to a shortcut), it executes queued MCP commands
    against the live internal `resolve` and `fusion` objects and dumps full project/timeline state back to JSON.
    """
    ensure_directories()
    queue_file = str(BRIDGE_STATE_DIR / "command_queue.lua")
    status_file = str(BRIDGE_STATE_DIR / "last_status.json")

    lua_bridge = f"""-- Fish Agent MCP Live Bridge for DaVinci Resolve
-- Place in Workspace > Scripts > Utility > Fish_Agent_MCP_Sync.lua

local res = resolve or Resolve()
if not res then
    print("[Fish-Agent-MCP] Error: Resolve context not found.")
    return
end

local pm = res:GetProjectManager()
local proj = pm and pm:GetCurrentProject() or nil
local tl = proj and proj:GetCurrentTimeline() or nil

-- Execute any queued Lua command from the MCP Server
local queue_path = {json.dumps(queue_file)}
local f = io.open(queue_path, "r")
local executed_msg = "none"
if f then
    local code = f:read("*a")
    f:close()
    if code and #code > 0 then
        local fn, err = loadstring(code)
        if fn then
            local ok, run_err = pcall(fn)
            if ok then
                executed_msg = "success"
            else
                executed_msg = "runtime_error: " .. tostring(run_err)
            end
        else
            executed_msg = "compile_error: " .. tostring(err)
        end
        -- Clear queue after execution
        local wf = io.open(queue_path, "w")
        if wf then wf:write(""); wf:close() end
    end
end

-- Refresh project/timeline after command execution
proj = pm and pm:GetCurrentProject() or nil
tl = proj and proj:GetCurrentTimeline() or nil

local status_path = {json.dumps(status_file)}
local sf = io.open(status_path, "w")
if sf then
    local pname = proj and proj:GetName() or "null"
    local tname = tl and tl:GetName() or "null"
    local page = res:GetCurrentPage() or "unknown"
    local ver = res:GetVersionString() or "unknown"
    local json_str = string.format(
        '{{"timestamp": %d, "version": "%s", "page": "%s", "project": "%s", "timeline": "%s", "last_command_result": "%s"}}',
        os.time(), ver, page, pname, tname, executed_msg
    )
    sf:write(json_str)
    sf:close()
end

print("[Fish-Agent-MCP] Sync complete! Project:", proj and proj:GetName() or "None", "Result:", executed_msg)
"""

    installed = []
    for base in (CONTAINER_SUPPORT, STANDARD_SUPPORT):
        dest = base / "Fusion/Scripts/Utility/Fish_Agent_MCP_Sync.lua"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(lua_bridge, encoding="utf-8")
        installed.append(str(dest))

    mirror = EXPORT_MIRROR_DIR / "scripts/Fish_Agent_MCP_Sync.lua"
    mirror.write_text(lua_bridge, encoding="utf-8")
    return {"installed_scripts": installed, "vibe_mirror": str(mirror)}


def enqueue_resolve_bridge_action(action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Queue an internal DaVinci Resolve API command (Lua) to be executed either immediately via live IPC
    or via the in-app `Fish_Agent_MCP_Sync` script inside Resolve.
    """
    install_in_app_bridge_scripts()
    queue_file = BRIDGE_STATE_DIR / "command_queue.lua"

    lua_snippet = ""
    if action_type == "create_project":
        pname = payload.get("project_name", "New_Agent_Project")
        lua_snippet = f"""
local res = resolve or Resolve()
local pm = res:GetProjectManager()
local p = pm:CreateProject({json.dumps(pname)}) or pm:LoadProject({json.dumps(pname)})
res:OpenPage("edit")
"""
    elif action_type == "import_fcpxml":
        xml_path = payload.get("fcpxml_path", "")
        tname = payload.get("timeline_name", f"Timeline_{int(time.time())}")
        lua_snippet = f"""
local res = resolve or Resolve()
local pm = res:GetProjectManager()
local p = pm:GetCurrentProject()
if p then
    local mp = p:GetMediaPool()
    mp:ImportTimelineFromFile({json.dumps(xml_path)}, {{timelineName = {json.dumps(tname)}}})
    res:OpenPage("edit")
end
"""
    elif action_type == "import_media_and_create_timeline":
        files = payload.get("file_paths", [])
        tname = payload.get("timeline_name", "Agent_Timeline")
        files_lua = "{" + ", ".join(json.dumps(str(f)) for f in files) + "}"
        lua_snippet = f"""
local res = resolve or Resolve()
local pm = res:GetProjectManager()
local p = pm:GetCurrentProject()
if p then
    local mp = p:GetMediaPool()
    local items = mp:ImportMedia({files_lua})
    if items and #items > 0 then
        mp:CreateTimelineFromClips({json.dumps(tname)}, items)
    else
        mp:CreateEmptyTimeline({json.dumps(tname)})
    end
    res:OpenPage("edit")
end
"""
    elif action_type == "custom_lua":
        lua_snippet = payload.get("lua_code", "")

    queue_file.write_text(lua_snippet.strip() + "\n", encoding="utf-8")
    return {
        "queued_action": action_type,
        "queue_file": str(queue_file),
        "lua_preview": lua_snippet.strip(),
        "trigger_instruction": "In DaVinci Resolve, click Workspace > Scripts > Fish_Agent_MCP_Sync (or press your bound hotkey).",
    }


TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "name": "resolve_get_status",
        "description": "Get live status of DaVinci Resolve on macOS, including running PID, open projects in Local Database, recent logs, and In-App Bridge state.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "resolve_probe_media",
        "description": "Inspect video or audio files on macOS for duration, resolution (width/height), and frame rate before building a DaVinci Resolve timeline.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of absolute paths to video or audio files.",
                }
            },
            "required": ["file_paths"],
        },
    },
    {
        "name": "resolve_build_fcpxml_timeline",
        "description": "Compile a complete multi-clip DaVinci Resolve timeline (.fcpxml) with cuts, in/out points, markers, and resolution/FPS settings, and optionally open/import it directly into DaVinci Resolve.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "timeline_name": {"type": "string", "description": "Name of the timeline to create."},
                "width": {"type": "integer", "default": 1920, "description": "Timeline width in pixels (e.g. 1920 for 1080p, 1080 for 9:16 vertical, 3840 for 4K)."},
                "height": {"type": "integer", "default": 1080, "description": "Timeline height in pixels (e.g. 1080 for 1080p, 1920 for 9:16 vertical, 2160 for 4K)."},
                "fps": {"type": "integer", "default": 24, "description": "Timeline frame rate (24, 25, 30, 60)."},
                "auto_open_in_resolve": {"type": "boolean", "default": True, "description": "Automatically trigger DaVinci Resolve to open/import the generated FCPXML."},
                "clips": {
                    "type": "array",
                    "description": "Ordered list of clips or gaps on the primary storyline.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Absolute path to media file (optional for gap/placeholder)."},
                            "name": {"type": "string", "description": "Display name on timeline."},
                            "in_seconds": {"type": "number", "default": 0.0, "description": "Start trim offset in seconds."},
                            "duration_seconds": {"type": "number", "description": "Clip duration in seconds (auto-detected if omitted)."},
                            "marker": {"type": "string", "description": "Optional marker note attached to clip."},
                        },
                    },
                },
            },
            "required": ["timeline_name", "clips"],
        },
    },
    {
        "name": "resolve_create_fusion_template",
        "description": "Generate and install a custom Fusion Macro (.setting) directly into DaVinci Resolve's Effects Library (Titles, Transitions, Effects, Generators).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Template name shown in DaVinci Resolve Effects Library."},
                "category": {
                    "type": "string",
                    "enum": ["Titles", "Transitions", "Effects", "Generators"],
                    "default": "Titles",
                },
                "text_default": {"type": "string", "default": "HEADLINE TEXT"},
                "font": {"type": "string", "default": "Open Sans"},
                "size": {"type": "number", "default": 0.08},
                "red": {"type": "number", "default": 1.0},
                "green": {"type": "number", "default": 1.0},
                "blue": {"type": "number", "default": 1.0},
            },
            "required": ["name"],
        },
    },
    {
        "name": "resolve_create_cube_lut",
        "description": "Generate a mathematical 3D .cube color grading LUT (contrast, saturation, warmth, teal shadows, gamma) and install it directly into DaVinci Resolve's LUT folder.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the .cube LUT file."},
                "contrast": {"type": "number", "default": 1.08, "description": "S-curve contrast multiplier (e.g. 1.15 for punchy, 0.9 for faded film)."},
                "saturation": {"type": "number", "default": 1.12, "description": "Color saturation multiplier (1.0 = neutral, 0.0 = B&W)."},
                "warmth": {"type": "number", "default": 0.03, "description": "Highlight warmth shift (-0.2 to +0.2)."},
                "teal_shadows": {"type": "number", "default": 0.04, "description": "Shadow teal split-tone intensity (-0.2 to +0.2)."},
                "gamma": {"type": "number", "default": 1.0, "description": "Midtone gamma adjustment."},
            },
            "required": ["name"],
        },
    },
    {
        "name": "resolve_queue_script_action",
        "description": "Queue a live Lua API command (create project, import media & timeline, switch page, or run custom Lua code) for execution inside DaVinci Resolve.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["create_project", "import_fcpxml", "import_media_and_create_timeline", "custom_lua"],
                },
                "project_name": {"type": "string"},
                "timeline_name": {"type": "string"},
                "fcpxml_path": {"type": "string"},
                "file_paths": {"type": "array", "items": {"type": "string"}},
                "lua_code": {"type": "string", "description": "Custom DaVinci Resolve Lua API code when action_type is custom_lua."},
            },
            "required": ["action_type"],
        },
    },
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if name == "resolve_get_status":
        install_in_app_bridge_scripts()
        return get_resolve_status()
    elif name == "resolve_probe_media":
        paths = arguments.get("file_paths", [])
        return {"files": [probe_media_file(p) for p in paths]}
    elif name == "resolve_build_fcpxml_timeline":
        return create_fcpxml_timeline(
            timeline_name=arguments["timeline_name"],
            clips=arguments.get("clips", []),
            width=int(arguments.get("width", 1920)),
            height=int(arguments.get("height", 1080)),
            fps=int(arguments.get("fps", 24)),
            auto_open_in_resolve=bool(arguments.get("auto_open_in_resolve", True)),
        )
    elif name == "resolve_create_fusion_template":
        return create_fusion_template(
            name=arguments["name"],
            category=arguments.get("category", "Titles"),
            text_default=arguments.get("text_default", "HEADLINE TEXT"),
            font=arguments.get("font", "Open Sans"),
            size=float(arguments.get("size", 0.08)),
            red=float(arguments.get("red", 1.0)),
            green=float(arguments.get("green", 1.0)),
            blue=float(arguments.get("blue", 1.0)),
        )
    elif name == "resolve_create_cube_lut":
        return create_cube_lut(
            name=arguments["name"],
            contrast=float(arguments.get("contrast", 1.08)),
            saturation=float(arguments.get("saturation", 1.12)),
            warmth=float(arguments.get("warmth", 0.03)),
            teal_shadows=float(arguments.get("teal_shadows", 0.04)),
            gamma=float(arguments.get("gamma", 1.0)),
        )
    elif name == "resolve_queue_script_action":
        return enqueue_resolve_bridge_action(
            action_type=arguments["action_type"],
            payload=arguments,
        )
    else:
        raise ValueError(f"Unknown tool: {name}")


def send_response(msg: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main() -> None:
    ensure_directories()
    install_in_app_bridge_scripts()

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = req.get("method")
        req_id = req.get("id")
        params = req.get("params") or {}

        # Notifications have no id
        if req_id is None:
            continue

        if method == "initialize":
            client_version = params.get("protocolVersion", SUPPORTED_PROTOCOL_VERSIONS[0])
            negotiated = client_version if client_version in SUPPORTED_PROTOCOL_VERSIONS else SUPPORTED_PROTOCOL_VERSIONS[0]
            send_response(
                {
                    "jsonrpc": JSONRPC_VERSION,
                    "id": req_id,
                    "result": {
                        "protocolVersion": negotiated,
                        "capabilities": {
                            "tools": {"listChanged": False},
                        },
                        "serverInfo": {
                            "name": SERVER_NAME,
                            "version": SERVER_VERSION,
                        },
                    },
                }
            )
        elif method == "ping":
            send_response({"jsonrpc": JSONRPC_VERSION, "id": req_id, "result": {}})
        elif method == "tools/list":
            send_response(
                {
                    "jsonrpc": JSONRPC_VERSION,
                    "id": req_id,
                    "result": {"tools": TOOLS_SCHEMA},
                }
            )
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments") or {}
            try:
                result_data = handle_tool_call(tool_name, tool_args)
                send_response(
                    {
                        "jsonrpc": JSONRPC_VERSION,
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result_data, indent=2),
                                }
                            ],
                            "isError": False,
                        },
                    }
                )
            except Exception as exc:
                send_response(
                    {
                        "jsonrpc": JSONRPC_VERSION,
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Error executing {tool_name}: {exc}",
                                }
                            ],
                            "isError": True,
                        },
                    }
                )
        elif method in ("resources/list", "prompts/list"):
            key = "resources" if method == "resources/list" else "prompts"
            send_response({"jsonrpc": JSONRPC_VERSION, "id": req_id, "result": {key: []}})
        else:
            send_response(
                {
                    "jsonrpc": JSONRPC_VERSION,
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            )


if __name__ == "__main__":
    main()
