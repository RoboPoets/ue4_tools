#################################################################
# Copyright (c) 2018 POET Industries
#
# This code is distributed under the MIT License. For a complete
# list of terms see accompanying LICENSE file or the copy at
# https://opensource.org/licenses/MIT
#################################################################

bl_info = {
    "name": "UE4 Tools",
    "author": "POET Industries",
    "version": (0, 2, 0),
    "blender": (2, 79, 0),
    "category": "Object"
}

import bpy, math

################################################################
# Renames the selected meshes according to Unreal Engine 4
# naming conventions for collision shapes, which are
# UCX_[objectname]_XX, where XX denotes a continuous sequence
# of numbers and [objectname] has to be the name of one mesh
# included in the exported static mesh FBX file.
#################################################################
class ToUCX(bpy.types.Operator):
    """Rename selected meshes to be compatible with UE4's collision naming conventions"""
    bl_idname = "object.ue4t_mesh_to_ucx"
    bl_label = "UE4 Tools: To UCX"
    bl_options = {'REGISTER', 'UNDO'}

    base_name = bpy.props.StringProperty(name="Base Name")
    start_idx = bpy.props.IntProperty(name="Starting Number")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None or obj.mode != 'OBJECT':
            return False
        return len(context.selected_objects) != 0

    def invoke(self, context, event):
        selection = context.selected_objects

        for o in selection:
            if o.type != 'MESH':
                self.report({'ERROR'}, "Only meshes can be collision shapes.")
                return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.row().prop(self, "base_name")
        layout.row().prop(self, "start_idx")

    def execute(self, context):
        has_base_name = False

        for obj in context.scene.objects:
            if obj.name == self.base_name:
                has_base_name = True
                break
        if not has_base_name:
            self.report({'WARNING'}, "No object with base name found in scene.")

        # determine the number of digits for the numerical suffix
        num_digits = max(1 + int(math.log10(self.start_idx + len(context.selected_objects))), 2)
        fmt = "%0" + str(num_digits) + "d"

        for obj in context.selected_objects:
            if obj.name == self.base_name:
                self.report({'WARNING'}, "Object with base name is selected and will be renamed.")
            obj.name = "UCX_" + self.base_name + "_" + fmt % self.start_idx
            self.start_idx += 1

        return {'FINISHED'}


################################################################
#
#################################################################
class SelectUCXCandidates(bpy.types.Operator):
    """Select all meshes that are intended to be used as collision shapes"""
    bl_idname = "object.ue4t_select_ucx_candidates"
    bl_label = "UE4 Tools: Select Possible Collision Shapes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object is None or context.object.mode == 'OBJECT'

    def execute(self, context):
        for obj in context.selected_objects:
            obj.select = False

        for obj in context.selectable_objects:
            if obj.name.startswith("UCX_"):
                continue
            if obj.type != 'MESH' or obj.draw_type != 'WIRE':
                continue
            if len(obj.material_slots) != 0:
                continue
            obj.select = True

        return {'FINISHED'}


#################### boring init stuff ############################

def register():
    bpy.utils.register_class(UCXData)
    bpy.utils.register_class(ToUCX)
    bpy.utils.register_class(SelectUCXCandidates)


def unregister():
    bpy.utils.unregister_class(UCXData)
    bpy.utils.unregister_class(ToUCX)
    bpy.utils.unregister_class(SelectUCXCandidates)


if __name__ == "__main__":
    register()
