# This script contains all the following functions :
#   - General :
#       - draw_wrapped_label : automatically cuts the given text to fit in the panel
#       - parse_string : parses a string in 4 pieces : prefix, base, count_suffix and side_suffix based on "_" and "."
#   - Animation :
#       - bone_search : returns the active object's bone name list (used as property auto-completion method)
#       - get_fcurves : returns the given action's (context.active_object.animation_data.action) fcurves, used to access keyframes and channels
#   - Modeling :
#       - get_bmesh_from_active_object : gets bmesh from active object so it can be used in python
#   - Rigging :
#       - bone_matrix : updates the transforms of the widget object to match the transforms of the bone
#       - check_collections : checks for bone collections, used in create_fk_controller()
#       - create_bone : creates a new bone based on all given parameters
#       - create_controller : sends a list of vertices and edges to create_shape() based on desired shape and returns created controller
#       - create_controllers : automatically creates needed controllers for create_fk_controller()
#       - create_fk_controller : creates a new bone copying selected one which will be used as a controller
#       - create_shape : creates a new shape based on given vertices and edges
#       - fmt_index : returns the correct format for given index (0# or ##)
#       - from_widget_find_bone : given an object, tries to find the bone that the object is a custom widget of
#       - get_view_layer_collection : gets the view layer collection of the given widget object
#       - recursively_find_layer_collection : recursively finds a collection with a specified collection name
#       - remove_sfx_number : removes .### numeral from selected bone to instead increment its count suffix such as _## and its equivalent's suffix as well
#       - select_children : selects current bone children
#       - update_rig_preset : automatically updates rig properties based on selected preset
#   - System :
#       - check_normals_outward : returns whether the normals are fine or not (True for fine)
#       - check_name : returns whether any object in the scene has an unaccepted name (True for no problems)
#       - count_total_verts : returns total poly count in the scene
#       - get_issues : applies all checking systems to the entire scene and returns a value for each checked common issue to tell if it is present
#       - fix_obj_name : fixes current object's name to match restriction
#       - get_presets_for_operator : returns found presets for the given export format
#       - PresetPropCollector, PresetFakeContext, PresetFakeBpy : classes used to create a fake environment for reading preset properties safely
#       - read_preset_properties : reads the properties from given preset
#       - export_with_preset : exports scene using given format and preset
#       - find_export_operators : searches for all export formats available to list them in the export tool
#   - JSON
#       - load_widgets_data : loads dictionnary stocked in json
#       - save_widgets_data : saves dictionnary in json
#       - get_widget_list_items : called by enumproperty to display widget list
#

import bpy
import bmesh
from mathutils import Vector, Matrix
import math
import json
import os

# ─────────────────────────────────────────────

#  VARIABLES

# ─────────────────────────────────────────────

WIDGET_JSON_PATH = os.path.join(os.path.dirname(__file__), "SPT_widgets.json")
widget_items_cache = []

# ─────────────────────────────────────────────

#  FUNCTIONS

# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
#  GENERAL
# ─────────────────────────────────────────────

def draw_wrapped_label(layout, context, text, icon="NONE", width=0, char_size=8):
    # Approximates width in chars (region.width is in pixels, ~7px per char)
    region_width = width if width != 0 else context.region.width
    chars_per_line = int(region_width / char_size)
    
    words = text.split()
    line = ""
    first = True
    
    for word in words:
        if len(line) + len(word) + 1 <= chars_per_line:
            line = f"{line} {word}".strip()
        else:
            # Displays current line and starting another one
            layout.label(text=line, icon=icon if first else "NONE")
            first = False
            line = word
    
    # Displays the rest
    if line:
        layout.label(text=line, icon=icon if first else "NONE")

# ──────────────────────────────────────────────────────────────────────────────────────────        
def parse_string(string):
    parsed_string = []
    prfx, base, count_sfx, side_sfx = "", "", "", ""
    parsed = False
    while not parsed :
        if "_" in string:
            idx = string.index("_") + 1   # index of the char following the underscore
            parsed_string.append(string[:idx]) # gets what's before index
            string = string[idx:]
        elif "." in string:
            idx = string.index(".")   # index of the char following the point
            side_sfx = string[idx:]   # gets what's after index as side_sfx directly
            string = string[:idx]
        else :
            parsed_string.append(string) # if all underscores and points have been found, adds the rest
            parsed = True
    if len(parsed_string) > 1 :
        prfx = parsed_string[0]
        parsed_string.remove(prfx)
    if parsed_string[len(parsed_string)-1][0].isdigit(): 
        count_sfx = parsed_string[len(parsed_string)-1]
        parsed_string.remove(count_sfx)
    base = ""
    for i, part in enumerate(parsed_string):
        base = f"{base}{part}"
    
    return prfx, base, count_sfx, side_sfx

