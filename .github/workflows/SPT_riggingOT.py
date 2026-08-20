# This script contains all the following rigging operators :
#   - General :
#       - Selecting parents or children of selected bone(s)
#   - Parameters :
#       - Setting used prefixes
#       - Setting used controller colors
#   - Renamer :
#       - Removing .### suffix and replacing it with a logical _## suffix
#       - Adding prefixes or switching them between defined ones
#       - Adding suffixes or switching them between .l and .r
#   - Creator :
#       - Creating a custom rig composed with customizable bone chains and chain lengths (with some presets)
#       - Creating a control rig for the selected rig
#   - Widgets :
#       - Creating preset widgets, accessing them via pose mode to edit rapidly
#       - Getting the shape to match bone's transforms to modify it cleanly
#       - Deleting current bone's widget
#       - Making current widget unique
#       - Saving current mesh or bone's shape as a shape to be used later
#

import bpy
import bmesh
from mathutils import Vector, Matrix
import math

from .SPT_functions import * 

#TODO : 
#       utiliser le système de custom rig pour ajouter des éléments à un rig existant en prenant le bone actif comme parent
#       ajouter un clear all widgets d'une armature/unused
#       améliorer le système d'IK avec du stretch
#       créer autant de properties ik/fk qu'il y a de membres (bras/jambes) et donc autant de boutons aussi

# ─────────────────────────────────────────────

#  OPERATORS

# ─────────────────────────────────────────────

