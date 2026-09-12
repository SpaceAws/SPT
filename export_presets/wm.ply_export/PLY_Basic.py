import bpy
op = bpy.context.active_operator

op.forward_axis = 'Y'
op.up_axis = 'Z'
op.global_scale = 1.0
op.apply_modifiers = True
op.export_selected_objects = True
op.export_uv = True
op.export_normals = False
op.export_colors = 'SRGB'
op.export_attributes = True
op.export_triangulated_mesh = False
op.ascii_format = False