# ─────────────────────────────────────────────
#  ANIMATION
# ─────────────────────────────────────────────

def bone_search(self, context, edit_text):
    obj = context.active_object
    if obj and obj.type == "ARMATURE":
        return [bone.name for bone in obj.pose.bones]
    return []

# ──────────────────────────────────────────────────────────────────────────────────────────
def get_fcurves(action):
    if action.is_action_legacy:
        # before Blender 4.4 : old system
        return action.fcurves
    else:
        # Blender 4.4+ : layer system
        fcurves = []
        for layer in action.layers:
            for strip in layer.strips:
                for channelbag in strip.channelbags:
                    fcurves.extend(channelbag.fcurves)
        return fcurves

# ─────────────────────────────────────────────
#  MODELING
# ─────────────────────────────────────────────

def get_bmesh_from_active_object():
    obj = bpy.context.edit_object  # None if not in edit mode
    if obj is None:
        # Force edit mode if needed
        obj = bpy.context.active_object
        if obj is None or obj.type != 'MESH':
            raise RuntimeError("Aucun objet mesh actif.")
        bpy.ops.object.mode_set(mode='EDIT')
 
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    return obj, bm

# ─────────────────────────────────────────────
#  RIGGING
# ─────────────────────────────────────────────

def bone_matrix(context: 'Context', widget: 'Object', match_bone: 'PoseBone'):
    """
    // Developped by Manuel Rais and Christophe Seux (bone widget addon) //
    
    context (Context): The current Blender context.
    widget (Object): The widget object.
    match_bone (PoseBone): The bone to match the transforms of.
    """

    if widget == None:
        return

    widget.matrix_local = match_bone.bone.matrix_local

    # Multiply the bones world matrix with the bones local matrix.
    widget.matrix_world = match_bone.id_data.matrix_world @ match_bone.bone.matrix_local
    if match_bone.custom_shape_transform:
        # if it has a tranform override apply this to the widget loc and rot
        org_scale = widget.matrix_world.to_scale()
        org_scale_mat = Matrix.Scale(1, 4, org_scale)
        target_matrix = match_bone.custom_shape_transform.id_data.matrix_world @ match_bone.custom_shape_transform.bone.matrix_local
        loc = target_matrix.to_translation()
        loc_mat = Matrix.Translation(loc)
        rot = target_matrix.to_euler().to_matrix()
        widget.matrix_world = loc_mat @ rot.to_4x4() @ org_scale_mat

    if match_bone.use_custom_shape_bone_size:
        ob_scale = context.scene.objects[match_bone.id_data.name].scale
        widget.scale = [match_bone.bone.length * ob_scale[0],
                        match_bone.bone.length * ob_scale[1], match_bone.bone.length * ob_scale[2]]
        # widget.scale = [match_bone.bone.length, match_bone.bone.length, match_bone.bone.length]
    widget.data.update()
    
# ──────────────────────────────────────────────────────────────────────────────────────────
def check_collections(props, active_rig, sfx, control_bones_created):
    # Checking if collections exist, creating them if not
    skin_collection = active_rig.collections.get(props.skin_prfx[:-1]) or active_rig.collections.get("Bones")
    if skin_collection :
        skin_collection.name = props.skin_prfx[:-1]
    else:
        skin_collection = active_rig.collections.new(props.skin_prfx[:-1])
    control_collection = active_rig.collections.get(f"{props.control_prfx}{sfx}")
    if not control_collection :
        control_collection = active_rig.collections.new(f"{props.control_prfx}{sfx}")
        
    bpy.ops.object.mode_set(mode="OBJECT")
    for bone_name, control_name in control_bones_created:
        skin_bone    = active_rig.bones.get(bone_name)
        control_bone = active_rig.bones.get(control_name)
        skin_collection.assign(skin_bone)
        control_collection.assign(control_bone)
        
