import sys
import math as np
from struct import pack

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QElapsedTimer
from PIL import Image

import wgpu
import wgpu.backends.rs
from wgpu.gui.qt import WgpuCanvas

# Limited by QTimer (min = 1ms/frame)
FPS = 60
mapTexture = "WorldTest.png"

shader_source = """
struct VertexInput {
    @builtin(vertex_index) vertex_index : u32,
};
struct VertexOutput {
    @builtin(position) pos: vec4<f32>,
    @location(0) uv: vec2<f32>,
};

@stage(vertex)
fn vs_main(in: VertexInput) -> VertexOutput {
    // 6 vertices. TODO: keep ratio
    var positions = array<vec2<f32>, 6>(
        vec2<f32>(1.0, 1.0), vec2<f32>(-1.0, 1.0), vec2<f32>(-1.0, -1.0),
        vec2<f32>(1.0, 1.0), vec2<f32>(1.0, -1.0), vec2<f32>(-1.0, -1.0)
    );
    let index = i32(in.vertex_index);
    let p = positions[index];
    var out: VertexOutput;
    out.pos = vec4<f32>(p, 0.0, 1.0);
    out.uv.x = p.x;
    out.uv.y = -p.y;
    return out;
}

@group(0) @binding(0) var tex: texture_2d<f32>;
@group(0) @binding(1) var sam: sampler;

struct Uniform { rot: vec4<f32> };
@group(0) @binding(2) var<uniform> un: Uniform;

@stage(fragment)
fn fs_main(in: VertexOutput)
-> @location(0) vec4<f32> {
    let pi = radians(180.);

    let d2 = in.uv.x * in.uv.x + in.uv.y * in.uv.y;

    // Camera rotation
    let in_uv_rot = vec2<f32>(
        in.uv.x * cos(un.rot.z) + in.uv.y * sin(un.rot.z),
        in.uv.y * cos(un.rot.z) - in.uv.x * sin(un.rot.z)
    );

    // Map transformation
    let c = sqrt(1.0 - d2);
    let lam = un.rot.x + atan2(in_uv_rot.x, c * cos(un.rot.y)
                               - in_uv_rot.y * sin(un.rot.y));
    let phi = asin(c * sin(un.rot.y)
                   + in_uv_rot.y * cos(un.rot.y));

    // Get coordinates of color on texture
    let uv = vec2<f32>(lam / 2.0, phi) / pi + 0.5;
    let col = textureSample(tex, sam, uv);

    if (d2 > 1.0) {
        // Display atmosphere
        // let density = exp(40.0 * (1.0 - d2));
        // return vec4<f32>(0.1, 0.5, 1.0, density);
        return vec4<f32>(0.1, 0.5, 1.0, 0.0);
    }

    // Set light direction
    let light = normalize(vec3<f32>(
        sin(un.rot.w),
        cos(un.rot.w),
        -.1 * un.rot.z
    ));

    // Get normal in globe reference frame
    let norm = normalize(vec3<f32>(
        cos(phi) * cos(lam),
        cos(phi) * sin(lam),
        sin(phi)
    ));

    // Get light intensity
    let intensity = dot(light, norm);

    // Set ambient lighting
    let ambient = .1;

    // Check if in shadow
    if (intensity < 0.0) {
        return col * vec4<f32>(ambient, ambient, ambient, 1.0);
    } else {
        let intensity = intensity + ambient;
        return col * vec4<f32>(intensity, intensity, intensity, 1.0);
    }
}
"""


