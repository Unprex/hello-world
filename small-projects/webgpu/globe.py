import sys
import math
from struct import pack

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QElapsedTimer
from PIL import Image

import wgpu
import wgpu.backends.rs
from wgpu.gui.qt import WgpuCanvas

from pyshader import python2shader
from pyshader import RES_INPUT, RES_OUTPUT, RES_UNIFORM, RES_TEXTURE
from pyshader import vec2, vec3, vec4, ivec2, i32

# Limited by QTimer (min = 1ms/frame)
FPS = 60
mapTexture = "WorldTest.png"


# %% Shaders
@python2shader
def vertex_shader(
    index: (RES_INPUT, "VertexId", i32),  # noqa
    pos: (RES_OUTPUT, "Position", vec4),  # noqa
    uv: (RES_OUTPUT, 0, vec2),
):
    # 6 vertices. TODO: Update with uniform to keep ratio
    positions = [vec2(1, 1), vec2(-1, 1), vec2(-1, -1),
                 vec2(1, 1), vec2(1, -1), vec2(-1, -1)]
    p = positions[index]
    pos = vec4(p, 0.0, 1.0)  # noqa
    uv = p  # noqa


@python2shader
def fragment_shader(
    in_tex: (RES_TEXTURE, 0, "2d f32"),
    in_uv: (RES_INPUT, 0, vec2),
    in_rot: (RES_UNIFORM, 1, vec4),
    out_color: (RES_OUTPUT, 0, vec4),
):
    # Distance squared to center of circle
    d2 = in_uv.x**2 + in_uv.y**2

    # Check if outside of map boundary
    if d2 > 1.0:
        # density = math.exp(50.0 * (1.0 - r))  # Display atmosphere
        out_color = vec4(0, 0, 0, 0)
    else:
        # Camera rotation
        in_uv_rot = vec2(
            in_uv.x * math.cos(in_rot.z) + in_uv.y * math.sin(in_rot.z),
            in_uv.y * math.cos(in_rot.z) - in_uv.x * math.sin(in_rot.z)
        )

        # Map transformation
        c = math.sqrt(1.0 - d2)
        lam = in_rot.x + math.atan2(in_uv_rot.x, c * math.cos(in_rot.y)
                                    - in_uv_rot.y * math.sin(in_rot.y))
        phi = math.asin(c * math.sin(in_rot.y)
                        + in_uv_rot.y * math.cos(in_rot.y))

        # Get coordinates of color on texture
        uvCoord = vec2((lam / math.pi + 1.0) % 2.0 - 1.0, 2.0 * phi / math.pi)
        texCoords = ivec2((uvCoord + vec2(1, -1)) * vec2(800, -400))

        # Get normal in globe reference frame
        norm = math.normalize(vec3(
            math.cos(phi) * math.cos(lam),
            math.cos(phi) * math.sin(lam),
            math.sin(phi)
        ))

        # Set light direction
        light = vec3(math.sin(in_rot.w), math.cos(in_rot.w), -.1 * in_rot.z)
        # Get light intensity
        intensity = norm @ math.normalize(light)
        # Set ambient lighting
        ambient = .1
        # Check if in shadow
        if intensity < 0.0:
            shading = vec4(ambient, ambient, ambient, 1)
        else:
            intensity += ambient
            shading = vec4(intensity, intensity, intensity, 1)

        # Get texture color and apply shading
        out_color = in_tex.read(texCoords).zyxw * shading  # noqa