# ──────────────────────────────────────────────────────────────────────────────────────────
def create_bone(collection, name, head_loc, tail_loc, parent, connected, roll=0.0):
    bone = collection.new(name)     #bpy.data.armatures.edit_bones
    bone.head = head_loc            #Vector((0,0,0))
    bone.tail = tail_loc            #Vector((0,0,0))
    bone.roll = roll                #float
    bone.parent = parent            #bone
    bone.use_connect = connected    #bool
    return bone

# ──────────────────────────────────────────────────────────────────────────────────────────
def create_controller(context, shape_key, name):
    verts_list = []
    
    # Creates a hidden collection for control shapes if it doesn't already exist
    ctrl_collection = bpy.data.collections.get("CTRL_Shapes")
    if not ctrl_collection :
        ctrl_collection = bpy.data.collections.new("CTRL_Shapes")
        bpy.context.scene.collection.children.link(ctrl_collection)
        ctrl_collection.hide_viewport = True
    
    # Deletes old obj if it exists
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)

    # Loads shape from json file
    widgets_data = load_widgets_data()
    shape_info = widgets_data.get(shape_key)

    if shape_info is None:
        raise ValueError(f"Shape '{shape_key}' not found in 'SPT_widgets.json'.")

    # Gets vertices and edges from data
    verts_list = [Vector(v) for v in shape_info["verts"]]
    edges_list = shape_info["edges"]
    
    # Sends infos to create_shape()
    controller = create_shape(name, verts_list, edges_list)
    
    # Sets collection
    bpy.context.collection.objects.unlink(controller)
    ctrl_collection.objects.link(controller)
    return controller

# ──────────────────────────────────────────────────────────────────────────────────────────
def create_controllers(context, bones):
    props = context.scene.spt
    active_obj = context.active_object
    
    bpy.ops.object.mode_set(mode="OBJECT")
    shapes = []
    widget_bones = []
    for bone_name in bones:
        shape_type = "Cube" if "IK" in bone_name or "Body" in bone_name else "Square_root" if "Position" in bone_name else "Circle_root" if "Trajectory" in bone_name else "Circle" if "Root" in bone_name else "Circle90"
        shape = create_controller(context, shape_type, f"{active_obj.name}_{bone_name}") 
        shapes.append(shape)
        widget_bones.append(bone_name)

    # ── Assign color and shape in Pose Mode ──
    for i, name in enumerate(widget_bones):
        bone = active_obj.pose.bones[name]
        color = props.bone_color_r if name[-2:] == ".r" else props.bone_color_l if name[-2:] == ".l" else props.bone_color
        context.view_layer.objects.active = bone.id_data
        bone.color.palette = "CUSTOM" 
        bone.color.custom.normal = color
        bone.color.custom.select = color *1.25
        bone.color.custom.active = color *1.5
        bone.rotation_mode = 'XYZ'
        if shapes[i]:
            bone.custom_shape = shapes[i] 
            
# ──────────────────────────────────────────────────────────────────────────────────────────            
def create_fk_controller(context, bones):
    props = context.scene.spt
    active_obj = context.active_object
    active_rig = active_obj.data
    
    # ── Creating control rig ──
    # ── Creating bones ──     
    bpy.ops.object.mode_set(mode="EDIT")
    control_bones_created = []  # stocks names to access them later
    for bone in bones :
        if bone.name.startswith(props.skin_prfx) :                
            control_bone = active_rig.edit_bones.get(f"{props.control_prfx}FK_{bone.name[len(props.skin_prfx):]}")
            if not control_bone :
                control_bone = active_rig.edit_bones.new(f"{props.control_prfx}FK_{bone.name[len(props.skin_prfx):]}")
                control_bone.head        = bone.head.copy()   # .copy() important for Vectors
                control_bone.tail        = bone.tail.copy()
                control_bone.roll        = bone.roll
                parent_bone = active_rig.edit_bones.get(f"{props.control_prfx}FK_{bone.parent.name[len(props.skin_prfx):]}") or active_rig.edit_bones.get(f"{props.skin_prfx}Root")
                control_bone.parent      = parent_bone
                control_bone.use_deform = False
            control_bones_created.append((bone.name, control_bone.name))
            
    # Creates or gets controller collection
    check_collections(props, active_rig, "FK", control_bones_created)
                    
    # ── Creating copy transforms constraints
    bpy.ops.object.mode_set(mode="POSE")
    for bone_name, control_name in control_bones_created:
        pose_bone = active_obj.pose.bones[bone_name]
        control_bone = active_obj.pose.bones[control_name]
        constraint = pose_bone.constraints.new("COPY_TRANSFORMS")
        constraint.target    = active_obj        # l'objet cible (peut être une autre armature)
        constraint.subtarget = control_bone.name   # nom du bone cible (string)
        constraint.name = "Copy Transforms FK"
    
    # ── Creating controller shapes ──                
    # ── Creating shape in Object Mode ──
    shape_bones = []
    for bone_name, control_name in control_bones_created:
        shape_bones.append(control_name)
    create_controllers(context, shape_bones)