class SPT_OT_base_bone_action(bpy.types.Operator):
    """
    Defining poll for all buttons requiring to be in pose/edit mode, be an armature and having a selected bone
    """
    bl_idname = "spt.base_bone_action" 
    bl_options = {"REGISTER", "UNDO"}
    bl_label = "Base Bone Action"
    
    @classmethod
    def poll(cls, context):
        if context.object :
            active_bone = context.active_pose_bone if context.object.mode == 'POSE' else context.active_bone
        return (context.object and context.object.type == 'ARMATURE'
            and context.object.mode in ['POSE', 'EDIT'] and active_bone)

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_create_custom_rig(bpy.types.Operator):
    """
    Creating a custom rig based on bone counts and length defined in properties
    """
    bl_idname = "spt.create_custom_rig"
    bl_label  = "Create Custom Rig"
    bl_description = "Creates a custom rig using the selected bones"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        """
        Main function of the class, executing other functions in the right order when button is pressed
        """
        props = context.scene.spt
        
        # ── Creating rig and roots ────────────────────────────────────────────────────────────────
        self.create_rig(context)
        self.create_roots(context) 
        
        # ── Creating bone chains ────────────────────────────────────────────────────────────────
        bpy.ops.object.mode_set(mode="EDIT")
        self.assign_variables(context)
        self.create_body_tail(context)
        self.create_head_hair(context)
        self.create_leg_foot(context)
        self.create_arm_finger(context)
        
        self.create_collection(context)
        self.clean_rig()
        
        self.report({"INFO"}, "Rig successfully created")
        return {"FINISHED"}
    
    
    def create_rig(self, context): # ──────────────────────────────────────────────────────────────────
        """
        Creates rig object
        """
        props = context.scene.spt
        
        # ── Creating rig object and its data ──
        self.rig_data = bpy.data.armatures.new(name=props.new_rig_name)
        self.rig_obj  = bpy.data.objects.new(name=props.new_rig_name, object_data=self.rig_data)
 
        # ── Linking created rig to the scene and making it active ──
        context.collection.objects.link(self.rig_obj)
        context.view_layer.objects.active = self.rig_obj
        self.rig_obj.select_set(True)
        
    
    def create_roots(self, context): # ──────────────────────────────────────────────────────────────────
        """
        Creates Position, Trajectory and Root bones with their controllers
        """
        props = context.scene.spt
        
        # ── Going to edit mode to enable bone creation ──
        bpy.ops.object.mode_set(mode="EDIT")
        self.edit_bones = self.rig_data.edit_bones  # Editbone collection
        
        # ── Creating bones using defined function ──
        bone_position=create_bone(self.edit_bones, f"{props.skin_prfx}Position", Vector((0, 0, -1)), Vector((0, 1, -1)), None, False)
        bone_trajectory=create_bone(self.edit_bones, f"{props.skin_prfx}Trajectory", Vector((0, 0, -1)), Vector((0, 1, -1)), bone_position, False)
        bone_root=create_bone(self.edit_bones, f"{props.skin_prfx}Root", Vector((0, 0, -1)), Vector((0, 1, -1)), bone_trajectory, False)
        
        # ── Creating bones' control shapes ──
        bone_names = [bone_position.name, bone_trajectory.name, bone_root.name]
        create_controllers(context, bone_names)
                
    
    def assign_variables(self, context): # ──────────────────────────────────────────────────────────────────
        """
        Assigns self variables a value to allow them to be called later
        """
        props = context.scene.spt
        
        self.bone_body = self.rig_data.edit_bones[f"{props.skin_prfx}Root"]
        self.bone_tail = None
        self.bone_head = None
        self.bone_hair = None
        self.bone_leg = None
        self.bone_foot = None
        self.bone_arm = None
        self.bone_finger = None
        
    
    def create_body_tail(self, context): # ──────────────────────────────────────────────────────────────────
        """
        Creates body and tails bone chains
        """
        props = context.scene.spt
        
        # ── Creating bodies ────────────────────────────────
        # ── Creating names ──
        if props.length_body == 1:
            bone_names = ["Body"]
        else :
            bone_names = []
            for i in range(props.length_body) :
                bone_names.append(f"Spine{fmt_index(i)}")
        
        # ── Creating bones ──    
        for i in range (props.count_body):
            for j in range (props.length_body):
                parent_bone = self.rig_data.edit_bones[f"{props.skin_prfx}Root"] if j == 0 else self.bone_body
                bone_name = f"{props.skin_prfx}{bone_names[j]}"
                bone_connect = False if j == 0 else props.bone_connected
                self.bone_body = create_bone(self.edit_bones, bone_name, Vector((0, 0, j/props.length_body)), Vector((0, 0, (j/props.length_body)+1/props.length_body)), parent_bone, bone_connect)
        
        # ── Creating tails ────────────────────────────────
        # ── Creating names ──
        bone_names = []
        for x in range(props.length_tails) :
            bone_names.append(f"Tail{fmt_index(x)}")
                
        # ── Creating bones ──    
        for i in range(props.count_tails):
            
            self.set_bases(i, props.count_tails, 0, True, 0.5) #idx, count, offset, sided, rayon

            for j in range(props.length_tails):
                
                self.set_parent_and_location(props, j, self.bone_body, self.bone_tail, props.length_tails, True) #props, idx, parent0, parent1, length, constant_z
                self.set_name(props, i, props.count_tails, bone_names[j]) #props, idx0, count, base_name
                self.bone_tail = create_bone(self.edit_bones, self.bone_name, self.head, self.tail, self.parent_bone, self.bone_connect)
                
    
    def create_head_hair(self, context): # ──────────────────────────────────────────────────────────────────
        """
        Creates heads and hairs bone chains
        """
        props = context.scene.spt
        
        # ── Creating heads ────────────────────────────────
        # ── Creating names ──
        if props.length_head == 1:
            bone_names = ["Head"]
        elif props.length_head <= 2:
            bone_names = ["Neck", "Head"]
        else :
            bone_names = []
            for i in range(props.length_head-1) :
                bone_names.append(f"Neck{fmt_index(i)}")
            bone_names.append("Head")
                
        # ── Creating bones ──    
        for i in range(props.count_head):
            
            self.set_bases(i, props.count_head, 0, False, 0.5) #idx, count, offset, sided, rayon

            for j in range(props.length_head):
                
                if props.count_head == 1 :
                    self.base_x = 0
                    self.base_y = 0
                self.set_parent_and_location(props, j, self.bone_body, self.bone_head, props.length_head, False, z_up=True) #props, idx, parent0, parent1, length, constant_z
                self.set_name(props, i, props.count_head, bone_names[j]) #props, idx0, count, base_name
                self.bone_head = create_bone(self.edit_bones, self.bone_name, self.head, self.tail, self.parent_bone, self.bone_connect)
            
            # ── Creating hairs ─────────────────────────────────────
            # ── Creating names ──        
            
            if props.length_hairs == 1 :
                hair_names = ["Hair"]
            else : 
                hair_names = []
                for x in range(props.length_hairs) :
                    hair_names.append(f"Hair{fmt_index(x)}")
                    
            # ── Creating bones ──        
            for k in range(props.count_hairs):
                
                self.set_bases(k, props.count_hairs, 0, True, 0.5) #idx, count, offset, sided, rayon

                for l in range(props.length_hairs):
                    
                    num_sfx = fmt_index(k) if props.count_hairs > 1 else ""
                    self.set_parent_and_location(props, l, self.bone_head, self.bone_hair, props.length_hairs, True, z_pos=self.bone_head.tail.z) #props, idx, parent0, parent1, length, constant_z
                    self.set_name(props, i, props.count_head, hair_names[l], num_sfx=num_sfx) #props, idx0, count, base_name
                    self.bone_hair = create_bone(self.edit_bones, self.bone_name, self.head, self.tail, self.parent_bone, self.bone_connect)
                    
        
    def create_leg_foot(self, context): # ──────────────────────────────────────────────────────────────────
        """
        Creates legs and feet bone chains
        """
        props = context.scene.spt
        
        # ── Creating legs ─────────────────────────────────────
        # ── Creating names ──
        if props.length_legs == 1:
            bone_names = ["Leg"]
        elif props.length_legs <= 4:
            bone_names = ["Pelvis", "Thigh", "Calf", "Ankle"]
        else :
            bone_names = []
            for i in range(props.length_legs) :
                bone_names.append(f"Leg{fmt_index(i)}")
                
        # ── Creating bones ──        
        for i in range(props.count_legs):
            
            self.set_bases(i, props.count_legs, 0, False, 1.0) #idx, count, offset, sided, rayon

            for j in range(props.length_legs):
                
                self.set_parent_and_location(props, j, self.rig_data.edit_bones[f"{props.skin_prfx}Root"], self.bone_leg, props.length_legs, False, always_co=False, loc_to_parent=False) #props, idx, parent0, parent1, length, constant_z
                self.set_name(props, i, props.count_legs, bone_names[j]) #props, idx0, count, base_name
                self.bone_leg = create_bone(self.edit_bones, self.bone_name, self.head, self.tail, self.parent_bone, self.bone_connect)
                self.bone_leg.align_roll(Vector((0, 0, 1)))
            
            # ── Creating feet ─────────────────────────────────────
            # ── Creating names ──        
            if props.length_foot <= 2:
                foot_names = ["Foot", "Toe"]
            else :
                foot_names = ["Foot"]
                for x in range(props.length_foot-1) :
                    foot_names.append(f"Toe{fmt_index(x)}")
                    
            # ── Creating bones ──        
            for k in range(props.count_foot):
                
                self.set_bases(k, props.count_foot, 0.25, False, 0.5) #idx, count, offset, sided, rayon

                for l in range(props.length_foot):
                    
                    num_sfx = fmt_index(k) if props.count_foot > 1 else ""
                    self.set_parent_and_location(props, l, self.bone_leg, self.bone_foot, props.length_foot, True, z_pos=self.bone_leg.tail.z) #props, idx, parent0, parent1, length, constant_z
                    self.set_name(props, i, props.count_legs, foot_names[l], num_sfx=num_sfx) #props, idx0, count, base_name                        
                    self.bone_foot = create_bone(self.edit_bones, self.bone_name, self.head, self.tail, self.parent_bone, self.bone_connect)
                    
    
    def create_arm_finger(self, context): # ──────────────────────────────────────────────────────────────────
        """
        Creates arms and fingers bone chains
        """
        props = context.scene.spt
        
        # ── Creating arms ─────────────────────────────────────
        # ── Creating names ──
        if props.length_arms == 1:
            bone_names = ["Arm"]
        elif props.length_arms <= 4:
            bone_names = ["Clavicle", "Arm", "Forearm", "Hand"]
        else :
            bone_names = []
            for i in range(props.length_arms-1) :
                bone_names.append(f"Arm{fmt_index(i)}")
            bone_names.append(f"Hand{fmt_index(i)}")
                
        # ── Creating bones ──        
        for i in range(props.count_arms):
            
            self.set_bases(i, props.count_arms, 0, False, 1.0) #idx, count, offset, sided, rayon

            for j in range(props.length_arms):
                
                self.set_parent_and_location(props, j, self.bone_body, self.bone_arm, props.length_arms, False) #props, idx, parent0, parent1, length, constant_z
                self.set_name(props, i, props.count_arms, bone_names[j]) #props, idx0, count, base_name
                self.bone_arm = create_bone(self.edit_bones, self.bone_name, self.head, self.tail, self.parent_bone, self.bone_connect)
                self.bone_arm.align_roll(Vector((0, 0, 1)))
        
            # ── Creating fingers ─────────────────────────────────────
            # ── Creating names ──        
            if props.count_fingers == 1:
                finger_names = ["Finger"]
            elif props.count_fingers <= 5:
                finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
            else :
                finger_names = []
                for x in range(props.count_fingers) :
                    finger_names.append(f"Finger{fmt_index(x)}")
                    
            # ── Creating bones ──        
            for k in range(props.count_fingers):
                
                offset = 0.5 if props.count_arms <= 2 and i == 0 else 1.5 if props.count_arms <= 2 and i == 1 else 0.25
                sided = True if props.count_arms <= 2 else False
                self.set_bases(k, props.count_fingers, offset, sided, 0.2) #idx, count, offset, sided, rayon

                for l in range(props.length_fingers):
                    
                    self.set_parent_and_location(props, l, self.bone_arm, self.bone_finger, props.length_fingers, False) #props, idx, parent0, parent1, length, constant_z
                    self.set_name(props, i, props.count_arms, finger_names[k], num_sfx=fmt_index(l)) #props, idx0, count, base_name
                    self.bone_finger = create_bone(self.edit_bones, self.bone_name, self.head, self.tail, self.parent_bone, self.bone_connect)
                    self.bone_finger.align_roll(Vector((0, 0, 1)))
                    
                    
    def set_bases(self, idx, count, offset, sided, rayon): # ──────────────────────────────────────────────────────────────────
        """
        Sets base locations and rayon of the bone
        
        idx     : current bone chain index
        count   : the total count of this bone chain type to create
        offset  : allows to offset first bone's location on the circle
        sided   : whether to create bones on the back side of the circle only or on the full circle
        rayon   : size of the circle in which bones are located
        """
        
        angle = 2 * math.pi * ((idx / count) - offset) if not sided else math.pi * (idx / (count - 1) - offset ) if count >1 else math.pi/2 - offset
        self.base_x = math.cos(angle) * rayon
        self.base_y = math.sin(angle) * rayon
        self.rayon = rayon
        
    
    def set_parent_and_location(self, props, idx, parent0, parent1, length, constant_z, z_pos=0, always_co=True, z_up=False, loc_to_parent=True): # ──────────────────────────────────────────────────────────────────
        """
        Sets parent and bone tail and head locations based on the bases created earlier
        
        props           : context.scene.spt (properties from panel)
        idx             : current bone idx in bone chain
        parent0         : last bone of the parent bone chain
        parent1         : last bone in current bone chain
        length          : length of the current bone chain
        constant_z      : whether z location is changing during chain or is constant
        z_pos           : used if z is constant, giving z value
        always_co       : allows to not connect first bone of the chain whatever the props value if set to false
        z_up            : defines if z location is increasing or decreasing along chain
        loc_to_parent   : defines if bone location is based on its parent or not
        """
        
        # Specific parent for the first bone, else precedent bone
        self.parent_bone = parent0 if idx == 0 else parent1
        self.bone_connect = props.bone_connected if always_co or idx>0 else False
        
        # Setting Z location, incrementing with chain depth
        base_z = parent0.tail.z if loc_to_parent else 0
        off_head = (idx / length * self.rayon)
        off_tail = ((idx + 1) / length * self.rayon)
        z_head = z_pos if constant_z else base_z - off_head if not z_up else base_z + off_head
        z_tail = z_pos if constant_z else base_z - off_tail if not z_up else base_z + off_tail

        # Length of a chain's segment
        segment = 1.0 / length

        # Each bone goes for idx*segment in the given direction
        parent_x = parent0.tail.x if loc_to_parent else 0
        parent_y = parent0.tail.y if loc_to_parent else 0
        self.head = Vector((parent_x + self.base_x * idx * segment, parent_y + self.base_y * idx * segment, z_head))
        self.tail = Vector((parent_x + self.base_x * (idx + 1) * segment, parent_y + self.base_y * (idx + 1) * segment, z_tail))
    
    
    def set_name(self, props, idx, count, base_name, num_sfx=""): # ──────────────────────────────────────────────────────────────────
        """
        Sets bone name to given name with adapted prefix and suffix
        
        props       : context.scene.spt (properties from panel)
        idx         : parent bone chain's index
        count       : parent bone chain's total count
        base_name   : bone's name without prefix/suffix
        num_sfx     : used to add a numeral suffix for bones with numerable parents in a bone chain
        """
    
        if count == 2:
            suffix = ".l" if idx == 0 else ".r"
            self.bone_name = f"{props.skin_prfx}{base_name}{num_sfx}{suffix}"
        else:
            suffix = fmt_index(idx) if count > 1 else ""
            self.bone_name = f"{props.skin_prfx}{base_name}{num_sfx}{suffix}"
    
    
    def create_collection(self, context): # ──────────────────────────────────────────────────────────────────
        """
        Creates a collection named after the skin bones prefix and stores every bones in it
        """
        
        props = context.scene.spt
        
        skin_collection = self.rig_data.collections.get(props.skin_prfx[:-1]) or self.rig_data.collections.get("Bones")
        if skin_collection :
            skin_collection.name = props.skin_prfx[:-1]
        else:
            skin_collection = self.rig_data.collections.new(props.skin_prfx[:-1])
        roots_collection = self.rig_data.collections.new("ROOTS")
        
        bpy.ops.object.mode_set(mode="OBJECT")
        for bone in self.rig_data.bones :
            if "Root" in bone.name or "Trajectory" in bone.name or "Position" in bone.name :
                roots_collection.assign(bone)
            else :
                skin_collection.assign(bone)
    
    def clean_rig(self): # ──────────────────────────────────────────────────────────────────
        """
        Cleans the created rig by setting rotation mode and placing it on the ground
        """
        # ── Going to Pose Mode to set rotations
        bpy.ops.object.mode_set(mode="POSE")
        for bone in self.rig_obj.pose.bones :
            bone.rotation_mode = 'XYZ'
        
        # ── Going back to Object Mode to fix location
        bpy.ops.object.mode_set(mode="OBJECT")
        if bpy.context.scene.tool_settings.use_keyframe_insert_auto == True :
            bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
            bpy.ops.transform.translate(value=(0,0,1))
            bpy.context.scene.tool_settings.use_keyframe_insert_auto = True
        else :
            bpy.ops.transform.translate(value=(0,0,1))
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# ──────────────────────────────────────────────────────────────────────────────────────────   
class SPT_OT_create_control_rig(bpy.types.Operator):
    """
    Creates a control rig for the selected rig
    """
    bl_idname = "spt.create_control_rig"
    bl_label  = "Create Control Rig"
    bl_description = "Creates a control rig within your current armature, duplicating every skinned bone to attach a controller to it"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type == 'ARMATURE')
    
    def execute(self, context): # ──────────────────────────────────────────────────────────────────
        base_mode = context.object.mode
        active_obj = context.active_object
        
        # Defining self variables and preparing parsing/collections
        self.control_bones_created = []
        self.parent_limits = ["Body","Root","Spine"]
        self.parse_rig(context)
        self.create_collections(context)
        
        # Creating control rig
        self.create_control_rig(context)
        
        # Cleaning viewport
        self.mecha_collection.is_visible = False
        bpy.ops.object.mode_set(mode=base_mode)  
        self.report({"INFO"}, f"Control rig successflly added to {active_obj.name}")
        return {'FINISHED'}
    
    def create_control_rig(self, context) : # ──────────────────────────────────────────────────────────────────
        props = context.scene.spt
        i=0

        # ── Creating bodies ─────────────────────────────────────
        for bone_name in self.bones["bodies"] :
            self.create_all(context, bone_name, "", i, self.control_collection, False)
            i+=1
        
        # ── Creating legs ─────────────────────────────────────
        if props.leg_ik and props.leg_fk :
            if len(self.bones["leg_r"]) > 0 :
                # ── Leg r ──
                self.prop_name = "ik_fk_leg_r"
                self.create_property(context, self.prop_name, 1)
                for bone_name in self.bones["leg_r"] :
                    self.create_all(context, bone_name, "FK", i, self.leg_fk_r_collection, True)
                    i+=1
                bones = [bone for bone in self.bones["leg_r"] if "Foot" in bone]
                for bone_name in bones :
                    self.create_all(context, bone_name, "IK", i, self.leg_ik_r_collection, True)
                    i+=1
                # ── Leg l ──
                self.prop_name = "ik_fk_leg_l"
                self.create_property(context, self.prop_name, 1)
                for bone_name in self.bones["leg_l"] :
                    self.create_all(context, bone_name, "FK", i, self.leg_fk_l_collection, True)
                    i+=1
                bones = [bone for bone in self.bones["leg_l"] if "Foot" in bone]
                for bone_name in bones :
                    self.create_all(context, bone_name, "IK", i, self.leg_ik_l_collection, True)
                    i+=1
            else :
                # ── Leg any ──
                self.prop_name = "ik_fk_legs"
                self.create_property(context, self.prop_name, 1)
                for bone_name in self.bones["legs"] :
                    self.create_all(context, bone_name, "FK", i, self.legs_fk_collection, True)
                    i+=1
                bones = [bone for bone in self.bones["legs"] if "Foot" in bone]
                for bone_name in bones :
                    self.create_all(context, bone_name, "IK", i, self.legs_ik_collection, True)
                    i+=1
        # ── No switch ──
        elif props.leg_ik :
            bones = [bone for bone in self.bones["legs"] if "Foot" in bone]
            for bone_name in bones :
                self.create_all(context, bone_name, "IK", i, self.legs_collection, False)
                i+=1
        elif props.leg_fk :
            for bone_name in self.bones["legs"] :
                self.create_all(context, bone_name, "FK", i, self.legs_collection, False)
                i+=1
        
        # ── Creating arms ─────────────────────────────────────      
        if props.arm_ik and props.arm_fk :
            if len(self.bones["arm_r"]) > 0 :
                # ── Arm r ──
                self.prop_name = "ik_fk_arm_r"
                self.create_property(context, self.prop_name, 0)
                for bone_name in self.bones["arm_r"] :
                    self.create_all(context, bone_name, "FK", i, self.arm_fk_r_collection, True)
                    i+=1
                bones = [bone for bone in self.bones["arm_r"] if "Hand" in bone]
                for bone_name in bones :
                    self.create_all(context, bone_name, "IK", i, self.arm_ik_r_collection, True)
                    i+=1
                # ── Arm l ──
                self.prop_name = "ik_fk_arm_l"
                self.create_property(context, self.prop_name, 0)
                for bone_name in self.bones["arm_l"] :
                    self.create_all(context, bone_name, "FK", i, self.arm_fk_l_collection, True)
                    i+=1
                bones = [bone for bone in self.bones["arm_l"] if "Hand" in bone]
                for bone_name in bones :
                    self.create_all(context, bone_name, "IK", i, self.arm_ik_l_collection, True)
                    i+=1
            else :
                # ── Arm any ──
                self.prop_name = "ik_fk_arms"
                self.create_property(context, self.prop_name, 0)
                for bone_name in self.bones["arms"] :
                    self.create_all(context, bone_name, "FK", i, self.arms_fk_collection, True)
                    i+=1
                bones = [bone for bone in self.bones["arms"] if "Hand" in bone]
                for bone_name in bones :
                    self.create_all(context, bone_name, "IK", i, self.arms_ik_collection, True)
                    i+=1
        # ── No switch ──
        elif props.arm_ik :
            bones = [bone for bone in self.bones["arms"] if "Hand" in bone]
            for bone_name in bones :
                self.create_all(context, bone_name, "IK", i, self.arms_collection, False)
                i+=1
        elif props.arm_fk :
            for bone_name in self.bones["arms"] :
                self.create_all(context, bone_name, "FK", i, self.arms_collection, False)
                i+=1
        
        # ── Creating fingers ───────────────────────────────────── 
        for bone_name in self.bones["fingers"] :
            self.create_control_bone(context, bone_name, "Finger")
            self.add_to_collection(context, self.control_bones_created[i], self.control_collection)
            self.create_constraint(context, bone_name, self.control_bones_created[i], "Finger")
            self.create_controller(context, "Circle90", self.control_bones_created[i])
            if self.finger_length > 1 and "_00" in bone_name :
                self.create_controller(context, "Paddle", self.scale_bone_name)
            i+=1

    def create_all(self, context, bone_name, type, idx, collection, switch): # ──────────────────────────────────────────────────────────────────
        """
        Creates an fk controller on given bone using the other class functions
        
        bone_name   : name of the skinned bone for which a controller is created
        type        : type of control applied from the controller to the skin bone
        idx         : index of the currently created bone
        collection  : collection in which the controller is placed
        switch      : boolean informing whether there should be an IK / FK switch on the created controller
        """
        
        props = context.scene.spt
        active_obj = context.active_object
        active_rig = active_obj.data
        
        # Preparing all needed names
        prfx, base, count_sfx, side_sfx = parse_string(bone_name)
        count_sfx = f"_{count_sfx}" if count_sfx != "" else ""
        self.pole_name = f"{props.control_prfx}IK_Pole_{active_obj.pose.bones[bone_name].parent.name[len(props.skin_prfx):]}"
        if "Foot" in bone_name :
            self.end_name = f"{props.mecha_prfx}IK_Roll_End{count_sfx}{side_sfx}"
            self.ik_target_name = f"{props.mecha_prfx}IK_Target{count_sfx}{side_sfx}"
            self.roll_name = f"{props.control_prfx}IK_Roll{count_sfx}{side_sfx}"
            if len(active_rig.bones.get(bone_name).children_recursive) > 1 :
                self.tip_name = []
                self.mid_name = []
                for i in range (len(active_rig.bones.get(bone_name).children_recursive)) :
                    self.tip_name.append(f"{props.mecha_prfx}IK_Roll_Tip{count_sfx}{fmt_index(i)}{side_sfx}")
                    self.mid_name.append(f"{props.mecha_prfx}IK_Roll_Middle{count_sfx}{fmt_index(i)}{side_sfx}")
            else :
                self.tip_name = [f"{props.mecha_prfx}IK_Roll_Tip{count_sfx}{side_sfx}"]
                self.mid_name = [f"{props.mecha_prfx}IK_Roll_Middle{count_sfx}{side_sfx}"]
        
        
        # Creating bone and adding it to corresponding collection
        self.create_control_bone(context, bone_name, type)
        self.add_to_collection(context, self.control_bones_created[idx], collection)
        if type =="IK":
            self.create_controller(context, "Cube", self.pole_name)
            self.add_to_collection(context, self.pole_name, collection)
            if "Foot" in bone_name :
                bone = active_rig.bones.get(bone_name)
                if len(bone.children_recursive) > 0 :
                    self.create_controller(context, "Turn", self.roll_name)
                    self.add_to_collection(context, self.roll_name, collection)
                    self.add_to_collection(context, self.end_name, self.mecha_collection)
                    for i in range (len(bone.children_recursive)) :
                        self.add_to_collection(context, self.tip_name[i], self.mecha_collection)
                        self.add_to_collection(context, self.mid_name[i], self.mecha_collection)
                self.add_to_collection(context, self.ik_target_name, self.mecha_collection)
        
        # Creating constraints and control shape
        self.create_constraint(context, bone_name, self.control_bones_created[idx], type)
        shape = "Cube" if type == "IK" else "Circle90" 
        self.create_controller(context, shape, self.control_bones_created[idx])
        
        # Adding drivers to constraints if there is a switch
        if switch :
            inverse = False if type == "IK" else True
            path = f'pose.bones["{bone_name}"].constraints["Copy Transforms {type}"].influence'
            self.add_driver(active_obj, path, active_obj, self.prop_name, inverse=inverse)
            if type == "IK" :
                path = f'pose.bones["{bone_name}"].parent.constraints["IK"].influence'
                self.add_driver(active_obj, path, active_obj, self.prop_name)
                bone = active_obj.pose.bones[bone_name]
                if "Foot" in bone_name and len(bone.children_recursive) > 0:
                    for child in bone.children_recursive:
                        target_bone = child
                        path = f'pose.bones["{target_bone.name}"].constraints["Copy Transforms {type}"].influence'
                        self.add_driver(active_obj, path, active_obj, self.prop_name)
            path = f'collections_all["{collection.name}"].is_visible'
            self.add_driver(active_rig, path, active_obj, self.prop_name, inverse=inverse)
            
    def create_collections(self, context): # ──────────────────────────────────────────────────────────────────
        """ 
        Creates collections adapted to current rig
        """
        
        props = context.scene.spt
        active_obj = context.active_object
        active_rig = active_obj.data
        
        self.control_collection = active_rig.collections.get(f"{props.control_prfx[:-1]}")
        if not self.control_collection :
            self.control_collection = active_rig.collections.new(f"{props.control_prfx[:-1]}")
        self.mecha_collection = active_rig.collections.get(f"{props.mecha_prfx[:-1]}")
        if not self.mecha_collection :
            self.mecha_collection = active_rig.collections.new(f"{props.mecha_prfx[:-1]}")
        
        if props.leg_ik and props.leg_fk:
            if len(self.bones["leg_r"]) > 0 :
                self.leg_ik_l_collection = active_rig.collections.new(f"{props.control_prfx}LEG_IK_L")
                self.leg_ik_r_collection = active_rig.collections.new(f"{props.control_prfx}LEG_IK_R")
                self.leg_fk_l_collection = active_rig.collections.new(f"{props.control_prfx}LEG_FK_L")
                self.leg_fk_r_collection = active_rig.collections.new(f"{props.control_prfx}LEG_FK_R")
            else :
                self.legs_ik_collection = active_rig.collections.new(f"{props.control_prfx}LEGS_IK")
                self.legs_fk_collection = active_rig.collections.new(f"{props.control_prfx}LEGS_FK")
        elif props.leg_ik or props.leg_fk :
            self.legs_collection = active_rig.collections.new(f"{props.control_prfx}LEGS")
        if props.arm_ik and props.arm_fk :
            if len(self.bones["arm_r"]) > 0 :
                self.arm_ik_l_collection = active_rig.collections.new(f"{props.control_prfx}ARM_IK_L")
                self.arm_ik_r_collection = active_rig.collections.new(f"{props.control_prfx}ARM_IK_R")
                self.arm_fk_l_collection = active_rig.collections.new(f"{props.control_prfx}ARM_FK_L")
                self.arm_fk_r_collection = active_rig.collections.new(f"{props.control_prfx}ARM_FK_R")
            else :
                self.arms_ik_collection = active_rig.collections.new(f"{props.control_prfx}ARMS_IK")
                self.arms_fk_collection = active_rig.collections.new(f"{props.control_prfx}ARMS_FK")
        elif props.arm_ik or props.arm_fk :
            self.arms_collection = active_rig.collections.new(f"{props.control_prfx}ARMS")
    
    def create_control_bone(self, context, bone_name, type): # ──────────────────────────────────────────────────────────────────
        """
        Creates a new bone on given bone's location
        """
        
        props = context.scene.spt
        active_obj = context.active_object
        active_rig = active_obj.data
        
        # Checking for type and if given bone is a skinned bone
        type_name = "IK" if type == "IK" else "FK"
        bpy.ops.object.mode_set(mode="EDIT")
        if bone_name.startswith(props.skin_prfx) :
            if not type == "IK" :
                # If not IK : a unique control bone is created and/or referenced as a created control bone
                control_bone = active_rig.edit_bones.get(f"{props.control_prfx}{type_name}_{bone_name[len(props.skin_prfx):]}")
                bone = active_rig.edit_bones.get(bone_name)
                if not control_bone :
                    control_bone = active_rig.edit_bones.new(f"{props.control_prfx}{type_name}_{bone_name[len(props.skin_prfx):]}")
                    control_bone.head        = bone.head.copy()
                    control_bone.tail        = bone.tail.copy()
                    control_bone.roll        = bone.roll
                    parent_bone = active_rig.edit_bones.get(f"{props.control_prfx}{type_name}_{bone.parent.name[len(props.skin_prfx):]}") or active_rig.edit_bones.get(f"{props.skin_prfx}Root")
                    control_bone.parent      = parent_bone
                    control_bone.use_deform  = False
                self.control_bones_created.append(control_bone.name)
            else :
                # If IK : checking for ik chain's length by looping through bone's parents until a limit is reached
                bone = active_rig.edit_bones.get(bone_name)
                parent = active_rig.edit_bones.get(bone_name).parent
                while parent :
                    for limit in self.parent_limits :
                        if not limit in parent.parent.name:
                            tmp_parent = parent.parent
                        else :
                            tmp_parent = None
                            break
                    target_bone = parent
                    parent = tmp_parent
                # Creating pole target if unique by taking the center point between first and last bone of the chain
                pole_bone = active_rig.edit_bones.get(self.pole_name)
                if not pole_bone :
                    pole_bone = active_rig.edit_bones.new(self.pole_name)
                    vec0 = Vector((0,0.5,0)) if "Foot" in bone_name else Vector((0,-0.5,0))
                    vec1 = Vector((0,0.6,0)) if "Foot" in bone_name else Vector((0,-0.6,0))
                    pole_bone.head = (target_bone.head.copy()/2) + (bone.head.copy()/2) - vec0
                    pole_bone.tail = (target_bone.head.copy()/2) + (bone.head.copy()/2) - vec1
                    pole_bone.parent = active_rig.edit_bones.get(f"{props.skin_prfx}Root")
                    pole_bone.use_deform = False
                # Creating the control bone if unique the same way as for non-IK
                control_bone = active_rig.edit_bones.get(f"{props.control_prfx}IK_{bone_name[len(props.skin_prfx):]}")
                if not control_bone :
                    control_bone = active_rig.edit_bones.new(f"{props.control_prfx}IK_{bone_name[len(props.skin_prfx):]}")
                    control_bone.head        = bone.head.copy()
                    control_bone.tail        = bone.tail.copy()
                    control_bone.parent      = active_rig.edit_bones.get(f"{props.skin_prfx}Root")
                    control_bone.use_deform  = False
                self.control_bones_created.append(control_bone.name)
                # Checking if ik chain is created for a leg, getting the last bone of the chain if that's the case
                if "Foot" in bone_name :
                    end_bone = None
                    chain_length = len(bone.children_recursive)
                    if chain_length > 0 :
                        used_children = []
                        for i in range (len(bone.children_recursive)):
                            #Getting last bone of the chain that hasn't been used yet to construct bone chain from last bone to closest to end bone
                            for child in bone.children_recursive:
                                if child not in used_children :
                                    target_bone = child
                            used_children.append(target_bone)
                            # Creating tip bone used for roll, an inversed version of the toe
                            new_tip_bone = active_rig.edit_bones.get(self.tip_name[chain_length-(i+1)])
                            if not new_tip_bone :
                                new_tip_bone = active_rig.edit_bones.new(self.tip_name[chain_length-(i+1)])
                                new_tip_bone.head = target_bone.tail.copy()
                                new_tip_bone.tail = target_bone.head.copy()
                                new_tip_bone.parent = control_bone if i == 0 else tip_bone
                                new_tip_bone.use_deform = False
                            tip_bone = new_tip_bone
                            # Creating middle bone used for roll, replicating toe's location
                            mid_bone = active_rig.edit_bones.get(self.mid_name[chain_length-(i+1)])
                            if not mid_bone :
                                mid_bone = active_rig.edit_bones.new(self.mid_name[chain_length-(i+1)])
                                mid_bone.head = target_bone.head.copy()
                                mid_bone.tail = target_bone.tail.copy()
                                mid_bone.parent = tip_bone
                                mid_bone.use_deform = False
                        # Creating end bone used for roll, an inversed version of the foot
                        end_bone = active_rig.edit_bones.get(self.end_name)
                        if not end_bone :
                            end_bone = active_rig.edit_bones.new(self.end_name)
                            end_bone.head = bone.tail.copy()
                            end_bone.tail = bone.head.copy()
                            end_bone.parent = mid_bone
                            end_bone.use_deform = False
                        # Creating the roll bone controling the foot roll
                        roll_bone = active_rig.edit_bones.get(self.roll_name)
                        if not roll_bone :
                            roll_bone = active_rig.edit_bones.new(self.roll_name)
                            roll_bone.head        = bone.head.copy() + Vector((0, 0.3, 0))
                            roll_bone.tail        = bone.head.copy() + Vector((0, 0.3, 0.2))
                            roll_bone.parent      = control_bone
                            roll_bone.use_deform  = False
                    # Creating ik_target bone used as a target for the ik constraint
                    ik_target_bone = active_rig.edit_bones.get(self.ik_target_name)
                    if not ik_target_bone :
                        ik_target_bone = active_rig.edit_bones.new(self.ik_target_name)
                        ik_target_bone.head        = bone.head.copy()
                        ik_target_bone.tail        = bone.tail.copy()
                        ik_target_bone.parent      = end_bone if end_bone != None else control_bone
                        ik_target_bone.use_deform  = False
            
            # Creating a scale bone for the first bone of a finger chain
            if type == "Finger" and "_00" in bone_name and self.finger_length > 1 :
                prfx, base, count_sfx, side_sfx = parse_string(bone_name)
                verif_base = base[:-1]
                if verif_base[-2:].isdigit() :
                    count_sfx = f"_{count_sfx}"
                    base = base[:-3]
                else :
                    count_sfx = ""
                target_bone = active_rig.edit_bones.get(f"{prfx}{base}0{self.finger_length}{count_sfx}{side_sfx}")
                self.scale_bone_name = f"{props.control_prfx}Scale_{base[:-1]}{count_sfx}{side_sfx}"
                scale_bone = active_rig.edit_bones.get(self.scale_bone_name)
                if not scale_bone :
                    scale_bone = active_rig.edit_bones.new(self.scale_bone_name)
                    scale_bone.head = bone.head.copy()
                    scale_bone.tail = target_bone.tail.copy()
                    scale_bone.roll = bone.roll
                    scale_bone.parent = control_bone
                    scale_bone.use_deform = False
                         
    def add_to_collection(self, context, bone_name, collection): # ──────────────────────────────────────────────────────────────────
        """
        Adds named bone to given collection
        """
        
        active_obj = context.active_object
        active_rig = active_obj.data
        
        bpy.ops.object.mode_set(mode="OBJECT")
        bone = active_rig.bones.get(bone_name)
        for col in active_rig.collections_all:
            col.unassign(bone)
        collection.assign(bone)
    
    def create_constraint(self, context, bone_name, control_name, type): # ──────────────────────────────────────────────────────────────────
        """
        Creates a constraint on bone targeting control_bone based on the type
        """
        
        active_obj = context.active_object
        active_rig = active_obj.data
        
        # Getting pose mode bones
        bpy.ops.object.mode_set(mode="POSE")
        pose_bone    = active_obj.pose.bones[bone_name]
        control_bone = active_obj.pose.bones[control_name]
        
        # Checking type to define what constraints to apply
        if type == "IK" :
            # Creating copy transform IK constraint
            target_bone_name = self.ik_target_name if "Foot" in bone_name else control_name
            constraint          = pose_bone.constraints.new("COPY_TRANSFORMS")
            constraint.target   = active_obj        # object
            constraint.subtarget= target_bone_name   # string
            constraint.name     = f"Copy Transforms IK"
            # Creating IK constraint by checking chain's length
            parent = pose_bone.parent
            constraint = parent.constraints.new("IK")
            constraint.target    = active_obj
            constraint.subtarget = target_bone_name
            chain = 0
            while parent :
                for limit in self.parent_limits :
                    if not limit in parent.parent.name:
                        tmp_parent = parent.parent
                    else :
                        tmp_parent = None
                        break
                parent = tmp_parent
                chain +=1
            constraint.chain_count = chain
            constraint.name = "IK"
            constraint.pole_target = active_obj
            constraint.pole_subtarget = self.pole_name
            # Checking if the given bone is a foot, getting end of the chain if true
            if "Foot" in bone_name and len(pose_bone.children_recursive) > 0:
                rot_angle = 1.5708 / (len(pose_bone.children_recursive)+1)

                for i, child in enumerate(pose_bone.children_recursive):
                    target_bone = child
                    # Creating copy transform IK between toe and mid bone
                    constraint = target_bone.constraints.new("COPY_TRANSFORMS")
                    constraint.target    = active_obj
                    constraint.subtarget = self.mid_name[i]
                    constraint.name     = f"Copy Transforms IK"
                
                    # Creating transform constraint between tip bone and roll bone
                    tip_bone = active_obj.pose.bones[self.tip_name[i]]
                    constraint = tip_bone.constraints.new("TRANSFORM")
                    constraint.target    = active_obj
                    constraint.subtarget = self.roll_name
                    constraint.name = "Transform roll"
                    constraint.target_space = 'LOCAL'
                    constraint.owner_space = 'LOCAL'
                    constraint.map_from = 'ROTATION'
                    constraint.from_min_x_rot = rot_angle*(i+1) # radians 
                    constraint.from_max_x_rot = rot_angle*(i+2)
                    constraint.map_to = 'ROTATION'
                    constraint.map_to_z_from = 'X'
                    constraint.to_min_x_rot = 0
                    constraint.to_max_x_rot = rot_angle
                
                # Creating transform constraint between end bone and roll bone
                end_bone = active_obj.pose.bones[self.end_name]
                constraint = end_bone.constraints.new("TRANSFORM")
                constraint.target    = active_obj
                constraint.subtarget = self.roll_name
                constraint.name = "Transform roll"
                constraint.target_space = 'LOCAL'
                constraint.owner_space = 'LOCAL'
                constraint.map_from = 'ROTATION'
                constraint.from_min_x_rot = 0
                constraint.from_max_x_rot = rot_angle
                constraint.map_to = 'ROTATION'
                constraint.map_to_z_from = 'X'
                constraint.to_min_x_rot = 0
                constraint.to_max_x_rot = rot_angle
                
        else : 
            # For non-IK, creating copy transform FK constraint
            constraint          = pose_bone.constraints.new("COPY_TRANSFORMS")
            constraint.target   = active_obj
            constraint.subtarget= control_bone.name
            constraint.name     = f"Copy Transforms FK"
        
        # Creating a constraint between first controller of each finger chain and hand's skinned bone so it keeps following whatever the IK/FK state
        if type == "Finger" :
            prfx, base, count_sfx, side_sfx = parse_string(bone_name)
            verif_base = base[:-1]
            if verif_base[-2:].isdigit() :
                bone_name = f"{prfx}{base}{side_sfx}"
            if "_00" in bone_name :
                constraint = control_bone.constraints.new("COPY_LOCATION")
                constraint.target    = active_obj
                constraint.subtarget = pose_bone.parent.name
                constraint.head_tail = 1.0
                constraint.name = "Copy Loc"
            elif self.finger_length > 1 :
                # Creating transform constraint on other finger controllers to follow finger scale
                constraint = control_bone.constraints.new("TRANSFORM")
                constraint.target    = active_obj
                constraint.subtarget = self.scale_bone_name 
                constraint.name = "Transform scale"
                constraint.target_space = 'LOCAL'
                constraint.owner_space = 'LOCAL'
                constraint.map_from = 'SCALE'
                constraint.from_min_y_scale = 0.5
                constraint.from_max_y_scale = 1.5
                constraint.map_to = 'ROTATION'
                constraint.map_to_x_from = 'Y'
                constraint.to_min_x_rot = 1.0472
                constraint.to_max_x_rot = -1.0472
            
    def create_controller(self, context, ctl_shape, bone_name): # ──────────────────────────────────────────────────────────────────
        """
        Creates a controller shape based on the given shape and bone name
        """
        
        props = context.scene.spt
        active_obj = context.active_object
        
        # Creating controller shape using external function
        bpy.ops.object.mode_set(mode="OBJECT")
        shape = create_controller(context, ctl_shape, f"{active_obj.name}_{bone_name}") 

        # Applying shape, rotation mode and color to control bone
        bpy.ops.object.mode_set(mode="POSE")
        bone = active_obj.pose.bones[bone_name]
        color = props.bone_color_r if bone_name[-2:] == ".r" else props.bone_color_l if bone_name[-2:] == ".l" else props.bone_color
        context.view_layer.objects.active = bone.id_data
        bone.color.palette = "CUSTOM" 
        bone.color.custom.normal = color
        bone.color.custom.select = color *1.25
        bone.color.custom.active = color *1.5
        bone.rotation_mode = 'XYZ'
        bone.custom_shape = shape
        
    def create_property(self, context, name, value): # ──────────────────────────────────────────────────────────────────
        """
        Creates a property for ik/fk handling
        
        name  : name of the property
        value : default value of the property
        """
        
        active_obj = context.active_object
        active_obj[name] =  value
        ui = active_obj.id_properties_ui(name)
        ui.update(
            min=0,
            max=1,
            default=value,
            description="",
            step=1,
        )
    
    def add_driver(self, target_obj, target_path, source_obj, source_path, index=-1, inverse=False): # ──────────────────────────────────────────────────────────────────
        """
        Adds a driver on target_obj.target_path reading source_obj[source_path]
        
        target_obj   : object which is driven
        target_path  : data_path of the driven property
        source_obj   : objct containing the property
        source_path  : property's path
        index        : -1 for scalar, 0/1/2 for X/Y/Z of a vector
        """
        # Creating driver on the given target
        fcurve = target_obj.driver_add(target_path, index)
        driver = fcurve.driver
        
        # Defining driver type and expression
        driver.type = "SCRIPTED"
        driver.expression = "ik_fk" if not inverse else "1-ik_fk" # var name
        
        # Defining the variable
        var = driver.variables.new()
        var.name = "ik_fk"
        var.type = "SINGLE_PROP" 
        
        target = var.targets[0]
        target.id = source_obj   # prop owner
        target.data_path = f'["{source_path}"]' # prop's path
    
    def parse_rig(self, context): # ──────────────────────────────────────────────────────────────────
        """
        Parses active rig to get bone types to clarify workflow 
        """
        
        props = context.scene.spt
        active_obj = context.active_object
        active_rig = active_obj.data
        
        # Defining names to search for
        root_names = ["Position", "Trajectory", "Root"]
        leg_names = ["Pelvis", "Thigh", "Calf", "Ankle", "Leg", "Foot", "Toe"]
        arm_names = ["Clavicle", "Arm", "Forearm", "Hand"]
        finger_names = ["Thumb","Index","Middle","Ring","Pinky","Finger"]
        
        # Defining dictionnary with the categories needed
        self.finger_length = 0
        self.bones={
            "roots":[],
            "legs":[],
            "leg_l":[],
            "leg_r":[],
            "arms":[],
            "arm_l":[],
            "arm_r":[],
            "fingers":[],
            "bodies":[],
            "fk":[],
            "ik":[],
            "ctl":[],
            "mch":[],
        }
        
        # Looping through rig searching for names and sorting them in the dictionnary
        past_base = None
        for bone in active_rig.bones :
            skip = False
            if props.control_prfx in bone.name :
                self.bones["ctl"].append(bone.name)
                break
            if props.mecha_prfx in bone.name :
                self.bones["mch"].append(bone.name)
                break
            for root in root_names :
                if root in bone.name :
                    self.bones["roots"].append(bone.name)
                    skip = True
                    break
            for leg in leg_names :
                if leg in bone.name :
                    self.bones["legs"].append(bone.name)
                    skip = True
                    if bone.name.endswith(".l") :
                        self.bones["leg_l"].append(bone.name)
                    elif bone.name.endswith(".r") :
                        self.bones["leg_r"].append(bone.name)
                    break
            for arm in arm_names :
                if arm in bone.name :
                    self.bones["arms"].append(bone.name)
                    skip = True
                    if bone.name.endswith(".l") :
                        self.bones["arm_l"].append(bone.name)
                    elif bone.name.endswith(".r") :
                        self.bones["arm_r"].append(bone.name)
                    break
            for fin in finger_names :
                if fin in bone.name :
                    self.bones["fingers"].append(bone.name)
                    prfx, base, count_sfx, side_sfx = parse_string(bone.name)
                    base = base[:-1]
                    base = base[:-3] if base[-2:].isdigit() else base
                    self.finger_length = self.finger_length + 1 if base == past_base else 0
                    past_base = base
                    skip = True
                    break
            if not skip : # Skipped if bone already is an identified body part
                self.bones["bodies"].append(bone.name) 
            if "FK" in bone.name :
                self.bones["fk"].append(bone.name)
            if "IK" in bone.name :
                self.bones["ik"].append(bone.name)
    
