# This script contains all the following operators and panels :
#   - General Operators :
#       - Unregistering add-on to clear n-panel until next blender launch
#       - Showing tooltip if you need to access its informations again
#   - General Panel :
#       - Giving access to general operators and some information boxes about the active object
#   - Specific Panels :
#       - Giving access to specific tools developped in dedicated scripts
#

import bpy

from .SPT_functions import *
from .SPT_animationOT import *
from .SPT_modelingOT import *
from .SPT_riggingOT import *
from .SPT_systemOT import *

# ─────────────────────────────────────────────

#  OPERATORS

# ─────────────────────────────────────────────
         
class SPT_OT_show_tooltip(bpy.types.Operator):
    """
    Shows hidden tooltip
    """
    bl_idname = "spt.show_tooltip"
    bl_label  = "Show Tooltip"
    bl_description = "Shows SPT main panel's info tooltip if you OKed it by mistake"
    bl_options = {"REGISTER", "UNDO"}        # UNDO → intégré dans l'historique Ctrl+Z
    
    @classmethod
    def poll(cls, context):
        return (context.scene.spt.hide_info)
    
    def execute(self, context):
        props = context.scene.spt
        
        props.hide_info = False
        return {'FINISHED'}

# ─────────────────────────────────────────────

#  PANELS

# ─────────────────────────────────────────────

class SPT_PT_main(bpy.types.Panel):
    
    bl_label       = "SpacePythonTool"
    bl_idname      = "SPT_PT_main"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"

    def draw(self, context):
        layout = self.layout
        props  = context.scene.spt
        
        if not props.hide_info :
            box = layout.box()
            box.label(icon="INFO", text="Tooltip :")
            draw_wrapped_label(box, context, "─ You can add any button from this panel to your quick favorites to access it faster.")
            draw_wrapped_label(box, context, "─ Make sure to define parameters if you work with an existing rig.")
            draw_wrapped_label(box, context, "─ If you encounter any trouble, feel free to contact me on discord : spaceaws.")
            box.prop(props, "hide_info")
        
# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_PT_general(bpy.types.Panel):
    
    bl_label       = "GENERAL"
    bl_idname      = "SPT_PT_general"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_main"
    bl_options     = {"DEFAULT_CLOSED"} 
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        props  = context.scene.spt

        # ── Separator ──
        layout.separator()
        # ── Button ──
        layout.operator("spt.show_tooltip")
        # ── Separator ──
        layout.separator()
        
        # Verifying obj
        if obj :
            
            obj_icon = "OUTLINER_OB_ARMATURE" if obj.type == "ARMATURE" else "OUTLINER_OB_CURVE" if obj.type == "CURVE" else "OUTLINER_OB_EMPTY" if obj.type == "EMPTY" else "OUTLINER_OB_MESH"
            
            # ── Object infos ──
            box = layout.box()
            row = box.row(align=True)
            row.label(text=f"Name     : {obj.name}")
            row.label(text="", icon=obj_icon)
            box.label(text=f"Type      : {obj.type}")
            
            if obj.type == "ARMATURE":
                box.label(text=f"Bones    : {len(obj.data.bones)}")
                # ── Active bone infos ──
                active_bone = context.active_bone or context.active_pose_bone
                if context.active_bone and context.object.mode == 'EDIT':
                    box3 = layout.box()
                    box3.label(text=f"Active bone  : {active_bone.name}", icon="BONE_DATA")
                    box3.label(text=f"Parent : {active_bone.parent.name}" if active_bone.parent else "Parent : None")
                    box3.label(text=f"Roll : {math.degrees(active_bone.roll):.1f}°")
                    box3.label(text=f"Length   : {active_bone.length:.3f}")
                    box3.label(text=f"Connected: {active_bone.use_connect}")
                elif context.active_pose_bone and context.object.mode == 'POSE':
                    box3 = layout.box()
                    box3.label(text=f"Active bone  : {active_bone.name}", icon="BONE_DATA")
                    box3.label(text=f"Parent : {active_bone.parent.name}" if active_bone.parent else "Parent : None")
                    
                # ── Separator ──
                layout.separator()
                
                # ── Bool to hide/show ──
                icon = "RIGHTARROW" if not props.show_general_details else "DOWNARROW_HLT"
                layout.prop(props, "show_general_details", toggle=True, icon=icon)
                
                if props.show_general_details:
                    # ── Bones list ──
                    col = layout.column(align=True)
                    for bone in obj.data.bones:
                        prefix = bone.name[:4]
                        row = col.row()
                        row.label(text=bone.name, icon="BONE_DATA" if prefix == props.skin_prfx else "PARTICLES" if prefix == props.control_prfx else "MEMORY" if prefix == props.mecha_prfx else "PANEL_CLOSE")
                        # Visual indent depending on hierarchical depth
                        depth = 0
                        p = bone.parent
                        while p:
                            depth += 1
                            p = p.parent
                        row.label(text="  " * depth + ("└" if bone.parent else ""))
            
        else :
            layout.label(text="No active object", icon="INFO")
                