# ──────────────────────────────────────────────────────────────────────────────────────────    
def create_shape(name, vertices_positions, edges):
    # Creates mesh data and object
    mesh = bpy.data.meshes.new(name)
    obj  = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Adds geometry using bmesh
    bm = bmesh.new()

    # Creates vertices
    verts = [bm.verts.new(pos) for pos in vertices_positions]

    if edges == None:
        # If no edges are given, creates edges between vertices following their indices
        for i in range(len(verts)):
            bm.edges.new([verts[i], verts[(i + 1) % len(verts)]])  # % to loop on the last one with the first one
    else:
        # Else creates edges as required from the given information
        for a, b in edges:
            bm.edges.new([verts[a], verts[b]])

    # Sends bmesh to mesh
    bm.to_mesh(mesh)
    bm.free()

    return obj

# ──────────────────────────────────────────────────────────────────────────────────────────
def fmt_index(n):
    return f"_0{n}" if n < 10 else f"_{n}"

# ──────────────────────────────────────────────────────────────────────────────────────────
def from_widget_find_bone(context, widget: 'Object') -> 'PoseBone':
    """
    // Developped by Manuel Rais and Christophe Seux (bone widget addon) //
    
    Returns:
        PoseBone: The bone, that the object is a widget of.
    """

    match_bone = None
    for ob in context.scene.objects:
        ob: 'Object'
        if ob.type != "ARMATURE":
            continue

        for bone in ob.pose.bones:
            bone: 'PoseBone'
            if bone.custom_shape == widget:
                match_bone: 'PoseBone' = bone
    return match_bone

# ──────────────────────────────────────────────────────────────────────────────────────────
def get_view_layer_collection(context: 'Context', widget: 'Object' = None) -> 'LayerCollection':
    """
    // Developped by Manuel Rais and Christophe Seux (bone widget addon) //
    
    Returns:
        LayerCollection: The view layer collection of the widget object.
    """

    widget_collection: 'Collection' = bpy.data.collections[
        bpy.data.objects[widget.name].users_collection[0].name]
    # save current active layer_collection
    saved_layer_collection: 'LayerCollection' = context.view_layer.layer_collection
    # actually find the view_layer we want
    layer_collection: 'LayerCollection' = recursively_find_layer_collection(
        saved_layer_collection, widget_collection.name)
    # make sure the collection (data level) is not hidden
    widget_collection.hide_viewport = False

    # change the active view layer
    context.view_layer.active_layer_collection = layer_collection
    # make sure it isn't excluded so it can be edited
    layer_collection.exclude = False
    # return the active view layer to what it was
    context.view_layer.active_layer_collection = saved_layer_collection

    return layer_collection

# ──────────────────────────────────────────────────────────────────────────────────────────
def recursively_find_layer_collection(layer_collection: 'Collection', collection_name: str) -> 'Collection':
    """
    // Developped by Manuel Rais and Christophe Seux (bone widget addon) //
    
    Args:
        layer_collection (Collection): The collection to start searching from.
        collection_name (str): The name of the searched collection.

    Returns:
        Collection: The collection that has been searched for.
    """

    found: 'Collection' = None

    if layer_collection.name == collection_name:
        return layer_collection

    for layer in layer_collection.children:
        found = recursively_find_layer_collection(layer, collection_name)
        if found:
            return found
        
