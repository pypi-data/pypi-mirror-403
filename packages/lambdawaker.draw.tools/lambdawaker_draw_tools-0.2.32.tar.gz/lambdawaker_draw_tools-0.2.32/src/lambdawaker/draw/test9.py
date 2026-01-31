import random

import moderngl
import numpy as np
from PIL import Image


def generate_custom_guilloche(
        width=1920,
        height=1080,
        line_density=140.0,  # Total number of horizontal line repeats
        wave_frequency=2.5,  # How many "wiggles" across the screen
        wave_amplitude=0.35,  # How tall the curves are
        weight_speed=5.0,  # How fast the lines thicken/thin along the path
        min_weight=0.0004,  # Minimum line thickness
        max_weight=0.0025,  # Maximum line thickness
        seed=None
):
    if seed is None:
        seed = random.uniform(0, 10000)

    ctx = moderngl.create_context(standalone=True)

    prog = ctx.program(
        vertex_shader='''
            #version 330
            in vec2 in_vert;
            void main() {
                gl_Position = vec4(in_vert, 0.0, 1.0);
            }
        ''',
        fragment_shader='''
            #version 330
            out vec4 fragColor;
            uniform vec2 iResolution;
            uniform float iSeed;

            // User Parameters
            uniform float iDensity;
            uniform float iFreq;
            uniform float iAmp;
            uniform float iWeightSpeed;
            uniform float iMinWeight;
            uniform float iMaxWeight;

            float hash(vec2 p) {
                return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
            }

            float noise(vec2 p) {
                vec2 i = floor(p);
                vec2 f = fract(p);
                vec2 u = f * f * (3.0 - 2.0 * f);
                return mix(mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), u.x),
                           mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
            }

            void main() {
                vec2 uv = gl_FragCoord.xy / iResolution.xy;
                vec3 color = vec3(0.005, 0.005, 0.01); // Deep ink background

                // Primary curve motion
                float wave = noise(vec2(uv.x * iFreq, iSeed)) * iAmp;

                for(float i = 0.0; i < 4.0; i++) {
                    float y_offset = wave + (i * 0.06);
                    float pattern = sin((uv.y + y_offset) * iDensity * 3.1415);

                    // Dynamic thickness modulation
                    // We use a mix of sine and noise for "gradual but random" swelling
                    float weight_noise = noise(vec2(uv.x * iWeightSpeed, i + iSeed));
                    float thickness = mix(iMinWeight, iMaxWeight, weight_noise);

                    float line = 1.0 - smoothstep(0.0, thickness * iDensity, abs(pattern));

                    // Subtle color variation based on line weight
                    vec3 lCol = vec3(0.4, 0.52, 0.65) * (0.5 + weight_noise * 0.5);
                    color += line * lCol * 0.55;
                }

                // Smooth vignette
                float d = length(uv - 0.5);
                color *= smoothstep(1.2, 0.3, d);

                fragColor = vec4(color, 1.0);
            }
        '''
    )

    fbo = ctx.framebuffer(color_attachments=[ctx.texture((width, height), 3)])
    fbo.use()

    vertices = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype='f4')
    vao = ctx.simple_vertex_array(prog, ctx.buffer(vertices), 'in_vert')

    # Assigning the Python parameters to the Shader Uniforms
    prog['iResolution'].value = (width, height)
    prog['iSeed'].value = seed
    prog['iDensity'].value = line_density
    prog['iFreq'].value = wave_frequency
    prog['iAmp'].value = wave_amplitude
    prog['iWeightSpeed'].value = weight_speed
    prog['iMinWeight'].value = min_weight
    prog['iMaxWeight'].value = max_weight

    ctx.clear()
    vao.render(moderngl.TRIANGLE_STRIP)

    raw_data = fbo.read(components=3)
    img = Image.frombytes('RGB', (width, height), raw_data)
    return img.transpose(Image.FLIP_TOP_BOTTOM)


# Example: Generate a "High Contrast" version
img = generate_custom_guilloche(
    width=1920,
    height=1080,
    line_density=100.0,  # Total number of horizontal line repeats
    wave_frequency=2.5,  # How many "wiggles" across the screen
    wave_amplitude=0.35,  # How tall the curves are
    weight_speed=5.0,  # How fast the lines thicken/thin along the path
    min_weight=0.0004,  # Minimum line thickness
    max_weight=0.0025,  # Maximum line thickness
    seed=None
)
img.show()
