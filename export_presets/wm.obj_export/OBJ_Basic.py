import bpy
op = bpy.context.active_operator

op.export_animation = False
op.start_frame = 1
op.end_frame = 250
op.forward_axis = 'NEGATIVE_Z'
op.up_axis = 'Y'
op.global_scale = 1.0
op.apply_modifiers = True
op.apply_transform = True
op.export_eval_mode = 'DAG_EVAL_VIEWPORT'
op.export_selected_objects = True
op.export_uv = True
op.export_normals = True
op.export_colors = False
op.export_materials = True
op.export_pbr_extensions = False
op.path_mode = 'AUTO'
op.export_triangulated_mesh = False
op.export_curves_as_nurbs = False
op.export_object_groups = False
op.export_material_groups = False
op.export_vertex_groups = False
op.export_smooth_groups = False
op.smooth_group_bitflags = False
