import moderngl
import numpy as np
from PIL import Image


def render_grid_shader_to_pil(width=1920, height=1080, timestamp=1.0):
    # 1. Initialize Standalone Context
    ctx = moderngl.create_context(standalone=True)

    # 2. The Shader Program
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

            #define UI0 1597334673U
            #define UI1 3812015801U
            #define UI2 uvec2(UI0, UI1)
            #define UIF (1.0 / float(0xffffffffU))
            #define SCALE 12.
            #define PURPLE (vec3(92., 25., 226.)/255.)

            const vec3[3] colors = vec3[](
                vec3(92., 197., 187.)/255., // cyan
                vec3(240., 221., 55.)/255., // yellow
                vec3(253., 87., 59.)/255.  // red
            );

            float hash12(vec2 p) {
                uvec2 q = uvec2(ivec2(p)) * UI2;
                uint n = (q.x ^ q.y) * UI0;
                return float(n) * UIF;
            }

            float sdBox( in vec2 p, in vec2 b ) {
                vec2 d = abs(p)-b;
                return length(max(d,vec2(0))) + min(max(d.x,d.y),0.0);
            }

            void main() {
                vec2 uv = gl_FragCoord.xy / iResolution.y;
                vec2 auv = uv * SCALE;
                vec2 _auv = fract(auv);
                vec2 buv = uv * SCALE - .5;
                vec2 _buv = fract(buv);
                float t = iTime;

                vec3 col = vec3(0.);

                float ah = hash12(floor(auv + 647.));
                float abox = smoothstep(.1, .05, sdBox(_auv - .5, vec2(.305)) - .12)
                    * (.75 + .25 * sin(t + 588. * ah)) * 1.1 + .1;

                // Note: Indexing must be cast to int
                int idxA = int(3. * hash12(floor(auv) + 378. + t * .4));
                vec3 aboxCol = colors[idxA % 3];

                float bh = hash12(floor(buv + 879.));
                float bbox = smoothstep(.1, .05, sdBox(_buv - .5, vec2(.305)) - .12)
                    * (.75 + .25 * sin(t + 261. * bh)) * 1.1 + .1;

                int idxB = int(3. * hash12(floor(buv) + 117. - t * .8));
                vec3 bboxCol = colors[idxB % 3];

                col = mix(col, vec3(abox) * aboxCol, abox);
                col = mix(col, vec3(bbox) * bboxCol, .5 * bbox);
                col = mix(col * 1.25, PURPLE, 1. - (abox + bbox) * .5);

                fragColor = vec4(col, 1.0);
            }
        '''
    )

    # 3. Setup Surface
    fbo = ctx.framebuffer(color_attachments=[ctx.texture((width, height), 3)])
    fbo.use()

    # 4. Quad Geometry
    vertices = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype='f4')
    vao = ctx.simple_vertex_array(prog, ctx.buffer(vertices), 'in_vert')

    # 5. Set Uniforms
    prog['iResolution'].value = (width, height)
    prog['iTime'].value = timestamp

    # 6. Render and Export
    ctx.clear()
    vao.render(moderngl.TRIANGLE_STRIP)

    raw_data = fbo.read(components=3)
    img = Image.frombytes('RGB', (width, height), raw_data)

    # Flip for PIL
    return img.transpose(Image.FLIP_TOP_BOTTOM)


# --- Generate Example ---
if __name__ == "__main__":
    result = render_grid_shader_to_pil(timestamp=12.4)
    result.show()
    result.save("geometric_grid.png")