# ──────────────────────────────────────────────────────────────────────────────────────────
def remove_sfx_numbers(context, curr_bone):
    active_obj = context.active_object
    new_name = curr_bone.name
    
    # Checking if there is a .### numeral suffix
    if len(new_name) > 4 and new_name[-4] == "." and new_name[-3:].isdigit():
        new_name = new_name[:-4]
    
    # Parsing new_name
    prfx, base, count_sfx, side_sfx = parse_string(new_name)
    if base[-1] == "_" :
        base = base[:-1]
    unique = False
    i = 0
    while not unique :
        # Setting new_name, then checking if it is unique or increment count_sfx
        new_name = f"{prfx}{base}{fmt_index(i)}{side_sfx}"
        bone = active_obj.data.edit_bones.get(new_name) if context.object.mode == 'EDIT' else active_obj.pose.bones.get(new_name)
        if not bone :
            base_name = f"{prfx}{base}{side_sfx}"
            base_bone = active_obj.data.edit_bones.get(base_name) if context.object.mode == 'EDIT' else active_obj.pose.bones.get(base_name)
            if base_bone and base_bone != curr_bone :
                base_bone.name = f"{prfx}{base}_00{side_sfx}"
                new_name = f"{prfx}{base}{fmt_index(i+1)}{side_sfx}"
            elif i == 0 :
                new_name = f"{prfx}{base}{side_sfx}"
            unique = True
        elif bone == curr_bone :
            if i == 0 :
                new_name = f"{prfx}{base}{side_sfx}"
            unique = True
        i+=1
        
    return new_name
  
# ──────────────────────────────────────────────────────────────────────────────────────────  
def select_children(context, bone):
    children = []
    for child in bone.children_recursive:
        children.append(child)

    for child in children:
        child.select = True
        if context.object.mode == 'EDIT': # needs some extra selection in edit mode so it is considered selected in viewport
            child.select_head  = True
            child.select_tail  = True
              
# ──────────────────────────────────────────────────────────────────────────────────────────
def update_rig_preset(self, context):
    if self.rig_preset == "CUSTOM":
        pass
    elif self.rig_preset == "BASIC":
        values = [1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1]
    elif self.rig_preset == "HUMANOID":
        values = [1,4,2,3,1,2,2,4,5,3,1,2,0,0,0,1]
    elif self.rig_preset == "ARACHNID":
        values = [1,1,8,4,1,2,0,1,0,1,1,1,0,1,0,1]
    self.count_body    = values[0]
    self.length_body   = values[1]
    self.count_legs    = values[2]
    self.length_legs   = values[3]
    self.count_foot    = values[4]
    self.length_foot   = values[5]
    self.count_arms    = values[6]
    self.length_arms   = values[7]
    self.count_fingers = values[8]
    self.length_fingers= values[9]
    self.count_head    = values[10]
    self.length_head   = values[11]
    self.count_hairs   = values[12]
    self.length_hairs  = values[13]
    self.count_tails   = values[14]
    self.length_tails  = values[15]

# ─────────────────────────────────────────────
#  SYSTEM
# ─────────────────────────────────────────────

def check_normals_outward(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)  # copies data to avoid live reference and modification
    bm.faces.ensure_lookup_table()

    before = [f.normal.copy() for f in bm.faces]

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    after = [f.normal.copy() for f in bm.faces]

    bm.free()  # frees copy from memory

    flipped_count = sum(
        1 for n_before, n_after in zip(before, after)
        if n_before.dot(n_after) < 0
    )

    return flipped_count == 0

# ──────────────────────────────────────────────────────────────────────────────────────────
def check_name(obj):
    name = obj.name

    unaccepted_char = [" ", "&", "é", "#", "è", "à", "@", "ç", "ù", "*", "{", "}", "(", ")", "[", "]", "€", "$", "~"]
    for char in unaccepted_char :
        if char in name :
            return False
    
    if len(name) > 4 and name[-4] == "." and name[-3:].isdigit():
        return False
    
    return True

# ──────────────────────────────────────────────────────────────────────────────────────────
def count_total_verts(context):
    depsgraph = context.evaluated_depsgraph_get()
    total = 0

    for obj in context.scene.objects:
        if obj.type != 'MESH':
            continue

        obj_eval = obj.evaluated_get(depsgraph)
        mesh_eval = obj_eval.to_mesh()

        total += len(mesh_eval.vertices)

        obj_eval.to_mesh_clear()  # libère la mesh temporaire générée

    return total