# ──────────────────────────────────────────────────────────────────────────────────────────   
class SPT_OT_create_fk_control(SPT_OT_base_bone_action):
    """
    Creates a fk controller for the selected bones by calling a function
    """
    bl_idname = "spt.create_fk_control"
    bl_label  = "Create FK Control"
    bl_description = "Creates a fk controller for the selected bones"
    
    def execute(self, context):
        base_mode = context.object.mode
        bpy.ops.object.mode_set(mode="EDIT")
        selected_bones = context.selected_editable_bones
        
        create_fk_controller(context, selected_bones)
            
        bpy.ops.object.mode_set(mode=base_mode)  
        self.report({"INFO"}, f"FK controller added for selected bones")
        return {'FINISHED'}
    
# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_edit_widget(bpy.types.Operator):
    """
    Edits the widget for selected bone // Developped by Manuel Rais and Christophe Seux (bone widget addon) //
    """
    bl_idname = "spt.edit_widget"
    bl_label = "Edit"
    bl_description = "Allows you to edit current bone's widget"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        props = context.scene.spt
        if props.edit_widget_active :
            return (context.object and context.object.type == 'MESH'
                and context.object.mode in ['EDIT', 'OBJECT'])
        else :
            active_bone = context.active_pose_bone
            shape = None
            if active_bone :
                shape = active_bone.custom_shape
            return (context.object and context.object.type == 'ARMATURE' and context.object.mode == 'POSE' and shape)

    def execute(self, context):
        props = context.scene.spt
        active_bone = context.active_pose_bone
        
        # Checking for bone related to the selected object
        if props.edit_widget_active :
            if not from_widget_find_bone(context, context.object):
                self.report({'INFO'}, 'Object is not a bone widget')
                return {'FINISHED'}

            D = bpy.data
            widget: 'Object' = context.object
            bone: 'PoseBone' = from_widget_find_bone(context, widget)
            armature: 'Armature' = bone.id_data
            props.edit_widget_active = False

            if context.active_object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.select_all(action='DESELECT')

            collection = get_view_layer_collection(context, widget)
            collection.hide_viewport = True
            if context.space_data.local_view:
                bpy.ops.view3d.localview()
            context.view_layer.objects.active = armature
            armature.select_set(True)
            bpy.ops.object.mode_set(mode='POSE')
            armature.data.bones.active = armature.data.bones[bone.name]
            return {'FINISHED'}
        else :
            try:
                D = bpy.data
                widget: 'Object' = active_bone.custom_shape
                props.edit_widget_active = True

                armature = active_bone.id_data
                bpy.ops.object.mode_set(mode='OBJECT')
                context.active_object.select_set(False)

                collection: 'LayerCollection' = get_view_layer_collection(
                    context, widget)
                collection.hide_viewport = False

                if context.space_data.local_view:
                    bpy.ops.view3d.localview()

                # select object and make it active
                widget.select_set(True)
                context.view_layer.objects.active = widget
                bpy.ops.object.mode_set(mode='EDIT')
            except KeyError:
                self.report(
                    {'INFO'}, 'This widget is not in the Widget Collection')
            return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_create_widget(bpy.types.Operator):
    """
    Creating a widget from a list's selection using create_controller function
    """
    bl_idname = "spt.create_widget"
    bl_label  = "Create Widget"
    bl_description = "Creates selected widget shape for selected bone"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        if context.object :
            active_bone = context.active_pose_bone if context.object.mode == 'POSE' else context.active_bone
        return (context.object and context.object.type == 'ARMATURE'
            and context.object.mode == 'POSE' and active_bone)
                
    def execute(self, context):
        props = context.scene.spt
        active_bone = context.active_pose_bone
        
        # ── Creating shape in Object Mode ──
        bpy.ops.object.mode_set(mode="OBJECT")
        shape = create_controller(context, props.widget_shape, f"{context.object.name}_{active_bone.name}")

        # ── Assign color and shape in Pose Mode ──
        context.view_layer.objects.active = active_bone.id_data
        bpy.ops.object.mode_set(mode="POSE")
        active_bone = context.active_pose_bone
        name = active_bone.name
        color = props.bone_color_r if name[-2:] == ".r" else props.bone_color_l if name[-2:] == ".l" else props.bone_color
        active_bone.color.palette = "CUSTOM" 
        active_bone.color.custom.normal = color
        active_bone.color.custom.select = color *1.25
        active_bone.color.custom.active = color *1.5
        active_bone.custom_shape = shape  

        self.report({"INFO"}, "Controller shape successfully created")
        return {"FINISHED"}

# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_delete_widget(bpy.types.Operator):
    """
    Deleting active bone's widget
    """
    bl_idname = "spt.delete_widget"
    bl_label  = "Delete Widget"
    bl_description = "Deletes active bone's widget"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        active_bone = context.active_pose_bone
        shape = None
        if active_bone :
            shape = active_bone.custom_shape 
        return (context.object and context.object.type == 'ARMATURE'
            and context.object.mode in ['POSE'] and shape)
            
    def execute(self, context):
        active_bone = context.active_pose_bone
        shape = active_bone.custom_shape
        if shape :
            active_bone.custom_shape = None
            bpy.data.objects.remove(shape, do_unlink=True)
        
        self.report({"INFO"}, "Controller shape successfully removed")
        return {"FINISHED"}
        
# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_match_bone_transforms(bpy.types.Operator):
    """
    Match the widget to the bone transforms // Developped by Manuel Rais and Christophe Seux (bone widget addon) //
    """
    bl_idname = "spt.match_bone_transforms"
    bl_label = "Match bone transforms"
    bl_description = "Matches current shape's transform with related bone's"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        props = context.scene.spt
        if props.edit_widget_active :
            return (context.object and context.object.type == 'MESH'
                and context.object.mode in ['EDIT', 'OBJECT'])
    
    def execute(self, context):
        if context.mode == "POSE":
            for bone in context.selected_pose_bones:
                bone_matrix(context, bone.custom_shape, bone)
            return {'FINISHED'}

        for ob in context.selected_objects:
            if ob.type != 'MESH':
                continue

            match_bone = from_widget_find_bone(context, ob)
            if match_bone:
                bone_matrix(context, ob, match_bone)
        return {'FINISHED'}
    
# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_make_widget_unique(bpy.types.Operator):
    """
    Makes the current bone's widget unique, so it doesn't modify another bone's appearance if changed
    """
    bl_idname = "spt.make_widget_unique"
    bl_label = "Make unique"
    bl_description = "Makes the current bone's widget unique"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        active_bone = context.active_pose_bone
        shape = None
        if active_bone :
            shape = active_bone.custom_shape 
        return (context.object and context.object.type == 'ARMATURE'
            and context.object.mode in ['POSE'] and shape)
    
    def execute(self, context):
        active_obj = context.object
        active_bone = context.active_pose_bone
        shape = active_bone.custom_shape
        state = "is already unique"
        
        for bone in active_obj.pose.bones :
            if shape.name[len(context.object.name)+1:] == bone.name and bone != active_bone:
                shape = shape.copy()
                ctrl_collection = bpy.data.collections.get("CTRL_Shapes")
                ctrl_collection.objects.link(shape)
                state = f"has been duplicated from '{bone.name}', renamed as '{context.object.name}_{active_bone.name}' and is now unique"
                break
            
        if shape.name != f"{context.object.name}_{active_bone.name}" :
            shape.name = f"{context.object.name}_{active_bone.name}"
            if state == "is already unique" :
                state = "is already unique, its name was changed to fit current bone"
        active_bone.custom_shape = shape
        self.report({"INFO"}, f"Widget shape {state}")
        return {'FINISHED'}
    
# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_fix_bone_name(SPT_OT_base_bone_action):
    """
    Removing ".001" at the end of a bone's name, replacing it with correct numbering, also checking for unaccepted characters
    """
    bl_idname = "spt.fix_bone_name"
    bl_label  = "Fix active bone(s) name"
    bl_description = "Removes .### suffix at the end of current bone's name and/or edits existant numerals to increment bone's name, checks for unaccepted characters"

    def execute(self, context):
        props = context.scene.spt
        
        # Checking if children are modifyed too, then calling external function
        selected_bones = context.selected_pose_bones if context.object.mode == 'POSE' else context.selected_editable_bones
        if props.apply_to_children :
            for bone in selected_bones :
                select_children(context, bone)
            selected_bones = context.selected_pose_bones if context.object.mode == 'POSE' else context.selected_editable_bones
        for bone in selected_bones :
            bone.name = fix_name(context, context.active_object, obj_type="bone", bone=bone)
                
        self.report({"INFO"}, "Bone name successfully fixed")
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_change_prefix(SPT_OT_base_bone_action):
    """
    Switching between prefixes
    """
    bl_idname = "spt.change_prefix"
    bl_label  = "Change Prefix"
    bl_description = "Switches between prefixes"
    
    def execute(self, context):
        props = context.scene.spt
        prefixes = [props.skin_prfx, props.control_prfx, props.mecha_prfx]
        
        #Selects all bones to work with
        selected_bones = context.selected_pose_bones if context.object.mode == 'POSE' else context.selected_editable_bones
        if props.apply_to_children :
            for bone in selected_bones :
                select_children(context, bone)
            selected_bones = context.selected_pose_bones if context.object.mode == 'POSE' else context.selected_editable_bones
        
        #Changes bones' prefixes    
        for bone in selected_bones :    
            curr_name = bone.name
            for i, prfx in enumerate(prefixes) :
                if prfx in curr_name :
                    new_prfx = prefixes[i+1] if i < len(prefixes)-1 else ""
                    new_name = f"{new_prfx}{curr_name[len(prfx):]}"
                    bone.name = new_name
                    break
                elif i == len(prefixes)-1 :
                    new_name = f"{props.skin_prfx}{curr_name}"
                    bone.name = new_name
                
        self.report({"INFO"}, "Prefix(es) successfully switched")
        return {'FINISHED'}
            
# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_change_suffix(SPT_OT_base_bone_action):
    """
    Switching between suffixes
    """
    bl_idname = "spt.change_suffix"
    bl_label  = "Change Suffix"
    bl_description = "Switches between suffixes"
    
    def execute(self, context):
        props = context.scene.spt
        suffixes = [".r", ".l"]
        
        #Selects all bones to work with
        selected_bones = context.selected_pose_bones if context.object.mode == 'POSE' else context.selected_editable_bones
        if props.apply_to_children :
            for bone in selected_bones :
                select_children(context, bone)
            selected_bones = context.selected_pose_bones if context.object.mode == 'POSE' else context.selected_editable_bones
        
        #Changes bones' suffixes
        for bone in selected_bones : 
            curr_name = bone.name
            for i, sfx in enumerate(suffixes) :
                if sfx in curr_name :
                    new_sfx = suffixes[i+1] if i < len(suffixes)-1 else ""
                    new_name = f"{curr_name[:-len(sfx)]}{new_sfx}"
                    bone.name = new_name
                    break
                elif i == len(suffixes)-1 :
                    new_name = f"{curr_name}{suffixes[0]}"
                    bone.name = new_name
                     
                  
        self.report({"INFO"}, "Suffix(es) successfully switched")
        return {'FINISHED'}    

# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_select_children(SPT_OT_base_bone_action):
    """
    Selects selected bone's children
    """
    bl_idname = "spt.select_children"
    bl_label  = "Select Children"
    bl_description = "Selects selected bone's children"
            
    def execute(self, context):
        active_bone = context.active_pose_bone if context.object.mode == 'POSE' else context.active_bone
        select_children(context, active_bone)
        return {'FINISHED'}
    
# ──────────────────────────────────────────────────────────────────────────────────────────    
class SPT_OT_select_parents(SPT_OT_base_bone_action):
    """
    Selects selected bone's parents
    """
    bl_idname = "spt.select_parents"
    bl_label  = "Select Parents"
    bl_description = "Selects selected bone's parents"
            
    def execute(self, context):
        active_bone = context.active_pose_bone if context.object.mode == 'POSE' else context.active_bone
        parent = active_bone.parent
        while parent :
            parent.select = True
            if context.object.mode == 'EDIT':
                parent.select_head  = True
                parent.select_tail  = True
            parent = parent.parent
        return {'FINISHED'}

# ──────────────────────────────────────────────────────────────────────────────────────────
class SPT_OT_save_as_shape(bpy.types.Operator):
    """
    Saves selected object as a new widget shape available in widget creation
    """
    bl_idname = "spt.save_as_shape"
    bl_label = "Save as shape"
    bl_description = "Saves selected object as a new widget shape available in widget creation"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        up = False
        if context.object and context.object.type == "MESH" :
            up = True
        elif context.object and context.object.type == "ARMATURE" and context.object.mode == 'POSE' and context.active_pose_bone and context.active_pose_bone.custom_shape :
            up = True
        return up

    def execute(self, context) :
        props = context.scene.spt
        mode = context.object.mode
        active_obj = context.object
        pose = False

        # Getting active mesh or active bone's custom shape
        if context.object and context.object.type == "MESH" :
            obj, bm = get_bmesh_from_active_object()
        else : 
            pose = True
            shape = context.active_pose_bone.custom_shape
            bpy.ops.object.mode_set(mode='OBJECT')
            context.active_object.select_set(False)

            collection = get_view_layer_collection(context, shape)
            collection.hide_viewport = False

            if context.space_data.local_view:
                bpy.ops.view3d.localview()

            # Selecting object and making it active
            shape.select_set(True)
            context.view_layer.objects.active = shape

            obj, bm = get_bmesh_from_active_object()

        # Getting verts and edges
        verts = [list(v.co) for v in bm.verts]
        edges = [[e.verts[0].index, e.verts[1].index] for e in bm.edges]
        # faces = [[v.index for v in f.verts] for f in bm.faces]

        # Loading json file and setting names
        data = load_widgets_data()
        new_key = obj.name
        prfx, base, count_sfx, side_sfx = parse_string(obj.name)
        base = base[:-1] if base[-1:] == "_" else base
        new_label = base

        # Checking if new_key exists
        if new_key in data:
            self.report({'WARNING'}, f"'{new_key}' already exists, change object name and retry.")
            return {'FINISHED'}

        # Writing new shape's infos
        data[new_key] = {
            "label": new_label,
            "icon": "USER",
            "verts": verts,
            "edges": edges,
        }
        save_widgets_data(data)

        # Going back to base state
        if pose :
            bpy.ops.object.mode_set(mode='OBJECT')
            obj.select_set(False)
            active_obj.select_set(True)
            context.view_layer.objects.active = active_obj
            collection.hide_viewport = True
        bpy.ops.object.mode_set(mode=mode)
        self.report({'INFO'}, f"Widget '{new_key}' successfully added.")
        return {'FINISHED'}