# ─────────────────────────────────────────────
#  ANIMATION
# ─────────────────────────────────────────────

class SPT_PT_animation(bpy.types.Panel):
    
    bl_label       = "ANIMATION"
    bl_idname      = "SPT_PT_animation"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_main"  
    bl_options     = {"DEFAULT_CLOSED"} 
    
    def draw(self, context):
        layout = self.layout
        
# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_PT_ik_fk(bpy.types.Panel):
    
    bl_label       = "── IK / FK ────────────"
    bl_idname      = "SPT_PT_ik_fk"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_animation"
    bl_options     = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        active_obj = context.active_object
        
        if active_obj and "ik_fk_arms" in active_obj :
            text = "Arms : IK" if active_obj["ik_fk_arms"] == 1 else "Arms : FK"
            layout.operator("spt.ik_fk_arms", text=text)
        else :
            row=layout.row(align=True)
            text = "── Arm L ──" if not active_obj or active_obj.type != "ARMATURE" or "ik_fk_arm_l" not in active_obj else "Arm L : IK" if active_obj["ik_fk_arm_l"] == 1 else "Arm L : FK"
            row.operator("spt.ik_fk_arm_l", text=text)
            text = "── Arm R ──" if not active_obj or active_obj.type != "ARMATURE" or "ik_fk_arm_r" not in active_obj else "Arm R : IK" if active_obj["ik_fk_arm_r"] == 1 else "Arm R : FK"
            row.operator("spt.ik_fk_arm_r", text=text)
        
        if active_obj and "ik_fk_legs" in active_obj :
            text = "Legs : IK" if active_obj["ik_fk_legs"] == 1 else "Legs : FK"
            layout.operator("spt.ik_fk_legs", text=text)
        else :
            row=layout.row(align=True)
            text = "── Leg L ──" if not active_obj or active_obj.type != "ARMATURE" or "ik_fk_leg_l" not in active_obj else "Leg L : IK" if active_obj["ik_fk_leg_l"] == 1 else "Leg L : FK"
            row.operator("spt.ik_fk_leg_l", text=text)
            text = "── Leg R ──" if not active_obj or active_obj.type != "ARMATURE" or "ik_fk_leg_r" not in active_obj else "Leg R : IK" if active_obj["ik_fk_leg_r"] == 1 else "Leg R : FK"
            row.operator("spt.ik_fk_leg_r", text=text)
        
# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_PT_offset(bpy.types.Panel):
    
    bl_label       = "Offset ──────────────"
    bl_idname      = "SPT_PT_offset"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_animation"
    bl_options     = {"DEFAULT_CLOSED"} 
    
    def draw(self, context):
        layout = self.layout
        props  = context.scene.spt
        
        # ── Displays active object ──
        obj = context.active_object
        if obj:
            row = layout.row()
            row.label(text="Active :", icon="OBJECT_DATA")
            row.label(text=obj.name)
        else:
            layout.label(text="Aucun objet actif", icon="INFO")
            
        # ── Separator ──
        layout.separator()
        
        # ── Entry ──
        layout.label(text="Target Bone :")
        layout.prop(props,"target_bone", text="")
        
        # ── Separator ──
        layout.separator()
        
        # ── Slider vector ──
        layout.prop(props, "offset_location")
        # ── Slider vector ──
        layout.prop(props, "offset_rotation")
        # ── Slider vector ──
        layout.prop(props, "offset_scale")
        
        # ── Separator ──
        layout.separator()
        
        # ── Button ──
        if props.add_remove >= 0 :
            layout.operator("spt.add_remove", text="Switch to remove")
        else :
            layout.operator("spt.add_remove", text="Switch to add")
        
        # ── Separator ──
        layout.separator()
        
        # ── Button ──
        layout.operator("spt.update_offset")
        
# ─────────────────────────────────────────────
#  MODELING
# ─────────────────────────────────────────────

class SPT_PT_modeling(bpy.types.Panel):
    
    bl_label       = "MODELING"
    bl_idname      = "SPT_PT_modeling"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_main"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

# ──────────────────────────────────────────────────────────────────────────────────────────        
class SPT_PT_setup(bpy.types.Panel):
    
    bl_label       = "Setup ──────────────"
    bl_idname      = "SPT_PT_setup"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_modeling"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout       
        props  = context.scene.spt

        # Float
        layout.prop(props, "ref_distance", icon="FIXED_SIZE")
        # Button
        layout.operator("spt.import_refs", icon="IMAGE_PLANE")

        layout.separator()

        # String entry        
        box = layout.box()
        box.label(text="Name : ", icon="SMALL_CAPS")
        row = box.row(align=True)
        row.label(text="GEO_")
        row.prop(props, "plane_name", text="")
        # Button
        layout.operator("spt.create_mirrored_obj", icon="MOD_MIRROR")

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_PT_selector(bpy.types.Panel):
    
    bl_label       = "── Selector ────────────"
    bl_idname      = "SPT_PT_selector"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_modeling"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props  = context.scene.spt
                
        # Bools for options
        row = layout.row(align=True)
        icon = "MESH_PLANE" if not props.loop_selection else "VIEW_ORTHO"

        row.prop(props, "loop_selection", toggle=True, icon=icon)
        row.prop(props, "loop_selection", text="")
        row = layout.row(align=True)
        icon = "LAYER_ACTIVE" if not props.select_diagonal else "PIVOT_CURSOR"
        row.prop(props, "select_diagonal", toggle=True, icon=icon)
        row.prop(props, "select_diagonal", text="")
        row = layout.row(align=True)
        icon = "RESTRICT_INSTANCED_OFF" if props.select_connected else "RESTRICT_INSTANCED_ON"
        row.prop(props, "select_connected", toggle=True, icon=icon)
        row.prop(props, "select_connected", text="")
        
        # Button
        layout.operator("spt.select_touching_faces", icon="PIVOT_BOUNDBOX")
        
# ─────────────────────────────────────────────
#  RIGGING
# ─────────────────────────────────────────────

