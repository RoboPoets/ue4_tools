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
    bl_label = "UCX: To UCX"
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
        for o in context.selected_objects:
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
    bl_label = "UCX: Select Possible Collision Shapes"
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


################################################################
#
#################################################################
class SelectUCX(bpy.types.Operator):
    """Select visible collision shapes, either all or only those matching an optional base name"""
    bl_idname = "object.ue4t_select_ucx"
    bl_label = "UCX: Select Collision Shapes"
    bl_options = {'REGISTER', 'UNDO'}

    base_name = bpy.props.StringProperty(name="Base Name (Optional)")

    @classmethod
    def poll(cls, context):
        return context.object is None or context.object.mode == 'OBJECT'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.row().prop(self, "base_name")

    def execute(self, context):
        for obj in context.selected_objects:
            obj.select = False

        search_string = "UCX_" + self.base_name
        for obj in context.selectable_objects:
            if obj.type != 'MESH':
                continue
            if obj.name.startswith(search_string):
                obj.select = True

        return {'FINISHED'}


class Bake(bpy.types.Operator):
    """Bake Maps used for edge wear, dust accumulation & cavities"""
    bl_idname = "object.mtrlz_bake"
    bl_label = "Materializer: Bake"
    bl_options = {'REGISTER', 'UNDO'}

    mat_id = "M_Bake"
    _node_ids = ['AO', 'WSN', 'Edge']

    _meshes = []
    _idx = 0
    _state = 0
    working = False
    timer = None

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        self._meshes = []
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                obj.select = False
                continue
            for slot in obj.material_slots:
                slot.material = bpy.data.materials[self.mat_id]
            obj.data.uv_textures.active_index = 1
            self._meshes.append(obj)

        self._idx = 0
        self._state = 0
        self.working = False
        self.timer = context.window_manager.event_timer_add(1.0, context.window)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER' and not self.working:
            self.working = True
            bpy.ops.object.select_all(action='DESELECT')
            self._meshes[self._idx].select = True
            nodes = bpy.data.materials[self.mat_id].node_tree.nodes
            node = nodes[self._node_ids[self._state]]
            node.select = True
            nodes.active = node

            if self._state == 0:
                bpy.ops.object.bake(type = 'AO', margin = 4, use_clear = (self._idx == 0))
            elif self._state == 1:
                bpy.ops.object.bake(type = 'NORMAL', margin = 4, normal_space = 'OBJECT', use_clear = (self._idx == 0))
            elif self._state == 2:
                bpy.ops.object.bake(type='DIFFUSE', margin=4, pass_filter={'COLOR'}, use_clear=(self._idx == 0))

            self._idx += 1
            if self._idx == len(self._meshes):
                self._idx = 0
                self._state += 1

            self.working = False
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        if self._state == 3:
            return self.cancel(context)

        return {'PASS_THROUGH'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self.timer)
        self.timer = None
        for obj in self._meshes:
            obj.select = True
        return {'CANCELLED'}


#################### boring init stuff ############################

def register():
    bpy.utils.register_class(ToUCX)
    bpy.utils.register_class(SelectUCXCandidates)
    bpy.utils.register_class(SelectUCX)
    bpy.utils.register_class(Bake)


def unregister():
    bpy.utils.unregister_class(ToUCX)
    bpy.utils.unregister_class(SelectUCXCandidates)
    bpy.utils.unregister_class(SelectUCX)
    bpy.utils.unregister_class(Bake)


if __name__ == "__main__":
    register()
