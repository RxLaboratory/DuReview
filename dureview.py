# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy # pylint: disable=import-error
from bpy_extras.io_utils import ImportHelper # pylint: disable=import-error
import os

def setVideo( videoFile ):
    # get file name
    videoName = bpy.path.basename( videoFile )
    videoName = os.path.splitext( videoName )[0]
    
    # remove all sounds
    for s in bpy.data.sounds:
        bpy.data.sounds.remove(s)
    # remove all clips from sequencer
    sequences = bpy.context.scene.sequence_editor.sequences
    for seq in reversed( sequences ):
        sequences.remove(seq)
    # set the video and sound in the sequencer
    sequences.new_sound(videoName, videoFile, 1, 1)
    video = sequences.new_movie(videoName, videoFile, 2, 1)
    # bug in blender. Let's change some param on the sound to update it
    bpy.data.sounds[0].use_mono = True
    bpy.data.sounds[0].use_mono = False
    
    # set the video in the node
    image = bpy.data.images.load(videoFile, check_existing = True)
    videoTexture = bpy.data.materials['VideoPlayer'].node_tree.nodes['VideoTexture']
    videoTexture.image = image
    image.source = 'MOVIE'
    videoTexture.image_user.frame_duration = video.frame_duration
    # set scene end frame
    bpy.context.scene.frame_end = video.frame_duration
    print("Video duration: " + str(video.frame_duration))
    print("New duration: " + str(bpy.context.scene.frame_end))
    # set scene name from video
    bpy.context.scene.name = videoName
    # set scene resolution to resolution of the video
    bpy.context.scene.render.resolution_x = image.size[0]
    bpy.context.scene.render.resolution_y = image.size[1]
    # set aspect
    bpy.data.objects['Screen'].scale = [1.0, image.size[1] / image.size[0], 1.0]

def isDuBlastEnabled():
    addons = bpy.context.preferences.addons
    for addon in addons:
        if addon.module == 'dublast':
            return True
    return False

class DUREVIEW_OT_importVideo( bpy.types.Operator, ImportHelper ):
    """Imports a video for the reviewer."""
    bl_idname = "scene.review_import_video"
    bl_label = "Open Video..."
    bl_description = "Imports a new video."
    bl_option = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        mat = bpy.data.materials['VideoPlayer']
        if mat is None: return False
        if mat.node_tree.nodes["VideoTexture"] is None: return False
        return True

    def execute(self, context):

        setVideo( self.filepath )

        return {'FINISHED'}

class DUREVIEW_PT_video_review(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Video Review"
    bl_idname = "DUREVIEW_PT_video_review"
    bl_category = 'View'

    def draw(self, context):
        layout = self.layout
        layout.operator(DUREVIEW_OT_importVideo.bl_idname)
        if isDuBlastEnabled():
            layout.operator('render.playblast',text="Export Video")

classes = (
    DUREVIEW_OT_importVideo,
    DUREVIEW_PT_video_review
)

def register():
    # register
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    # unregister
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
