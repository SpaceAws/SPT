# This script contains all the following modeling operators :
#   - Selector :
#       - Selecting all faces touching active one(s), can loop to take all the surface
#   - Blocking :
#       - Importing multiple references at once and auto-placing/renaming them
#       - Creating a plane mirrored in the center and with uv grid material to start with
#

import bpy
import bmesh
import os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, CollectionProperty
from bpy.types import OperatorFileListElement
from mathutils import Vector, Matrix
import math

from .SPT_functions import * 

# TODO :
#   - 

# ─────────────────────────────────────────────

#  OPERATORS

# ─────────────────────────────────────────────
    
class SPT_OT_select_touching_faces(bpy.types.Operator):
    
    bl_idname = "spt.select_touching_faces"
    bl_label  = "Select touching faces"
    bl_description = "Selects faces touching selected one with separate points"
    bl_options = {"UNDO"}
    
    dont_show_again: bpy.props.BoolProperty(
        name="Don't show again",
        default=False,
    )
    
    def invoke(self, context, event): # ─────────────────────────────────────────────
        props = context.scene.spt
        
        if props.loop_selection and not self.dont_show_again:
            # Opens a verification pop-up 
            return context.window_manager.invoke_props_dialog(self)
        else:
            # No verification pop-up
            return self.execute(context)
        
    def draw(self, context): # ─────────────────────────────────────────────
        props = context.scene.spt
        layout = self.layout
        
        # Pop-up content
        layout.label(text="Warning : this operation can take time. Continue ?")
        layout.label(text="You may want to save your project before continuing.")
        
        layout.separator()
        
        row = layout.row()
        row.operator("wm.save_mainfile", text="Save project", icon='FILE_TICK')
        row.prop(self, "dont_show_again")
        
        layout.separator()
        
    def execute(self, context): # ─────────────────────────────────────────────
        props = context.scene.spt
        active_obj, bm = get_bmesh_from_active_object()
                
        # Location table -> vertices list, built once only since locations always stay the same during loop
        pos_to_verts = {}
        for v in bm.verts :
            key = (round(v.co.x, 5), round(v.co.y, 5), round(v.co.z, 5))
            pos_to_verts.setdefault(key, []).append(v)
        
        keep_search = True
        while keep_search :
            # Getting selected vertices and preparing lists
            verts_sel = [v for v in bm.verts if v.select]
            touching_faces = {}
            touching_verts = []
            
            # Getting vertices touching selected ones
            for v_sel in verts_sel :
                key = (round(v_sel.co.x, 5), round(v_sel.co.y, 5), round(v_sel.co.z, 5))
                for v in pos_to_verts.get(key, ()) :
                    if v != v_sel :
                        touching_verts.append(v)
            
            # Getting faces created by touching vertices, counting how many vertices are on the same faces
            for v in touching_verts :
                for face in v.link_faces :
                    if not face in touching_faces.keys() :
                        touching_faces[face] = 0
                    else :
                        touching_faces[face] += 1
            
            if props.select_connected :
                for v in verts_sel :
                    for face in v.link_faces :
                        if not face in touching_faces.keys() :
                            touching_faces[face] = 0
                        else :
                            touching_faces[face] += 1
            
            # Keeping only faces with multiple touching points if diagonal selection is disabled
            i = 0
            minimal_value = 0 if props.select_diagonal else 1
            for f, value in touching_faces.items() :
                if value >= minimal_value and f.select == False :
                    f.select = True
                    i+=1
            
            # Updating bmesh and stopping search if no new faces were found
            bmesh.update_edit_mesh(active_obj.data)
            keep_search = True if i != 0 and props.loop_selection else False
    
        return {"FINISHED"}
        
