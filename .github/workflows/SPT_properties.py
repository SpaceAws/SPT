# This script contains all the properties used for SPT :
#   - General properties
#   - Preset item and format group used for export tool to access saved presets
#

import bpy
    
from .SPT_functions import * 

# ─────────────────────────────────────────────

#  PROPERTIES

# ─────────────────────────────────────────────

class SPT_PG_properties(bpy.types.PropertyGroup):
    """
    Stocks every properties used by the panels
    """  
    # ─────────────────────────────────────────────
    # GENERAL
    # ─────────────────────────────────────────────  
    hide_info: bpy.props.BoolProperty(name="OK",description="",default=False)
    show_general_details: bpy.props.BoolProperty(name="Show details",description="",default=True)
    
    # ─────────────────────────────────────────────
    # ANIMATION
    # ─────────────────────────────────────────────  
    # 3D Vectors
    offset_location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Bone's location offset",
        default=(0.0, 0.0, 0.0),
        subtype="XYZ",  # other options : "COLOR", "EULER", "VELOCITY"...
    )
    offset_rotation: bpy.props.FloatVectorProperty(
        name="Rotation",
        description="Bone's rotation offset",
        default=(0.0, 0.0, 0.0),
        subtype="EULER",
    )
    offset_scale: bpy.props.FloatVectorProperty(
        name="Scale",
        description="Bone's scale offset",
        default=(0.0, 0.0, 0.0),
        subtype="XYZ",
    )
    
    # Entry for a scene object
    target_bone: bpy.props.StringProperty(
        name="Target Bone",
        description="Choose a bone to target with this panel's actions",
        search=bone_search
    )
    
    # Float
    add_remove: bpy.props.FloatProperty(
        name="Add or Remove",
        description="Whether you add or remove offset",
        default=1.0,
        min=-1.0,
        max=1.0,
        step=100,
        precision=3,
    )
    
    # ─────────────────────────────────────────────
    # MODELING
    # ───────────────────────────────────────────── 
    # Bools
    loop_selection: bpy.props.BoolProperty(name="Propagate selection",description="",default=False)
    select_diagonal: bpy.props.BoolProperty(name="Select diagonally",description="",default=False)
    select_connected: bpy.props.BoolProperty(name="Select connected",description="",default=False)

    # Float
    ref_distance: bpy.props.FloatProperty(
        name="Distance",
        description="Distance at which references are placed",
        default=20.0,
        min=0.0,
        max=10000.0,
        step=10,
        precision=1,
    )

    # String
    plane_name: bpy.props.StringProperty(
        name="Name",
        description="Name given to created object",
        default="Plane",
        maxlen=64,
    )
    
    # ─────────────────────────────────────────────
    # RIGGING
    # ─────────────────────────────────────────────
    #Entries for prefixes
    skin_prfx: bpy.props.StringProperty(
        name="Skinned",
        description="Prefix given to created rigs and used for skinned bones recognition",
        default="BNS_",
        maxlen=64) 
    control_prfx: bpy.props.StringProperty(
        name="Control",
        description="Prefix given to created rigs and used for control bones recognition",
        default="CTL_",
        maxlen=64) 
    mecha_prfx: bpy.props.StringProperty(
        name="Mecha",
        description="Prefix given to created rigs and used for mecha bones recognition",
        default="MCH_",
        maxlen=64)
    
    # RGBA colors for controllers
    bone_color_l: bpy.props.FloatVectorProperty(name="Left",description="",default=(0.0, 0.0, 0.8),size=3,min=0.0,max=1.0,subtype="COLOR")
    bone_color: bpy.props.FloatVectorProperty(name="Center",description="",default=(1.0, 0.8, 0.0),size=3,min=0.0,max=1.0,subtype="COLOR")
    bone_color_r: bpy.props.FloatVectorProperty(name="Right",description="",default=(0.8, 0.0, 0.0),size=3,min=0.0,max=1.0,subtype="COLOR")
    
    #Entry for rig creation
    new_rig_name: bpy.props.StringProperty(
        name="Name",
        description="Name given to created rig",
        default="RIG_Object",
        maxlen=64,
    )
    
    #Enum
    rig_preset: bpy.props.EnumProperty(
        name="Preset",
        description="Choose a preset to use for custom rig creation",
        items=[
            # (internal_id, lable, description, icon, index)
            ("CUSTOM",     "Custom",   "", "MODIFIER",      0),
            ("BASIC",      "Basic",    "", "EMPTY_DATA",    1),
            ("HUMANOID",   "Humanoid", "", "POSE_HLT",      2),
            ("ARACHNID",   "Arachnid", "", "LIGHT_SUN",     3),
        ],
        default="CUSTOM",
        update=update_rig_preset, #calls function on every change
    )
    
    # Integers
    count_body: bpy.props.IntProperty(name="Body",description="",default=1,min=0,max=1)
    count_tails: bpy.props.IntProperty(name="Tails",description="",default=1,min=0,max=20)
    count_head: bpy.props.IntProperty(name="Head",description="",default=0,min=0,max=10)
    count_hairs: bpy.props.IntProperty(name="Hairs",description="",default=0,min=0,max=50)
    count_legs: bpy.props.IntProperty(name="Legs",description="",default=0,min=0,max=20)
    count_foot: bpy.props.IntProperty(name="Feet",description="",default=0,min=0,max=10)
    count_arms: bpy.props.IntProperty(name="Arms",description="",default=0,min=0,max=20)
    count_fingers: bpy.props.IntProperty(name="Fingers",description="",default=0,min=0,max=20)
    
    length_body: bpy.props.IntProperty(name="Length Body",description="",default=1,min=1,max=20)
    length_tails: bpy.props.IntProperty(name="Length Tails",description="",default=1,min=1,max=20)
    length_head: bpy.props.IntProperty(name="Length Head",description="",default=0,min=1,max=20)
    length_hairs: bpy.props.IntProperty(name="Length Hair",description="",default=0,min=1,max=20)
    length_legs: bpy.props.IntProperty(name="Length Legs",description="",default=0,min=1,max=20)
    length_foot: bpy.props.IntProperty(name="Length Feet",description="",default=0,min=1,max=10)
    length_arms: bpy.props.IntProperty(name="Length Arms",description="",default=0,min=1,max=20)
    length_fingers: bpy.props.IntProperty(name="Length Fingers",description="",default=0,min=1,max=20)
    
    #Bools
    edit_widget_active: bpy.props.BoolProperty(name="",description="",default=False)
    show_rig_details: bpy.props.BoolProperty(name="Show details",description="",default=True)
    show_rig_crea: bpy.props.BoolProperty(name="Show Rig Creation",description="",default=True)
    show_ctl_crea: bpy.props.BoolProperty(name="Show Control Creation",description="",default=True)
    bone_connected: bpy.props.BoolProperty(
        name="Connect bones",
        description="Whether the bones created are connected to their parents' tail or not",
        default=False)
    apply_to_children: bpy.props.BoolProperty(
        name="Apply to children",
        description="Whether children of the selected bone should be affected by renaming actions or not",
        default=False)
    leg_ik: bpy.props.BoolProperty(name="Leg IK",description="",default=True)
    leg_fk: bpy.props.BoolProperty(name="Leg FK",description="",default=True)
    arm_ik: bpy.props.BoolProperty(name="Arm IK",description="",default=True)
    arm_fk: bpy.props.BoolProperty(name="Arm FK",description="",default=True)
    
    #Enum
    widget_shape: bpy.props.EnumProperty(
        name="Shape",
        description="Controller's shape given to the active bone",
        items=get_widget_list_items,
    )

    # ─────────────────────────────────────────────
    # SYSTEM
    # ───────────────────────────────────────────── 
    # Bools
    scene_validated: bpy.props.BoolProperty(name="Manual validation",description="Allows you to bypass scene validation to access export operators",default=False)
    abc_export: bpy.props.BoolProperty(name="ABC",description="",default=False)
    fbx_export: bpy.props.BoolProperty(name="FBX",description="",default=False)
    glb_export: bpy.props.BoolProperty(name="GLB",description="",default=False)
    obj_export: bpy.props.BoolProperty(name="OBJ",description="",default=False)
    ply_export: bpy.props.BoolProperty(name="PLY",description="",default=False)
    stl_export: bpy.props.BoolProperty(name="STL",description="",default=False)
    usd_export: bpy.props.BoolProperty(name="USD",description="",default=False)

    # String
    name_export: bpy.props.StringProperty(name="Export name", description="", default="", maxlen=64) 
    unverified_collection: bpy.props.StringProperty(name="Add non-checked Collection",search=collection_search)

class SPT_PG_preset_item(bpy.types.PropertyGroup):
    preset_name: bpy.props.StringProperty()
    preset_filepath: bpy.props.StringProperty()
    origin: bpy.props.StringProperty()  # "user" or "addon"
    selected: bpy.props.BoolProperty(default=False)

class SPT_PG_format_group(bpy.types.PropertyGroup):
    idname: bpy.props.StringProperty()       # ex: "export_scene.fbx"
    label: bpy.props.StringProperty()        # ex: "FBX"
    enabled: bpy.props.BoolProperty(default=False)
    presets: bpy.props.CollectionProperty(type=SPT_PG_preset_item)
