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
    "version": (0, 1, 0),
    "blender": (2, 79, 0),
    "category": "Object"
}

import bpy

class UCXData(bpy.types.PropertyGroup):
    base_name = bpy.props.StringProperty(name="Base Name")
    start_idx = bpy.props.IntProperty(name="Starting Number")


################################################################
# Transfer an action from one skeletonn to another. This is
# done by renaming the curves in the action from old bone names
# to their counterparts in the active skeleton.
#################################################################
class ToUCX(bpy.types.Operator):
    """Rename selected meshes to be compatible with UE4's collision naming conventions"""
    bl_idname = "object.ue4t_mesh_to_ucx"
    bl_label = "UE4 Tools: To UCX"
    bl_options = {'REGISTER', 'UNDO'}

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
        layout.row().prop(context.scene.ue4t_ucx_data, "base_name")
        layout.row().prop(context.scene.ue4t_ucx_data, "start_idx")

    def execute(self, context):
        data = context.scene.ue4t_ucx_data
        has_base_name = False

        for obj in context.scene.objects:
            if obj.name == data.base_name:
                has_base_name = True
                break
        if not has_base_name:
            self.report({'WARNING'}, "No object with base name found in scene.")

        for obj in context.selected_objects:
            if obj.name == data.base_name:
                self.report({'WARNING'}, "Object with base name is selected and will be renamed.")
            obj.name = "UCX_" + data.base_name + "_" + "%02d" % data.start_idx
            data.start_idx += 1

        print(data.base_name, data.start_idx)
        return {'FINISHED'}


#################### boring init stuff ############################

def register():
    bpy.utils.register_class(UCXData)
    bpy.utils.register_class(ToUCX)

    bpy.types.Scene.ue4t_ucx_data = bpy.props.PointerProperty(type=UCXData)


def unregister():
    del bpy.types.Scene.ue4t_ucx_data

    bpy.utils.unregister_class(UCXData)
    bpy.utils.unregister_class(ToUCX)


if __name__ == "__main__":
    register()
