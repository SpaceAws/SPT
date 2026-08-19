# Space's Ptyhon Tools is an add-on created by Elouan Le Strat (Space) willing to centralize all tools 
# I created for different purposes using blender python concerning modeling, rigging and animation
# 
# This script registers all operators and panels created within Space's Ptyhon Tools
#

import bpy
import importlib

from . import SPT_functions
from . import SPT_properties
from . import SPT_animationOT
from . import SPT_modelingOT
from . import SPT_riggingOT
from . import SPT_systemOT
from . import SPT_panels

bl_info = {
    "name": "Space's Python Tools",
    "author": "Space",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),         # minimal Blender version
    "location": "View3D > N-Panel > SPT",
    "description": "Panel filled with tools I created using blender python",
    "category": "Object",
}

# ─────────────────────────────────────────────

#  REGISTERY
#  All classes are registered here
#  Properties first, then operators, then panels

# ─────────────────────────────────────────────
importlib.reload(SPT_functions)
importlib.reload(SPT_properties)
importlib.reload(SPT_animationOT)
importlib.reload(SPT_modelingOT)
importlib.reload(SPT_riggingOT)
importlib.reload(SPT_systemOT)
importlib.reload(SPT_panels)

CLASSES = [
    SPT_properties.SPT_PG_properties,
    SPT_properties.SPT_PG_preset_item,
    SPT_properties.SPT_PG_format_group,
    SPT_animationOT.SPT_OT_update_offset,
    SPT_animationOT.SPT_OT_add_remove,
    SPT_animationOT.SPT_OT_ik_fk_arm_l,
    SPT_animationOT.SPT_OT_ik_fk_arm_r,
    SPT_animationOT.SPT_OT_ik_fk_leg_l,
    SPT_animationOT.SPT_OT_ik_fk_leg_r,
    SPT_animationOT.SPT_OT_ik_fk_legs,
    SPT_animationOT.SPT_OT_ik_fk_arms,
    SPT_modelingOT.SPT_OT_select_touching_faces,
    SPT_modelingOT.SPT_OT_import_refs,
    SPT_modelingOT.SPT_OT_create_mirrored_obj,
    SPT_riggingOT.SPT_OT_base_bone_action,
    SPT_riggingOT.SPT_OT_create_custom_rig,
    SPT_riggingOT.SPT_OT_create_control_rig,
    SPT_riggingOT.SPT_OT_create_fk_control,
    SPT_riggingOT.SPT_OT_edit_widget,
    SPT_riggingOT.SPT_OT_create_widget,
    SPT_riggingOT.SPT_OT_delete_widget,
    SPT_riggingOT.SPT_OT_match_bone_transforms,
    SPT_riggingOT.SPT_OT_make_widget_unique,
    SPT_riggingOT.SPT_OT_remove_numeral,
    SPT_riggingOT.SPT_OT_change_prefix,
    SPT_riggingOT.SPT_OT_change_suffix,
    SPT_riggingOT.SPT_OT_select_children,
    SPT_riggingOT.SPT_OT_select_parents,
    SPT_riggingOT.SPT_OT_save_as_shape,
    SPT_systemOT.SPT_OT_clean_scene,
    SPT_systemOT.SPT_OT_fix_obj_name,
    SPT_systemOT.SPT_OT_show_info_popup,
    SPT_systemOT.SPT_OT_export_tool,
    SPT_systemOT.SPT_OT_uv_creation,
    SPT_systemOT.SPT_OT_apply_location,
    SPT_systemOT.SPT_OT_apply_scale,
    SPT_systemOT.SPT_OT_apply_rot,
    SPT_systemOT.SPT_OT_normals_orient,
    SPT_systemOT.SPT_OT_fix_name,
    SPT_systemOT.SPT_OT_apply_smooth,
    SPT_systemOT.SPT_OT_show_modifier,
    SPT_panels.SPT_OT_show_tooltip,
    SPT_panels.SPT_PT_main,
    SPT_panels.SPT_PT_general,
    SPT_panels.SPT_PT_animation,
    SPT_panels.SPT_PT_offset,
    SPT_panels.SPT_PT_ik_fk,
    SPT_panels.SPT_PT_modeling,
    SPT_panels.SPT_PT_setup,
    SPT_panels.SPT_PT_selector,
    SPT_panels.SPT_PT_rigging,
    SPT_panels.SPT_PT_parameters,
    SPT_panels.SPT_PT_renamer,
    SPT_panels.SPT_PT_creator,
    SPT_panels.SPT_PT_widgets,
    SPT_panels.SPT_PT_system,
    SPT_panels.SPT_PT_scene_validation,
]

def safe_register(cls):
    try:
        bpy.utils.register_class(cls)
    except ValueError:
        old_cls = getattr(bpy.types, cls.__name__, None)
        if old_cls is not None:
            try:
                bpy.utils.unregister_class(old_cls)
            except RuntimeError as e:
                print(f"[register] Cannot unregister {cls.__name__} : {e}")
        if cls.__name__ == "SPT_PG_properties":
            bpy.utils.unregister_class(cls)
            if hasattr(bpy.types.Scene, "spt") :
                del bpy.types.Scene.spt
        bpy.utils.register_class(cls)

def register():
    for cls in CLASSES:
        safe_register(cls)
        
    # Attach PropertyGroup to Scene to access it via context.scene.spt
    if not hasattr(bpy.types.Scene, "spt"):
        bpy.types.Scene.spt = bpy.props.PointerProperty(type=SPT_properties.SPT_PG_properties)

def unregister():
    if hasattr(bpy.types.Scene, "spt"):
        del bpy.types.Scene.spt

    for cls in reversed(CLASSES):   # reversed to avoid dependancies
        try :
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


# ─────────────────────────────────────────────
#  Registers when running from editor
# ─────────────────────────────────────────────
if __name__ == "__main__":
    unregister()
    register()