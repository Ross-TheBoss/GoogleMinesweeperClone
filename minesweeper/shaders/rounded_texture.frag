#version 150 core
#define THRESHOLD 0.0001

in vec4 vertex_colors;
in vec3 texture_coords;

out vec4 final_colors;

uniform sampler2D sprite_texture;
uniform vec2 texture_dimensions;

float roundedRectMask(vec2 p, vec2 b, float r){
    return 1.0 - (
       step(r, distance(p, b - vec2(r))) *
       step(r, distance(p, vec2(b.x-r, r))) *
       step(r, distance(p, vec2(r, b.y-r))) *
       step(r, distance(p, vec2(r))) *
       step((b.x * 0.5) - r, distance(b.x * 0.5, p.x)) *
       step((b.y * 0.5) - r, distance(b.y * 0.5, p.y))
    );
}

void main()
{
    vec4 texture_colors = texture(sprite_texture, vec2(texture_coords.xy));

    float mask = roundedRectMask(texture_coords.xy * texture_dimensions.xy, texture_dimensions.xy, 8.0);

    final_colors = mask * texture_colors * vertex_colors;
}