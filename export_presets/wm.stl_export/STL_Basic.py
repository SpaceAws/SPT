import bpy
op = bpy.context.active_operator

op.ascii_format = False
op.use_batch = False
op.export_selected_objects = True
op.global_scale = 1.0
op.use_scene_unit = False
op.forward_axis = 'Y'
op.up_axis = 'Z'
op.apply_modifiers = True