# ──────────────────────────────────────────────────────────────────────────────────────────
def get_issues(context):
    props  = context.scene.spt

    validation_check = []
    for i in range(9) :
        validation_check.append(1)

    uv_objects = []
    loc_objects = []
    scale_objects = []
    rot_objects = []
    normals_objects = []
    name_objects = []
    smooth_objects = []
    modifier_objects = []

    for obj in context.scene.objects:
        if obj.type == "MESH" and obj.visible_get() and not obj.data.uv_layers:
            validation_check[0] = 0
            uv_objects.append(obj.name)
        
        if obj.type in ["MESH", "ARMATURE"] and not obj.location == Vector((0.0,0.0,0.0)):
            validation_check[1] = 0
            loc_objects.append(obj.name)
        
        if not obj.scale == Vector((1.0,1.0,1.0)):
            validation_check[2] = 0
            scale_objects.append(obj.name)

        rot = (obj.rotation_euler[0], obj.rotation_euler[1], obj.rotation_euler[2])
        if not rot == (0.0, 0.0, 0.0):
            validation_check[3] = 0
            rot_objects.append(obj.name)
        
        if obj.type == "MESH" and obj.visible_get() and not check_normals_outward(obj):
            validation_check[4] = 0
            normals_objects.append(obj.name)
        
        if not check_name(obj):
            validation_check[5] = 0
            name_objects.append(obj.name)

        if obj.type == "MESH":
            smoothed = False
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group is not None:
                    if mod.node_group.name.startswith("Smooth by Angle"):
                        smoothed = True
            if not smoothed :
                validation_check[6] = 0
                smooth_objects.append(obj.name)

        hidden = False
        for mod in obj.modifiers:
            if not mod.show_viewport:
                hidden = True
        if hidden :
            validation_check[7] = 0
            modifier_objects.append(obj.name)

        if count_total_verts(context) >= 100000 :
            validation_check[8] = 0

    messages=[
            f"UVs issues",
            f"Location issues",
            f"Scale issues",
            f"Rotation issues",
            f"Normals issues",
            f"Naming issues",
            f"Smooth issues",
            f"Modifiers issues",
            "Poly count > 100 000",
            ]
    operators=[
            "spt.uv_creation",
            "spt.apply_location",
            "spt.apply_scale",
            "spt.apply_rot",
            "spt.normals_orient",
            "spt.fix_name",
            "spt.apply_smooth",
            "spt.show_modifier",
            ""
            ]
    objects=[
            uv_objects,
            loc_objects,
            scale_objects,
            rot_objects,
            normals_objects,
            name_objects,
            smooth_objects,
            modifier_objects,
            "",
            ]

    return validation_check, messages, operators, objects

# ──────────────────────────────────────────────────────────────────────────────────────────
def fix_obj_name(context, obj):
    new_name = obj.name

    unaccepted_char = ["&", "é", "#", "è", "à", "@", "ç", "ù", "*", "{", "}", "(", ")", "[", "]", "€", "$", "~"]
    for i, char in enumerate(new_name):
        if char in unaccepted_char :
            new_name = f"{new_name[:i]}{new_name[i+1:]}"

    for i, char in enumerate(new_name):
        if char == " " :
            new_name = f"{new_name[:i]}_{new_name[i+1:]}"

    if len(new_name) > 4 and new_name[-4] == "." and new_name[-3:].isdigit():
        new_name = new_name[:-4]
        unique = False
        i = 0
        while not unique :
            # Setting new_name, then checking if it is unique or increment
            curr_name = f"{new_name}{fmt_index(i)}"
            curr_obj = context.scene.objects.get(curr_name)

            if not curr_obj :
                base_obj = context.scene.objects.get(new_name)
                if base_obj and base_obj != obj :
                    base_obj.name = f"{new_name}_00"
                    new_name = f"{new_name}{fmt_index(i+1)}"
                elif i != 0 :
                    new_name = curr_name
                unique = True
            elif curr_obj == obj :
                unique = True
            i+=1

    obj.name=new_name

