from typing import Tuple, Union, Optional, Any

import moderngl
import numpy as np
from PIL import Image

from lambdawaker.draw.color.HSLuvColor import ColorUnion, to_hsluv_color
from lambdawaker.draw.gradient.voronoid.parameters import generate_random_voronoid_parameters
from lambdawaker.random.values import Random, Default, clean_passed_parameters


def paint_voronoid(
        image: Image.Image,
        right_corner: Tuple[int, int] = (0, 0),
        size: Optional[Tuple[int, int]] = None,
        color_a: ColorUnion = (193, 41, 46, 255),
        color_b: ColorUnion = (241, 211, 2, 255),
        timestamp: float = 1.0,
        scale: float = 30.0,
        angle_degrees: float = 0.0,  # New parameter
) -> None:
    """
    Draws a Voronoi (voronoid) gradient onto an existing PIL image using ModernGL.
    """

    width, height = size if size is not None else image.size

    c1 = to_hsluv_color(color_a).to_rgba()
    c2 = to_hsluv_color(color_b).to_rgba()

    # Normalize colors to 0-1 for GLSL
    col1_vec = [c1[0] / 255.0, c1[1] / 255.0, c1[2] / 255.0]
    col2_vec = [c2[0] / 255.0, c2[1] / 255.0, c2[2] / 255.0]

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
            uniform float iTime;
            uniform float SIZE;
            uniform vec3 col1;
            uniform vec3 col2;
            uniform float iAngle; // Passed in radians from Python

            #define t iTime*2.

            vec2 ran(vec2 uv) {
                uv *= vec2(dot(uv,vec2(127.1,311.7)),dot(uv,vec2(227.1,521.7)) );
                return 1.0-fract(tan(cos(uv)*123.6)*3533.3)*fract(tan(cos(uv)*123.6)*3533.3);
            }

            vec2 pt(vec2 id) {
                return sin(t*(ran(id+.5)-0.5)+ran(id-20.1)*8.0)*0.5;
            }

            void main() {
                vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.x;
                vec2 off = iTime / vec2(50., 30.);
                uv += off;
                uv *= SIZE;

                vec2 gv = fract(uv) - 0.5;
                vec2 id = floor(uv);

                float mindist = 1e9;
                vec2 vorv;

                for(float i=-1.; i<=1.; i++) {
                    for(float j=-1.; j<=1.; j++) { 
                        vec2 offv = vec2(i, j);
                        float dist = length(gv + pt(id + offv) - offv);
                        if(dist < mindist){
                            mindist = dist;
                            vorv = (id + pt(id + offv) + offv) / SIZE - off;
                        }
                    }
                }

                // Apply rotation for the color direction
                float s = sin(iAngle);
                float c = cos(iAngle);
                mat2 rot = mat2(c, -s, s, c);
                vec2 rotatedVorv = rot * vorv;

                
                // Mix using the x-component of the rotated vector
                vec3 col = mix(col1, col2, clamp(rotatedVorv.x * 3.0, -1., 1.) * 0.5 + 0.5);
                
                float shading = smoothstep(0.8, 0.012, mindist * 0.25);
                col *= (1.85 + 0.15 * shading);
                
                fragColor = vec4(col, 1.0);
            }
        '''
    )

    fbo = ctx.framebuffer(color_attachments=[ctx.texture((width, height), 3)])
    fbo.use()

    vertices = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype='f4')
    vao = ctx.simple_vertex_array(prog, ctx.buffer(vertices), 'in_vert')

    # Set Uniforms
    prog['iResolution'].value = (width, height)
    prog['iTime'].value = timestamp
    prog['SIZE'].value = scale
    prog['col1'].value = tuple(col1_vec)
    prog['col2'].value = tuple(col2_vec)
    # Convert degrees to radians for the GPU
    prog['iAngle'].value = np.radians(angle_degrees)

    ctx.clear()
    vao.render(moderngl.TRIANGLE_STRIP)

    raw_data = fbo.read(components=3)
    img_patch = Image.frombytes('RGB', (width, height), raw_data)
    img_patch = img_patch.transpose(Image.FLIP_TOP_BOTTOM)

    if image.mode == 'RGBA':
        img_patch = img_patch.convert('RGBA')

    image.paste(img_patch, right_corner)
    ctx.release()


def paint_random_voronoid(
        img: Image.Image,
        primary_color: Union[ColorUnion, Random] = Random,
        right_corner: Union[Tuple[int, int], Default, Random] = Default,
        size: Union[Tuple[int, int], Default, Random] = Default,
        color_a: Optional[ColorUnion] = Default,
        color_b: Optional[ColorUnion] = Default,
        timestamp: Optional[float] = Default,
        scale: Optional[float] = Default,
        angle_degrees: Optional[float] = Random
) -> dict[str, Any]:
    passed_values = clean_passed_parameters({
        "right_corner": right_corner,
        "size": size,
        "color_a": color_a,
        "color_b": color_b,
        "timestamp": timestamp,
        "scale": scale,
        "angle_degrees": angle_degrees,
    })

    random_parameters = generate_random_voronoid_parameters(
        img,
        primary_color,
        right_corner,
        size,
        angle_degrees
    )

    parameters = random_parameters | passed_values
    paint_voronoid(img, **parameters)

    return parameters