def get_draw_function(canvas, img):
    """Regular function to setup a viz on the given canvas."""

    # Note: passing the canvas here can (oddly enough) prevent the
    # adapter from being found. Seen with wx/Linux.
    adapter = wgpu.request_adapter(  # "high-performance" or "low-power"
        canvas=None, power_preference="high-performance")

    # Create an instance of the previous adapter
    device = adapter.request_device()

    # Create texture object
    texture = device.create_texture(
        size=(img.width, img.height, 1),
        format=wgpu.TextureFormat.rgba8unorm_srgb,
        usage=wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.COPY_DST
    )
    # Update texture with pixels
    device.queue.write_texture(
        destination={"texture": texture},
        data=img.tobytes(),
        data_layout={"bytes_per_row": img.width * 4},
        size=(img.width, img.height, 1)
    )
    # Create sampler
    sampler = device.create_sampler(
        address_mode_u=wgpu.AddressMode.repeat,
        mag_filter=wgpu.FilterMode.linear
    )

    # Create 16 byte uniform buffer (updated in draw_frame)
    rotation = device.create_buffer(
        size=16,
        usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
    )

    shader = device.create_shader_module(code=shader_source)

    # bindings
    bind_group_layout = device.create_bind_group_layout(entries=[
        {
            "binding": 0,
            "visibility": wgpu.ShaderStage.FRAGMENT,
            "texture": {
                "sample_type": wgpu.TextureSampleType.float,  # optional
                "view_dimension": wgpu.TextureViewDimension.d2,  # optional
                "multisampled": False,  # optional
            }
        },
        {
            "binding": 1,
            "visibility": wgpu.ShaderStage.FRAGMENT,
            "sampler": {
                "type": wgpu.SamplerBindingType.filtering,
            }
        },
        {
            "binding": 2,
            "visibility": wgpu.ShaderStage.FRAGMENT,
            "buffer": {
                "type": wgpu.BufferBindingType.uniform,
                "has_dynamic_offset": False,  # optional
                "min_binding_size": 0  # optional
            }
        }
    ])
    bind_group = device.create_bind_group(layout=bind_group_layout, entries=[
        {
            "binding": 0,
            "resource": texture.create_view(),
        },
        {
            "binding": 1,
            "resource": sampler,
        },
        {
            "binding": 2,
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

    present_context = canvas.get_context()
    render_texture_format = present_context.get_preferred_format(
        device.adapter)
    present_context.configure(device=device, format=render_texture_format)

    render_pipeline = device.create_render_pipeline(
        layout=pipeline_layout,

        vertex={
            "module": shader,
            "entry_point": "vs_main",
            "buffers": []
        },
        primitive={
            "topology": wgpu.PrimitiveTopology.triangle_list,
            "front_face": wgpu.FrontFace.ccw,
            "cull_mode": wgpu.CullMode.none,
        },

        fragment={
            "module": shader,
            "entry_point": "fs_main",
            "targets": [
                {
                    "format": render_texture_format,
                    "blend": {
                        "color": (
                            wgpu.BlendFactor.src_alpha,
                            wgpu.BlendFactor.one_minus_src_alpha,
                            wgpu.BlendOperation.add,
                        ),
                        "alpha": (
                            wgpu.BlendFactor.one,
                            wgpu.BlendFactor.zero,
                            wgpu.BlendOperation.add,
                        ),
                    },
                },
            ],
        },
    )

    def draw_frame(t):
        f1 = -t % (2 * np.pi)
        f2 = 0.5 * np.sin(0.4 * t % (2 * np.pi))
        f3 = -0.5 * np.cos(0.4 * t % (2 * np.pi))
        f4 = (t * 0.5) % (2 * np.pi)

        # Update 16 byte uniform buffer
        device.queue.write_buffer(
            rotation, 0,
            pack("f", f1) + pack("f", f2) + pack("f", f3) + pack("f", f4)
        )

        current_texture_view = present_context.get_current_texture()
        command_encoder = device.create_command_encoder()

        render_pass = command_encoder.begin_render_pass(
            color_attachments=[
                {
                    "view": current_texture_view,
                    "resolve_target": None,
                    "clear_value": (0, 0, 0, 0),
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                }
            ],
        )

        render_pass.set_pipeline(render_pipeline)

        # last 2 elements not used
        render_pass.set_bind_group(0, bind_group, [], 0, 1)

        # Draw 6 vertices (two triangles)
        render_pass.draw(6)
        render_pass.end()

        device.queue.submit([command_encoder.finish()])

    return draw_frame


class MainWindow(WgpuCanvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load Map texture
        img = Image.open(mapTexture).convert("RGBA")

        # Create the WebGPU draw function and initialize GPU
        self.drawFunction = get_draw_function(self, img)

        # Set timer to update every frame
        self.timer = QTimer()
        self.timer.timeout.connect(self.mainloop)
        self.timer.start(int(np.floor(1000 / FPS)))

        # Track time
        self.timing = QElapsedTimer()
        self.timing.start()
        self.oldTime = 0

    def mainloop(self):
        """Main update loop"""

        if self.is_closed():
            self.timer.stop()
            return

        # Get current time since launch
        t = self.timing.elapsed() / 1000

        # Call draw fonction with the tracked time
        self.drawFunction(t)
        # Update the Widget
        self.update()

        # Display FPS
        if t - self.oldTime > 0:
            print(round(1 / (t - self.oldTime), 2), "FPS")
        self.oldTime = t


def main():
    app = QApplication(sys.argv)
    gui = MainWindow(size=(800, 800), title="wgpu with Qt")
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
