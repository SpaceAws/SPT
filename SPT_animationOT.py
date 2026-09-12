# This script contains all the following animation operators :
#   - Offset :
#       - Adding or removing transform offsets to a selected bone
#   - IK / FK :
#       - Inverting ik / fk custom properties from selected armature to easily switch control types
#

import bpy
import bmesh
from mathutils import Vector, Matrix
import math

from .SPT_functions import * 

# ─────────────────────────────────────────────

#  OPERATORS

# ─────────────────────────────────────────────
    
class SPT_OT_update_offset(bpy.types.Operator):
    
    bl_idname = "spt.update_offset"
    bl_label  = "Update offset"
    bl_description = "Adds or remove given offset to every keyframes for the selected bone"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        props = context.scene.spt        
        obj = context.active_object
        bone = obj.pose.bones.get(context.scene.spt.target_bone)
        
        # ──── Verifying selection ────
        if not bone:
            self.report({"ERROR"}, "No bone selected")
            return {"CANCELLED"}
        # Gets action from object's animation data
        action = obj.animation_data.action
        if not action:
            return {"CANCELLED"}
        
        offsets = {
            "location":       props.offset_location,
            "rotation_euler": props.offset_rotation,
            "scale":          props.offset_scale,
        }        

        # ──── Applying offset ────
        data_path_base = f'pose.bones["{bone.name}"]'

        for fcurve in get_fcurves(action):
            # Filtering this bone's FCurves only
            if not fcurve.data_path.startswith(data_path_base):
                continue
            
            # Identifying channel : location, rotation_euler, scale...
            channel = fcurve.data_path.replace(data_path_base + ".", "")
            
            # Ignoring channels that are not in dictionnary
            if channel not in offsets:
                continue

            # Getting offset value via array_index
            offset_value = offsets[channel][fcurve.array_index]

            for keyframe in fcurve.keyframe_points:
                keyframe.co[1] += offset_value*props.add_remove

            fcurve.update()
        
        self.report({"INFO"}, "Offset successfully updated")
        return {"FINISHED"}
    
# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_add_remove(bpy.types.Operator):
    
    bl_idname = "spt.add_remove"
    bl_label  = "Add or Remove"
    bl_description = "Chooses if you will add or remove the selected offset"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        props = context.scene.spt
        
        if props.add_remove >= 0 :
            props.add_remove = -1
            self.report({"INFO"}, "Offset will now be removed when updating")
        else:
            props.add_remove = 1
            self.report({"INFO"}, "Offset will now be added when updating")
        
        return {"FINISHED"}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_ik_fk_arm_l(bpy.types.Operator):
    
    bl_idname = "spt.ik_fk_arm_l"
    bl_label  = "Arm l"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        if context.object : 
            active_obj  = context.active_object
        
        return (context.object and context.object.type == 'ARMATURE' and "ik_fk_arm_l" in active_obj)
        
    def execute(self, context):
        active_obj  = context.active_object
        
        active_obj["ik_fk_arm_l"] = 1 if active_obj["ik_fk_arm_l"] == 0 else 0 # inverts property value
        
        mode = context.object.mode
        bpy.ops.object.mode_set(mode="EDIT") # actualizes value
        bpy.ops.object.mode_set(mode=mode)
        
        return {"FINISHED"}

# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_ik_fk_arm_r(bpy.types.Operator):
    
    bl_idname = "spt.ik_fk_arm_r"
    bl_label  = "Arm r"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        if context.object : 
            active_obj  = context.active_object
        
        return (context.object and context.object.type == 'ARMATURE' and "ik_fk_arm_r" in active_obj)
        
    def execute(self, context):
        active_obj  = context.active_object
        
        active_obj["ik_fk_arm_r"] = 1 if active_obj["ik_fk_arm_r"] == 0 else 0 # inverts property value
        
        mode = context.object.mode
        bpy.ops.object.mode_set(mode="EDIT") # actualizes value
        bpy.ops.object.mode_set(mode=mode)
        
        return {"FINISHED"}
   
# ────────────────────────────────────────────────────────────────────────────────────────── 
class SPT_OT_ik_fk_leg_l(bpy.types.Operator):
    
    bl_idname = "spt.ik_fk_leg_l"
    bl_label  = "Leg l"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        if context.object : 
            active_obj  = context.active_object
        
        return (context.object and context.object.type == 'ARMATURE' and "ik_fk_leg_l" in active_obj)
        
    def execute(self, context):
        active_obj  = context.active_object
        
        active_obj["ik_fk_leg_l"] = 1 if active_obj["ik_fk_leg_l"] == 0 else 0 # inverts property value
        
        mode = context.object.mode
        bpy.ops.object.mode_set(mode="EDIT") # actualizes value
        bpy.ops.object.mode_set(mode=mode)
        
        return {"FINISHED"}

# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_ik_fk_leg_r(bpy.types.Operator):
    
    bl_idname = "spt.ik_fk_leg_r"
    bl_label  = "Leg r"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        if context.object : 
            active_obj  = context.active_object
        
        return (context.object and context.object.type == 'ARMATURE' and "ik_fk_leg_r" in active_obj)
        
    def execute(self, context):
        active_obj  = context.active_object
        
        active_obj["ik_fk_leg_r"] = 1 if active_obj["ik_fk_leg_r"] == 0 else 0 # inverts property value
        
        mode = context.object.mode
        bpy.ops.object.mode_set(mode="EDIT") # actualizes value
        bpy.ops.object.mode_set(mode=mode)
        
        return {"FINISHED"}

# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_ik_fk_legs(bpy.types.Operator):
    
    bl_idname = "spt.ik_fk_legs"
    bl_label  = "Legs"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        if context.object : 
            active_obj  = context.active_object
        
        return (context.object and context.object.type == 'ARMATURE' and "ik_fk_legs" in active_obj)
        
    def execute(self, context):
        active_obj  = context.active_object
        
        active_obj["ik_fk_legs"] = 1 if active_obj["ik_fk_legs"] == 0 else 0 # inverts property value
        
        mode = context.object.mode
        bpy.ops.object.mode_set(mode="EDIT") # actualizes value
        bpy.ops.object.mode_set(mode=mode)
        
        return {"FINISHED"}

# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_ik_fk_arms(bpy.types.Operator):
    
    bl_idname = "spt.ik_fk_arms"
    bl_label  = "Arms"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        if context.object : 
            active_obj  = context.active_object
        
        return (context.object and context.object.type == 'ARMATURE' and "ik_fk_arms" in active_obj)
        
    def execute(self, context):
        active_obj  = context.active_object
        
        active_obj["ik_fk_arms"] = 1 if active_obj["ik_fk_arms"] == 0 else 0 # inverts property value
        
        mode = context.object.mode
        bpy.ops.object.mode_set(mode="EDIT") # actualizes value
        bpy.ops.object.mode_set(mode=mode)
        
        return {"FINISHED"}    
