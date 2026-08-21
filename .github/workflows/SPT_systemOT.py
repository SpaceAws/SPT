# This script contains all the following system operators :
#   - General :
#       - Cleaning scene by purging orphan data
#       - Fixing selected object's name so it fits requirements
#       - Showing an info popup with custom info
#   - Export :
#       - Fixing all different detectable issues : UVs, location, scale, rotation, normals, naming, smoothness, hidden modifiers
#       - Opening export tool giving access to batch export in different file formats using created presets
#

import bpy
import os

from .SPT_properties import *
from .SPT_functions import * 

# TODO :
#   - Batch import : système qui récupère tous les fichiers blend d'un dossier et ajoute leur contenu à l'asset browser de Blender + possibilité d'import instantané (https://shaterstudio.gumroad.com/l/ohzllx)
#   - Export avec preset : 
#   - Scene validator : show hidden ou del hidden pour les modifiers, ajouter une vérif des materials si mesh (naming), naming des bones si armature, pas de smooth verif si hidden (control shapes)
#   - Render tool : auto-render de frame ranges, changements de paramètres entre deux...
#   - Comparator : Comparaison de 2 versions pour review les changements
#   - Name fixer : add curve type (C_) and text type (T_) and image type (IMG_)

# ─────────────────────────────────────────────

#  OPERATORS

# ─────────────────────────────────────────────
    
