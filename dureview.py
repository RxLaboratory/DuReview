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

def removeAnnotations():
    gps = bpy.data.grease_pencils
    for gp in reversed(gps):
        gps.remove(gp)

def createAnnotations():
    bpy.ops.gpencil.annotation_add()
    gp = bpy.data.grease_pencils[0]
    
    rp = bpy.context.scene.review_params

    gp.layers[0].color = rp.notes_colors[0].note_color
    gp.layers[0].info = "Note 01"
    gp.layers[0].thickness = rp.notes_thickness
    
    n = 1
    while n < rp.num_notes:
        noteName = "Note 0" + str(n+1)
        if n == 9: noteName = "Note " + str(n+1)
        gp.layers.new(noteName)
        gp.layers[n].color = rp.notes_colors[n].note_color
        gp.layers[n].thickness = rp.notes_thickness
        n = n+1

def isDuBlastEnabled():
    addons = bpy.context.preferences.addons
    for addon in addons:
        if addon.module == 'dublast':
            return True
    return False

class DUREVIEW_noteColor( bpy.types.PropertyGroup ):
    """The color of a note"""
    note_color: bpy.props.FloatVectorProperty(
        name= "Note color",
        description= "The color of a note",
        default= [0.85, 1.0, 0.0],
        subtype='COLOR'
    )

class DUREVIEW_params( bpy.types.PropertyGroup ):
    """DuReview parameters."""

    num_notes: bpy.props.IntProperty(
        name = "Number of notes",
        description= "Number of notes to setup when opening a video",
        default = 1,
        min = 1,
        max = 10
        )
        
    notes_thickness: bpy.props.IntProperty(
        name = "Default thickness",
        description= "Default thickness of the notes",
        default = 5,
        min = 1,
        max = 10,
        subtype= 'PIXEL'
        )
        
    notes_colors: bpy.props.CollectionProperty(
        type= DUREVIEW_noteColor,
        description="The colors of the notes"
    )

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
        removeAnnotations()
        setVideo( self.filepath )
        createAnnotations()

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
        layout.separator()
        layout.prop(bpy.context.scene.review_params, "num_notes")
        layout.prop(bpy.context.scene.review_params, "notes_thickness")
        if isDuBlastEnabled():
            layout.separator()
            layout.operator('render.playblast',text="Export Video")

classes = (
    DUREVIEW_noteColor,
    DUREVIEW_params,
    DUREVIEW_OT_importVideo,
    DUREVIEW_PT_video_review
)

def register():
    # register
    for cls in classes:
        bpy.utils.register_class(cls)
            
    # Add the params in the scene
    if hasattr( bpy.types.Scene, 'review_params' ):
        del bpy.types.Scene.review_params
        
    bpy.types.Scene.review_params = bpy.props.PointerProperty( type=DUREVIEW_params )
    rp = bpy.context.scene.review_params
    c = rp.notes_colors.add()
    c.note_color = [0.85, 1.0, 0.0]
    c = rp.notes_colors.add()
    c.note_color = [1.0, 0.45, 0.0]
    c = rp.notes_colors.add()
    c.note_color = [1.0, 0.0, 0.85]
    c = rp.notes_colors.add()
    c.note_color = [0.45, 0.0, 1.0]
    c = rp.notes_colors.add()
    c.note_color = [0.0, 0.0, 1.0]
    c = rp.notes_colors.add()
    c.note_color = [0.0, 1.0, 1.0]
    c = rp.notes_colors.add()
    c.note_color = [0.0, 1.0, 0.45]
    c = rp.notes_colors.add()
    c.note_color = [0.0, 1.0, 0.0]
    c = rp.notes_colors.add()
    c.note_color = [1.0, 0.0, 0.0]
    c = rp.notes_colors.add()
    c.note_color = [0.85, 0.0, 0.0]

def unregister():
    # unregister
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    # attributes
    del bpy.types.Scene.review_params

if __name__ == "__main__":
    register()