# ─────────────────────────────────────────────────────────────────────
class SPT_OT_import_refs(bpy.types.Operator):
    
    bl_idname = "spt.import_refs"
    bl_label  = "Import references"
    bl_description = "Imports reference images correctly placed in the scene"
    bl_options = {"UNDO"}

    filter_glob: StringProperty(
        default="*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.bmp;*.exr;*.webp",
        options={"HIDDEN"},
    )

    files: CollectionProperty(type=OperatorFileListElement)
    directory: StringProperty(subtype="DIR_PATH")

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        props = context.scene.spt

        if not self.files:
            self.report({'WARNING'}, "No file selected.")
            return {'CANCELLED'}

        dist = props.ref_distance
        locations = {
            "top"   : (Vector((0,0,-dist)),   (0,0,0),            "FRONT"),
            "bot"   : (Vector((0,0,dist)),    (0,0,0),            "BACK"),
            "front" : (Vector((0,dist,0)),    (1.5708,0,0),       "FRONT"),
            "back"  : (Vector((0,-dist,0)),   (1.5708,0,0),       "BACK"),
            "side"  : (Vector((-dist,0,0)),   (1.5708,0,1.5708),  "FRONT"),
            "left"  : (Vector((-dist,0,0)),   (1.5708,0,1.5708),  "FRONT"),
            "right" : (Vector((dist,0,0)),    (1.5708,0,1.5708),  "BACK"),
            }
        
        # Creating collection
        ref_collection = bpy.data.collections.get("REFERENCES")
        if not ref_collection :
            ref_collection = bpy.data.collections.new("REFERENCES")
            bpy.context.scene.collection.children.link(ref_collection)

        for file_elem in self.files:
            full_path = os.path.join(self.directory, file_elem.name)
            bpy.ops.object.empty_image_add(filepath=full_path)
            img_name = os.path.splitext(file_elem.name)[0]
            obj = context.object

            for key, value in locations.items() :
                if key in img_name.lower() :
                    obj.location = value[0]
                    obj.rotation_euler = value[1]
                    obj.empty_image_side = value[2]
                    pass
            
            obj.name = f"REF_{img_name}" if not "REF_" in img_name else img_name
            bpy.context.collection.objects.unlink(obj)
            ref_collection.objects.link(obj)  

        return {'FINISHED'}
        
    def invoke(self, context, event): # ─────────────────────────────────────────────
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# ─────────────────────────────────────────────────────────────────────
class SPT_OT_create_mirrored_obj(bpy.types.Operator):
    
    bl_idname = "spt.create_mirrored_obj"
    bl_label  = "Create mirrored plane"
    bl_description = "Creates a plane cut in half with mirror modifier"
    bl_options = {"UNDO"}

    def execute(self, context):
        props = context.scene.spt

        # Creating plane and getting its bmesh
        bpy.ops.mesh.primitive_plane_add()
        obj, bm = get_bmesh_from_active_object()

        # Moving verts at center
        for v in bm.verts :
            if v.co.x < 0 :
                v.co.x = 0
        bmesh.update_edit_mesh(obj.data)

        # Setting name and mirror modifier
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.name = f"GEO_{props.plane_name}"
        obj.modifiers.new(name="Mirror", type="MIRROR")

        # Setting material
        material = bpy.data.materials.get(f"M_{props.plane_name}")
        if not material :
            material = bpy.data.materials.new(f"M_{props.plane_name}")
        material.use_nodes = True
        obj.data.materials.append(material)
        obj.active_material_index = len(obj.data.materials) - 1

        # Setting UV grid texture
        # Getting principled BSDF
        principled = material.node_tree.nodes.get("Principled BSDF")

        # Creating UV grid image
        image = bpy.data.images.new(name="UV_Checker", width=1024, height=1024)
        image.generated_type = 'UV_GRID'

        # Creating image texture node
        tex_node = material.node_tree.nodes.new(type="ShaderNodeTexImage")
        tex_node.image = image
        tex_node.location = (principled.location.x - 300, principled.location.y)

        # Color -> Base Color connexion
        material.node_tree.links.new(tex_node.outputs["Color"], principled.inputs["Base Color"])

        return {'FINISHED'}