# ──────────────────────────────────────────────────────────────────────────────────────────
def get_presets_for_operator(bl_idname):
    """bl_idname ex: 'export_scene.fbx'"""
    subdir = f"operator/{bl_idname}"
    preset_dirs = bpy.utils.preset_paths(subdir)

    presets = []
    for folder in preset_dirs:
        if not os.path.isdir(folder):
            continue
        for filename in sorted(os.listdir(folder)):
            if filename.endswith(".py"):
                presets.append({
                    "name": os.path.splitext(filename)[0],
                    "filepath": os.path.join(folder, filename),
                })
    return presets

# ──────────────────────────────────────────────────────────────────────────────────────────
class PresetPropCollector:
    def __init__(self):
        object.__setattr__(self, "properties", {})

    def __setattr__(self, name, value):
        self.properties[name] = value

# ──────────────────────────────────────────────────────────────────────────────────────────
class PresetFakeContext:
    def __init__(self, collector):
        self.active_operator = collector

# ──────────────────────────────────────────────────────────────────────────────────────────
class PresetFakeBpy:
    def __init__(self, collector):
        self.context = PresetFakeContext(collector)

# ──────────────────────────────────────────────────────────────────────────────────────────
def read_preset_properties(preset_filepath):
    collector = PresetPropCollector()
    fake_bpy = PresetFakeBpy(collector)

    with open(preset_filepath, "r", encoding="utf-8") as f:
        code = f.read()
    
    # Neutralizes import lines destroying fake bpy
    cleaned_lines = [
        line for line in code.splitlines()
        if not line.strip().startswith("import bpy")
    ]
    cleaned_code = "\n".join(cleaned_lines)

    exec(compile(cleaned_code, preset_filepath, "exec"), {"bpy": fake_bpy})

    return collector.properties

# ──────────────────────────────────────────────────────────────────────────────────────────
def export_with_preset(bl_idname, preset_filepath, output_filepath):
    props = read_preset_properties(preset_filepath)
    props["filepath"] = output_filepath

    category, op_name = bl_idname.split(".")
    export_func = getattr(getattr(bpy.ops, category), op_name)

    return export_func(**props)

# ──────────────────────────────────────────────────────────────────────────────────────────
def find_export_operators():
    """Detecte tous les operateurs d'export de fichier reels (via bpy.ops,
    plus fiable que dir(bpy.types)), en filtrant sur la presence des
    proprietes 'filepath' + 'filter_glob' typiques des exporteurs 
    utilisant ExportHelper."""

    EXPORT_BLACKLIST = {
        "wm.keyconfig_export",
        "anim.keying_set_export",
        "uv.export_layout",
        "spt.export_tool",
        }
    exporters = []

    for cat_name in dir(bpy.ops):
        if cat_name.startswith("_"):
            continue
        category = getattr(bpy.ops, cat_name)

        for op_name in dir(category):
            idname = f"{cat_name}.{op_name}"

            if "export" not in idname.lower():
                continue
            if idname in EXPORT_BLACKLIST:
                continue

            op = getattr(category, op_name)
            try:
                rna = op.get_rna_type()
            except AttributeError:
                continue

            props = rna.properties.keys()

            # Heuristique : un vrai exporteur de fichier a "filepath" 
            # ET "filter_glob" (ajoutes automatiquement par ExportHelper)
            if "filepath" not in props or "filter_glob" not in props:
                continue

            exporters.append({
                "idname": idname,
                "label": rna.name,
            })

    return sorted(exporters, key=lambda e: e["label"])

# ─────────────────────────────────────────────
#  JSON
# ─────────────────────────────────────────────

def get_widget_list_items(self, context):
    global widget_items_cache
    data = load_widgets_data()

    items = []
    for i, (key, info) in enumerate(data.items()):
        items.append((
            key,
            info.get("label", key),
            "",  # description
            info.get("icon", "MESH_CIRCLE"),
            i,
        ))

    widget_items_cache = items
    return widget_items_cache

# ──────────────────────────────────────────────────────────────────────────────────────────
def load_widgets_data():
    if not os.path.exists(WIDGET_JSON_PATH):
        return {}
    with open(WIDGET_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ──────────────────────────────────────────────────────────────────────────────────────────
def save_widgets_data(data):
    with open(WIDGET_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
