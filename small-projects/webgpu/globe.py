import sys
import math
import time
from struct import pack

from PyQt5.QtWidgets import QApplication
from PIL import Image

import wgpu
import wgpu.backends.rs
from wgpu.gui.qt import WgpuCanvas

from pyshader import python2shader
from pyshader import RES_INPUT, RES_OUTPUT, RES_UNIFORM, RES_TEXTURE
from pyshader import vec2, vec3, vec4, ivec2, i32

img = Image.open("WorldTest.png").convert("RGBA")

FPS = 240
numVertices = 6


# %% Shaders
@python2shader
def vertex_shader(
    index: (RES_INPUT, "VertexId", i32),  # noqa
    pos: (RES_OUTPUT, "Position", vec4),  # noqa
    uv: (RES_OUTPUT, 0, vec2),
):
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
    d2 = in_uv.x**2 + in_uv.y**2
    if d2 > 1.0:
        # density = math.exp(50.0 * (1.0 - r))
        out_color = vec4(0, 0, 0, 0)
    else:
        c = math.sqrt(1.0 - d2)

        in_uv_rot = vec2(
            in_uv.x * math.cos(in_rot.z) + in_uv.y * math.sin(in_rot.z),
            in_uv.y * math.cos(in_rot.z) - in_uv.x * math.sin(in_rot.z)
        )

        lam = in_rot.x + math.atan2(in_uv_rot.x, c * math.cos(in_rot.y)
                                    - in_uv_rot.y * math.sin(in_rot.y))
        phi = math.asin(c * math.sin(in_rot.y)
                        + in_uv_rot.y * math.cos(in_rot.y))

        uvCoord = vec2((lam / math.pi + 1.0) % 2.0 - 1.0, 2.0 * phi / math.pi)

        texCoords = ivec2((uvCoord + vec2(1, -1)) * vec2(800, -400))

        pos = vec3(
            math.cos(phi) * math.cos(lam),
            math.cos(phi) * math.sin(lam),
            math.sin(phi)
        )

        light = vec3(math.sin(in_rot.w), math.cos(in_rot.w), -.1 * in_rot.z)
        intensity = math.normalize(pos) @ math.normalize(light)
        if intensity < 0.0:
            color = vec4(.01, .01, .01, 1)
        else:
            intensity += .01
            color = vec4(intensity, intensity, intensity, 1)

        out_color = in_tex.read(texCoords).zyxw * color  # noqa


# %% The wgpu calls
def main(canvas):
    """Regular function to setup a viz on the given canvas."""
    # like Graphics driver (search for compatible)
    adapter = wgpu.request_adapter(  # "high-performance" or "low-power"
        canvas=canvas, power_preference="high-performance")
    # Create an instance of the previous adapter
    device = adapter.request_device(extensions=[], limits={})
    return _main(canvas, device)


def _main(canvas, device):
    texture = device.create_texture(
        size=(img.width, img.height, 1),
        format=wgpu.TextureFormat.bgra8unorm_srgb,
        usage=wgpu.TextureUsage.SAMPLED | wgpu.TextureUsage.COPY_DST
    )
    device.default_queue.write_texture(
        destination={"texture": texture},
        data=img.tobytes(),
        data_layout={"bytes_per_row": img.width * 4},
        size=(img.width, img.height, 1)
    )

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

    def draw_frame(i):
        f1 = -i % (2 * math.pi)
        f2 = 0.5 * math.sin(0.4 * i % (2 * math.pi))
        f3 = -0.5 * math.cos(0.4 * i % (2 * math.pi))
        f4 = (i * 0.5) % (2 * math.pi)

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

            render_pass.draw(numVertices)
            render_pass.end_pass()

            device.default_queue.submit([command_encoder.finish()])

    return draw_frame


if __name__ == "__main__":
    app = QApplication(sys.argv)
    canvas = WgpuCanvas(title="wgpu with Qt")
    canvas.resize(800, 800)
    draw_frame = main(canvas)

    while not canvas.is_closed():
        start = time.time()
        app.processEvents()

        canvas.request_draw(lambda: draw_frame(start))

        # The slowest thing in the loop is time.sleep
        time.sleep(max(1 / FPS - time.time() + start, 0))
        print(round(1 / (time.time() - start), 2), "FPS", start)

    app.exit()