class SPT_OT_clean_scene(bpy.types.Operator):
    
    bl_idname = "spt.clean_scene"
    bl_label  = "Clean scene"
    bl_description = "Purges all unused data"
    bl_options = {"UNDO"}
        
    def execute(self, context):
        props = context.scene.spt
        active_obj = context.object

        bpy.data.orphans_purge()
    
        self.report({"INFO"}, "Scene cleaned")
        return {"FINISHED"}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_fix_selected_name(bpy.types.Operator):
    
    bl_idname = "spt.fix_selected_name"
    bl_label  = "Fix object name"
    bl_description = "Fixes current object's name"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return context.active_object and not check_name(context, obj.name, obj_type=obj.type)

    def execute(self, context):
        obj = context.active_object
        obj.name = fix_name(context, obj, obj_type=obj.type)
        
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_show_info_popup(bpy.types.Operator):
    bl_idname = "spt.show_info_popup"
    bl_label = "Info"

    title: bpy.props.StringProperty(default="Information")
    icon: bpy.props.StringProperty(default="INFO")
    footer: bpy.props.StringProperty(default="Note...")

    # A line for each message/icon, joined by "\n"
    messages: bpy.props.StringProperty(default="")
    icons: bpy.props.StringProperty(default="")
    operators: bpy.props.StringProperty(default="")

    def invoke(self, context, event):
        self.width = 630
        self.char = 6

        window = context.window
        center_x = (window.width//2)-(self.width//2)
        center_y = (window.height//2)+(self.width//2)
        window.cursor_warp(center_x, center_y)
        return context.window_manager.invoke_popup(self, width=self.width)

    def draw(self, context):
        layout = self.layout
        draw_wrapped_label(layout, context, self.title, icon=self.icon, width=self.width, char_size=self.char)
        layout.separator()

        message_lines = self.messages.split("\n") if self.messages else []
        icon_lines = self.icons.split("\n") if self.icons else []
        op_lines = self.operators.split("\n") if self.operators else []

        for i, message in enumerate(message_lines):
            line_icon = icon_lines[i] if i < len(icon_lines) else "NONE"
            row = layout.row()
            box = row.box()
            if line_icon == "X":
                box.alert = True
            draw_wrapped_label(box, context, message, icon=line_icon, width=self.width, char_size=self.char)
            if op_lines[i] != "" :
                box = row.box()
                box.operator(op_lines[i])
        
        layout.separator()
        draw_wrapped_label(layout, context, self.footer, width=self.width, char_size=self.char)

    def execute(self, context):
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_uv_creation(bpy.types.Operator):
    
    bl_idname = "spt.uv_creation"
    bl_label  = "Fix UVs"
    bl_description = "Fixes UVs by applying smart projection to UV-less objects"
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        for obj in context.scene.objects:
            if obj.type == "MESH" and obj.visible_get() and not obj.data.uv_layers:
                obj.select_set(True)
                context.view_layer.objects.active = obj

                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.smart_project()

                bpy.ops.object.mode_set(mode="OBJECT")
                obj.select_set(False)
        
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_apply_location(bpy.types.Operator):
    
    bl_idname = "spt.apply_location"
    bl_label  = "Fix locations"
    bl_description = "Fixes rotations by applying location to problematic objects"
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        for obj in context.scene.objects:
            if obj.type in ["MESH", "ARMATURE"] and not obj.location == Vector((0.0,0.0,0.0)):
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

                obj.select_set(False)
        
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_apply_scale(bpy.types.Operator):
    
    bl_idname = "spt.apply_scale"
    bl_label  = "Fix scales"
    bl_description = "Fixes rotations by applying scale to problematic objects"
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        for obj in context.scene.objects:
            if not obj.scale == Vector((1.0,1.0,1.0)):
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

                obj.select_set(False)
        
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_apply_rot(bpy.types.Operator):
    
    bl_idname = "spt.apply_rot"
    bl_label  = "Fix rotations"
    bl_description = "Fixes rotations by applying rotation to problematic objects"
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        for obj in context.scene.objects:
            rot = (obj.rotation_euler[0], obj.rotation_euler[1], obj.rotation_euler[2])
            if not rot == (0.0, 0.0, 0.0):
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

                obj.select_set(False)
        
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_normals_orient(bpy.types.Operator):
    
    bl_idname = "spt.normals_orient"
    bl_label  = "Fix normals"
    bl_description = "Fixes normals by recalculating them on problematic objects"
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        for obj in context.scene.objects:
            if obj.type == "MESH" and obj.visible_get() and not check_normals_outward(obj):
                mesh = obj.data
                obj.select_set(True)
                context.view_layer.objects.active = obj

                bpy.ops.object.mode_set(mode="EDIT")
                bm = bmesh.from_edit_mesh(mesh)
                bm.faces.ensure_lookup_table()

                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.normals_make_consistent(inside=False)

                bm = bmesh.from_edit_mesh(mesh)
                bm.faces.ensure_lookup_table()

                bpy.ops.object.mode_set(mode="OBJECT")
                obj.select_set(False)
        
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_fix_obj_name(bpy.types.Operator):
    
    bl_idname = "spt.fix_obj_name"
    bl_label  = "Fix object names"
    bl_description = "Fixes object names by correcting them to fit desired conventions"
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        for obj in context.scene.objects:
            if not check_name(context, obj.name):
                obj.name = fix_name(context, obj, obj_type=obj.type)
        
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_fix_mat_name(bpy.types.Operator):
    
    bl_idname = "spt.fix_mat_name"
    bl_label  = "Fix material names"
    bl_description = "Fixes material names by correcting them to fit desired conventions"
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        for mat in bpy.data.materials:
            if not check_name(context, mat.name, obj_type="material"):
                mat.name = fix_name(context, mat, obj_type="material")
        
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_apply_smooth(bpy.types.Operator):
    
    bl_idname = "spt.apply_smooth"
    bl_label  = "Fix smooth"
    bl_description = "Fixes smooth by applying auto-smooth to problematic objects"
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        for obj in context.scene.objects:
            if obj.type == "MESH":
                smoothed = False
                for mod in obj.modifiers:
                    if mod.type == 'NODES' and mod.node_group is not None:
                        if mod.node_group.name.startswith("Smooth by Angle"):
                            smoothed = True
                if not smoothed :
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
                    
                    bpy.ops.object.shade_auto_smooth()

                    obj.select_set(False)
        
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_show_modifier(bpy.types.Operator):
    
    bl_idname = "spt.show_modifier"
    bl_label  = "Fix modifiers"
    bl_description = "Fixes modifiers by showing hidden ones on problematic objects"
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        for obj in context.scene.objects:
            hidden = False
            for mod in obj.modifiers:
                if not mod.show_viewport:
                    mod.show_viewport = True
        
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_export_tool(bpy.types.Operator):
    
    bl_idname = "spt.export_tool"
    bl_label  = "Export tool"
    bl_description = "Allows you to export multiple files from your scene using presets and multiple formats"

    formats: bpy.props.CollectionProperty(type=SPT_PG_format_group)
    
    @classmethod
    def poll(cls, context):
        return context.scene.objects

    def invoke(self, context, event): # ─────────────────────────────────────────────
        enabled_fmt = []
        enabled_presets = []
        for fmt in self.formats:
            if fmt.enabled:
                enabled_fmt.append(fmt)
                for item in fmt.presets :
                    if item.selected : 
                        enabled_presets.append(item)
                
        self.formats.clear()
        
        for exporter in find_export_operators():
            fmt = self.formats.add()
            fmt.idname = exporter["idname"]
            fmt.label = exporter["label"]

            for preset in get_presets_for_operator(exporter["idname"]):
                item = fmt.presets.add()
                item.preset_name = preset["name"]
                item.preset_filepath = preset["filepath"]
                item.origin = preset["origin"]

        for fmt in enabled_fmt:
            fmt.enabled = True
        for item in enabled_presets:
            item.selected = True

        width = 630
        window = context.window
        center_x = (window.width//2)-(width//2)
        center_y = (window.height//2)+(width//2)
        window.cursor_warp(center_x, center_y)
        context.scene.spt.name_export = f"{bpy.path.basename(bpy.context.blend_data.filepath)[:-6]}"
        return context.window_manager.invoke_props_dialog(self, width=width)
        
    def draw(self, context): # ─────────────────────────────────────────────
        props = context.scene.spt
        layout = self.layout
        
        layout.prop(props, "name_export")

        for fmt in self.formats:
            box = layout.box()
            box.prop(fmt, "enabled", text=fmt.label)
            if fmt.enabled:
                i = 0
                for item in fmt.presets:
                    i += 1

                if i == 0:
                    box.label(text="No preset can be accessed for this export type, please create one using the base Blender export function")
                else:
                    row = box.row()
                    col_addon = row.column()
                    col_addon.label(text="Add-on delivered presets")
                    col_user = row.column()
                    col_user.label(text="User created presets")
                    for item in fmt.presets:
                        if item.origin == "addon" :
                            col_addon.prop(item, "selected", text=item.preset_name, toggle=True)
                        else:
                            col_user.prop(item, "selected", text=item.preset_name, toggle=True)
        
        layout.separator()

    def execute(self, context):
        props = context.scene.spt

        if not bpy.data.filepath:
            self.report({'ERROR'}, "File must be saved before export.")
            return {'CANCELLED'}

        output_dir = os.path.dirname(bpy.path.abspath(bpy.data.filepath))

        to_export = {}
        for fmt in self.formats:
            if not fmt.enabled:
                continue
            to_export[fmt] = []
            for item in fmt.presets:
                if item.selected:
                    to_export[fmt].append(item)
                    
        exported_count = 0
        for fmt, items in to_export.items() :
            for item in items :
                ext = fmt.idname.split(".")[-1]
                name = f"{props.name_export}_{item.preset_name}.{ext}" if len(to_export[fmt]) > 1 else f"{props.name_export}.{ext}"
                output_path = os.path.join(output_dir, name)
                export_with_preset(fmt.idname, item.preset_filepath, output_path)
                exported_count += 1

        self.report({'INFO'}, f"{exported_count} export(s) terminé(s).")
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_add_coll_to_unverification(bpy.types.Operator):
    
    bl_idname = "spt.add_coll_to_unverification"
    bl_label  = "Add collection to unverification"
    bl_options = {"UNDO"}

    def execute(self, context):
        props = context.scene.spt
        global unverified_colls

        coll = bpy.data.collections.get(props.unverified_collection)
        unverified_colls.append(coll)
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_remove_coll_from_unverification(bpy.types.Operator):
    
    bl_idname = "spt.remove_coll_from_unverification"
    bl_label  = "Remove collection from unverification"
    bl_options = {"UNDO"}

    coll_name: bpy.props.StringProperty()

    def execute(self, context):
        global unverified_colls

        coll = bpy.data.collections.get(self.coll_name)
        if coll in get_valid_unverified_colls():
            unverified_colls.remove(coll)
        else:
            self.report({'WARNING'}, f"'{self.coll_name}' not found.")
        return {'FINISHED'}