# %% The wgpu calls
def get_draw_function(canvas, img):
    """Regular function to setup a viz on the given canvas."""
    # like Graphics driver (search for compatible)
    adapter = wgpu.request_adapter(  # "high-performance" or "low-power"
        canvas=canvas, power_preference="high-performance")
    # Create an instance of the previous adapter
    device = adapter.request_device(extensions=[], limits={})

    # Create texture object
    texture = device.create_texture(
        size=(img.width, img.height, 1),
        format=wgpu.TextureFormat.bgra8unorm_srgb,
        usage=wgpu.TextureUsage.SAMPLED | wgpu.TextureUsage.COPY_DST
    )
    # Update texture with pixels
    device.default_queue.write_texture(
        destination={"texture": texture},
        data=img.tobytes(),
        data_layout={"bytes_per_row": img.width * 4},
        size=(img.width, img.height, 1)
    )

    # Create 16 byte uniform buffer (updated in draw_frame)
    rotation = device.create_buffer(
        size=16,
        usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
    )

    # Default swap chain (frame buffer)
    swap_chain = device.configure_swap_chain(
        canvas,
        device.get_swap_chain_preferred_format(canvas),
        wgpu.TextureUsage.OUTPUT_ATTACHMENT,
    )

    vshader = device.create_shader_module(code=vertex_shader)
    fshader = device.create_shader_module(code=fragment_shader)

    # bindings
    bind_group_layout = device.create_bind_group_layout(entries=[
        {
            "binding": 0,
            "visibility": wgpu.ShaderStage.FRAGMENT,
            "type": wgpu.BindingType.sampled_texture,
            "view_dimension": wgpu.TextureViewDimension.d2,
            "texture_component_type": wgpu.TextureComponentType.float
        },
        {
            "binding": 1,
            "visibility": wgpu.ShaderStage.FRAGMENT,
            "type": wgpu.BindingType.uniform_buffer
        }
    ])
    bind_group = device.create_bind_group(layout=bind_group_layout, entries=[
        {
            "binding": 0,
            "resource": texture.create_view(),
        },
        {
            "binding": 1,
            "resource": {
                "buffer": rotation,
                "offset": 0,
                "size": 16
            }
        }
    ])

    pipeline_layout = device.create_pipeline_layout(
        bind_group_layouts=[bind_group_layout]
    )

    render_pipeline = device.create_render_pipeline(
        layout=pipeline_layout,
        vertex_stage={"module": vshader, "entry_point": "main"},
        fragment_stage={"module": fshader, "entry_point": "main"},
        primitive_topology=wgpu.PrimitiveTopology.triangle_list,
        rasterization_state={
            "front_face": wgpu.FrontFace.ccw,
            "cull_mode": wgpu.CullMode.none,
            "depth_bias": 0,
            "depth_bias_slope_scale": 0.0,
            "depth_bias_clamp": 0.0,
        },
        color_states=[{
            "format": wgpu.TextureFormat.bgra8unorm_srgb,
            "alpha_blend": (
                wgpu.BlendFactor.one,
                wgpu.BlendFactor.zero,
                wgpu.BlendOperation.add,
            ),
            "color_blend": (
                wgpu.BlendFactor.one,
                wgpu.BlendFactor.zero,
                wgpu.BlendOperation.add,
            ),
        }],
        vertex_state={
            "index_format": wgpu.IndexFormat.uint32,
            "vertex_buffers": []
        }
    )

    def draw_frame(t):
        f1 = -t % (2 * math.pi)
        f2 = 0.5 * math.sin(0.4 * t % (2 * math.pi))
        f3 = -0.5 * math.cos(0.4 * t % (2 * math.pi))
        f4 = (t * 0.5) % (2 * math.pi)

        # Update 16 byte uniform buffer
        device.default_queue.write_buffer(
            rotation, 0,
            pack("f", f1) + pack("f", f2) + pack("f", f3) + pack("f", f4)
        )

        with swap_chain as current_texture_view:
            command_encoder = device.create_command_encoder()

            render_pass = command_encoder.begin_render_pass(
                color_attachments=[{
                    "attachment": current_texture_view,
                    "load_value": (0, 0, 0, 0),
                }]
            )

            render_pass.set_pipeline(render_pipeline)

            # Associate a vertex buffer with a bind slot
            # render_pass.set_vertex_buffer(slot, buffer)

            # last 2 elements not used
            render_pass.set_bind_group(0, bind_group, [], 0, 999999)

            # Draw 6 vertices (two triangles)
            render_pass.draw(6)
            render_pass.end_pass()

            device.default_queue.submit([command_encoder.finish()])

    return draw_frame


class MainWindow(WgpuCanvas):
    def __init__(self, parent=None, title=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle(title)

        # Load Map texture
        img = Image.open(mapTexture).convert("RGBA")

        # Create the WebGPU draw function and initialize GPU
        self.drawFunction = get_draw_function(self, img)

        self.request_draw(self.mainloop)  # Updates on resize / redraw

        # Set timer to update every frame
        self.timer = QTimer()
        self.timer.timeout.connect(self.mainloop)
        self.timer.start(math.floor(1000 / FPS))

        self.timing = QElapsedTimer()
        self.timing.start()
        self.oldTime = 0

    def mainloop(self):
        """ Main update loop """

        if self.is_closed():
            self.timer.stop()
            return

        # Get current time since launch
        t = self.timing.elapsed() / 1000

        # Call draw fonction with the time
        self.drawFunction(t)

        # Display FPS
        if t - self.oldTime > 0:
            print(round(1 / (t - self.oldTime), 2), "FPS")
        self.oldTime = t


def main():
    app = QApplication(sys.argv)
    gui = MainWindow(title="wgpu with Qt")
    gui.resize(800, 800)
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
