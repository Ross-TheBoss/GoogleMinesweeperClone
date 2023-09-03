#version 150 core
in vec3 translate;
in vec4 colors;
in vec3 tex_coords;
in vec2 scale;
in vec3 position;
in float rotation;

out vec4 vertex_colors;
out vec3 texture_coords;
out vec2 tile_dim;

uniform WindowBlock
{
    mat4 projection;
    mat4 view;
} window;

uniform float tile_size;
uniform vec2 texture_dimensions;

mat4 m_scale = mat4(1.0);
mat4 m_rotation = mat4(1.0);
mat4 m_translate = mat4(1.0);

void main()
{
    m_scale[0][0] = scale.x;
    m_scale[1][1] = scale.y;
    m_translate[3][0] = translate.x;
    m_translate[3][1] = translate.y;
    m_translate[3][2] = translate.z;
    m_rotation[0][0] =  cos(-radians(rotation));
    m_rotation[0][1] =  sin(-radians(rotation));
    m_rotation[1][0] = -sin(-radians(rotation));
    m_rotation[1][1] =  cos(-radians(rotation));

    gl_Position = window.projection * window.view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

    vertex_colors = colors;
    texture_coords = tex_coords;

    tile_dim = vec2(tile_size / texture_dimensions.x, tile_size / texture_dimensions.y);
}