class SPT_PT_rigging(bpy.types.Panel):
    
    bl_label       = "RIGGING"
    bl_idname      = "SPT_PT_rigging"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_main"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        
        row = layout.row(align=True)
        row.operator("spt.select_children")
        row.operator("spt.select_parents")

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_PT_parameters(bpy.types.Panel):
    
    bl_label       = "Parameters ──────────────"
    bl_idname      = "SPT_PT_parameters"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_rigging"
    bl_options     = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        props  = context.scene.spt
        
        # ── Separator ──
        layout.separator()
        
        # ── Label ──
        row=layout.row()
        row.alignment = "CENTER"
        row.label(text="Bones Prefixes")
        # ── Prefixes entries ──
        row = layout.row()
        row.prop(props, "skin_prfx", text="")
        row.prop(props, "control_prfx", text="")
        row.prop(props, "mecha_prfx", text="")
        
        # ── Label ──
        row=layout.row()
        row.alignment = "CENTER"
        row.label(text="Controller Colors")
        # ── Colors ──
        row = layout.row()
        row.prop(props, "bone_color_l", text="")
        row.prop(props, "bone_color", text="")
        row.prop(props, "bone_color_r", text="")
        
        # ── Separator ──
        layout.separator()

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_PT_renamer(bpy.types.Panel):
    
    bl_label       = "── Renamer ────────────"
    bl_idname      = "SPT_PT_renamer"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_rigging"
    bl_options     = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        props  = context.scene.spt
        
        # ── Separator ──
        layout.separator()
        
        # ── Label ──
        if context.object and context.object.type == "ARMATURE" and context.object.mode in ['POSE', 'EDIT']:
            active_bone = context.active_pose_bone if context.object.mode == "POSE" else context.active_bone
            if active_bone :
                curr_name = active_bone.name
                prfx, base, count_sfx, side_sfx = parse_string(curr_name)
                box = layout.box()
                row = box.row()
                row.alignment = "CENTER"
                struct = f"{prfx}|BASE|_{count_sfx}{side_sfx}" if count_sfx != "" else f"{prfx}|BASE|{side_sfx}"
                row.label(text=f"Current Structure : {struct}")
            else :
                box = layout.box()
                box.label(text="")
        
        # ── Bool ──
        layout.prop(props, "apply_to_children")    
        
        # ── Separator ──
        layout.separator()
        
        # ── Button ──
        layout.operator("spt.fix_bone_name", icon="LINENUMBERS_ON")        
        
        # ── Labels ──
        row = layout.row(align=True)
        row.label(text=props.skin_prfx, icon="RIGHTARROW")
        row.label(text=props.control_prfx, icon="RIGHTARROW")
        row.label(text=props.mecha_prfx, icon="RIGHTARROW")
        row.label(text="...", icon="RIGHTARROW")
        # ── Button ──
        layout.operator("spt.change_prefix", icon="TRACKING_FORWARDS_SINGLE")
        
        # ── Labels ──
        row = layout.row(align=True)
        row.label(text=".r", icon="RIGHTARROW")
        row.label(text=".l", icon="RIGHTARROW")
        row.label(text="...", icon="RIGHTARROW")
        row.label(text="")
        layout.operator("spt.change_suffix", icon="TRACKING_BACKWARDS_SINGLE")
        
        # ── Separator ──
        layout.separator()
        
