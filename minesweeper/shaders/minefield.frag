#version 150 core
#define PI 3.141592

in vec4 vertex_colors;
in vec3 texture_coords;
in vec2 tile_dim;

out vec4 final_colors;

uniform sampler2D background_texture;
uniform sampler2D foreground_texture;

void main()
{
    vec4 background_colors = texture(background_texture, vec2(texture_coords.xy));
    vec4 foreground_colors = texture(foreground_texture, vec2(texture_coords.xy));

    float within_circle = step(0.3, distance(mod(texture_coords.xy / tile_dim.xy, 1.0), vec2(0.5)));

    final_colors = mix(foreground_colors, background_colors, within_circle) * vertex_colors;
}