# ──────────────────────────────────────────────────────────────────────────────────────────  
class SPT_PT_creator(bpy.types.Panel):
    
    bl_label       = "──── Creator ───────────"
    bl_idname      = "SPT_PT_creator"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_rigging"
    bl_options     = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        props  = context.scene.spt
        
        # ── Separator ──
        layout.separator()
        
        # ── RIG ──
        icon = "RIGHTARROW" if not props.show_rig_crea else "DOWNARROW_HLT"
        box=layout.box()
        box.prop(props, "show_rig_crea", icon=icon, text="──── RIG CREATION ────")
        
        if props.show_rig_crea :
            # ── Menu ──
            layout.prop(props, "rig_preset")
            
            # ── Bool to hide/show ──
            icon = "RIGHTARROW" if not props.show_rig_details else "DOWNARROW_HLT"
            layout.prop(props, "show_rig_details", toggle=True, icon=icon)
            
            # ── Separator ──
            layout.separator()
            
            # ── Sliders ──
            if props.show_rig_details :
                row = layout.row(align=True)
                row.label(text="", icon="MOD_CLOTH")
                row.prop(props,"count_body")
                col = row.row(align=True)
                col.enabled = props.count_body > 0
                col.prop(props,"length_body")
                
                row = layout.row(align=True)
                row.enabled = props.count_body > 0
                row.label(text="", icon="MOD_CURVE")
                row.prop(props,"count_tails")
                col = row.row(align=True)
                col.enabled = props.count_tails > 0 and props.count_body > 0
                col.prop(props,"length_tails")
                
                row = layout.row(align=True)
                row.enabled = props.count_body > 0
                row.label(text="", icon="MONKEY")
                row.prop(props,"count_head")
                col = row.row(align=True)
                col.enabled = props.count_head > 0 and props.count_body > 0
                col.prop(props,"length_head")
                
                row = layout.row(align=True)
                row.enabled = props.count_head > 0 and props.count_body > 0
                row.label(text="", icon="CURVES")
                row.prop(props,"count_hairs")
                col = row.row(align=True)
                col.enabled = props.count_hairs > 0 and props.count_head > 0 and props.count_body > 0
                col.prop(props,"length_hairs")
                
                row = layout.row(align=True)
                row.enabled = props.count_body > 0
                row.label(text="", icon="HANDLE_VECTOR")
                row.prop(props,"count_legs")
                col = row.row(align=True)
                col.enabled = props.count_legs > 0 and props.count_body > 0
                col.prop(props,"length_legs")
                
                row = layout.row(align=True)
                row.enabled = props.count_legs > 0 and props.count_body > 0
                row.label(text="", icon="MOD_DYNAMICPAINT")
                row.prop(props,"count_foot")
                col = row.row(align=True)
                col.enabled = props.count_foot > 0 and props.count_legs > 0 and props.count_body > 0
                col.prop(props,"length_foot")
                
                row = layout.row(align=True)
                row.enabled = props.count_body > 0
                row.label(text="", icon="CON_STRETCHTO")
                row.prop(props,"count_arms")
                col = row.row(align=True)
                col.enabled = props.count_arms > 0 and props.count_body > 0
                col.prop(props,"length_arms")
                
                row = layout.row(align=True)
                row.enabled = props.count_arms > 0 and props.count_body > 0
                row.label(text="", icon="VIEW_PAN")
                row.prop(props,"count_fingers")
                col = row.row(align=True)
                col.enabled = props.count_fingers > 0 and props.count_arms > 0 and props.count_body > 0
                col.prop(props,"length_fingers")
                
                # ── Separator ──
                layout.separator()
            
            # ── String Entry and bool ──
            layout.prop(props, "bone_connected")
            layout.prop(props, "new_rig_name")
            
            # ── Button ──
            layout.operator("spt.create_custom_rig", icon="OBJECT_DATA")
            
            # ── Separator ──
            layout.separator()
                
        
        # ── CONTROLLERS ──
        icon = "RIGHTARROW" if not props.show_ctl_crea else "DOWNARROW_HLT"
        box=layout.box()
        box.prop(props, "show_ctl_crea", icon=icon, text="──── CONTROL CREATION ────")
        
        if props.show_ctl_crea :
            # ── Bools IK FK ──
            icon0 = "RADIOBUT_ON" if props.leg_ik else "RADIOBUT_OFF"
            icon1 = "RADIOBUT_ON" if props.leg_fk else "RADIOBUT_OFF"
            row=layout.row(align=True)
            row.prop(props, "leg_ik", toggle=True, icon=icon0)
            row.prop(props, "leg_fk", toggle=True, icon=icon1)
            icon0 = "RADIOBUT_ON" if props.arm_ik else "RADIOBUT_OFF"
            icon1 = "RADIOBUT_ON" if props.arm_fk else "RADIOBUT_OFF"
            row=layout.row(align=True)
            row.prop(props, "arm_ik", toggle=True, icon=icon0)
            row.prop(props, "arm_fk", toggle=True, icon=icon1)
            # ── Button ──
            layout.operator("spt.create_control_rig", icon="PARTICLES")
            # ── Button ──
            layout.operator("spt.create_fk_control", icon="TRACKING_REFINE_FORWARDS")
            
        # ── Separator ──
        layout.separator()
               
# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_PT_widgets(bpy.types.Panel):
    
    bl_label       = "────── Widgets ────────"
    bl_idname      = "SPT_PT_widgets"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_rigging"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props  = context.scene.spt
        
        # ── Separator ──
        layout.separator()
        
        # ── Menu  ──
        layout.prop(props,"widget_shape")
        
        # ── Buttons ──
        row = layout.row(align=True)
        row.operator("spt.create_widget", icon="OBJECT_DATA")
        if props.edit_widget_active :
            row.operator("spt.edit_widget", text="Back to bone", icon="LOOP_BACK")
        else : 
            row.operator("spt.edit_widget", text="Edit", icon="OUTLINER_DATA_MESH")
        
        # ── Button ──    
        layout.operator("spt.match_bone_transforms", icon="GROUP_BONE")
        
        # ── Buttons ──    
        row = layout.row(align=True)
        row.operator("spt.delete_widget", icon="TRASH")
        row.operator("spt.make_widget_unique", icon="UNLINKED")
        
        # ── Separator ──
        layout.separator()

        # ── Button ──
        layout.operator("spt.save_as_shape", icon="FILE_TICK")

        # ── Separator ──
        layout.separator()

# ─────────────────────────────────────────────
#  SYSTEM
# ─────────────────────────────────────────────

class SPT_PT_system(bpy.types.Panel):
    
    bl_label       = "SYSTEM"
    bl_idname      = "SPT_PT_system"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_main"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props  = context.scene.spt
        
        row = layout.row(align=True)
        row.operator("spt.clean_scene", icon="TRASH") 
        row.operator("spt.fix_selected_name", icon="SORTALPHA")       

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_PT_scene_validation(bpy.types.Panel):
    
    bl_label       = "Export ───────────────"
    bl_idname      = "SPT_PT_scene_validation"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "SPT"
    bl_parent_id   = "SPT_PT_system"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props  = context.scene.spt

        # Gets issues
        auto_validation = False
        validation_check, messages, operators, objects = get_issues(context)

        # Selector for collections to avoid
        layout.label(text="Add/Remove non-checked collections :")
        row = layout.row(align=True)
        row.prop(props, "unverified_collection", text="")
        row.operator("spt.add_coll_to_unverification", icon="CHECKMARK", text="")
        for coll in get_valid_unverified_colls() :
            row = layout.row(align=True)
            row.label(text=coll.name, icon="OUTLINER_COLLECTION")
            op = row.operator("spt.remove_coll_from_unverification",text="",icon='X',)
            op.coll_name = coll.name

        layout.separator()

        # Adds a warning message or each issue
        if 0 in validation_check :
            for i, v in enumerate(validation_check) :
                if v == 0 :
                    self.add_warning(context, messages[i], operators[i], objects[i])
        else:
            # Enables auto validation if no issues
            auto_validation = True
            box = layout.box()
            box.label(text="Scene clear", icon="CHECKMARK")

        layout.separator()

        # Manual validation bool and export tool operator
        layout.prop(props, "scene_validated")
        row = layout.row()
        row.enabled = auto_validation if not props.scene_validated else True
        row.operator("spt.export_tool", icon="EXPORT")

    def add_warning(self,context,message,operator,obj):
        layout = self.layout

        # Label
        row = layout.row()
        box = row.box()
        box.alert = True
        draw_wrapped_label(box, context, message, icon="X")

        # Operator
        box = row.box()
        box.operator(operator)

        # Objects concerned
        layout.label(text=f"{obj}", icon="OBJECT_DATA")

