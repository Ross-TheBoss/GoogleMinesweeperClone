#version 150 core
#define PRECISION 0.001

in vec4 vertex_colors;
in vec3 texture_coords;
in vec2 texture_outline_dim;
in vec2 tile_dim;

out vec4 final_colors;

uniform sampler2D sprite_texture;
uniform vec4 outline_color;
uniform vec4 color1;
uniform vec4 color2;
uniform vec4 flood_color1;
uniform vec4 flood_color2;
uniform vec4 cleared_color;

float texture_mask (vec2 offset){
    /*
    if (
        texture_coords.x + offset.x <= PRECISION ||
        texture_coords.x + offset.x >= 1. - PRECISION ||
        texture_coords.y + offset.y <= PRECISION ||
        texture_coords.y + offset.y >= 1. - PRECISION
    ) {
        return 0.;
    } else {
        return texture(sprite_texture, vec2(texture_coords.xy) + offset).a;
    }
    */

    float within_bounds = (
        step(PRECISION, texture_coords.x + offset.x) *
        step(texture_coords.x + offset.x, 1. - PRECISION) *
        step(PRECISION, texture_coords.y + offset.y) *
        step(texture_coords.y + offset.y, 1. - PRECISION)
    );

    return within_bounds * texture(sprite_texture, vec2(texture_coords.xy) + offset).a;
}

float flood_wave(float tex_coord, float offset){
    // -1 < x < 2
    float intensity = max(0.0, tex_coord + (offset * 4.0) - 1.0);
    return min(intensity, abs(mod(intensity, 2.0) - 1.0) + 1.0);
}

void main()
{
    vec4 texture_colors = texture(sprite_texture, vec2(texture_coords.xy));

    // show_texture = 1.0 if texture_color.a > 0.0 else 0.0
    float show_texture = step(PRECISION, texture_colors.a);

    float show_outline = min(1.0,
        step(PRECISION, texture_mask(vec2(texture_outline_dim.x, -texture_outline_dim.y))) +
        step(PRECISION, texture_mask(vec2(-texture_outline_dim.x, texture_outline_dim.y))) +
        step(PRECISION, texture_mask(vec2(-texture_outline_dim.x, -texture_outline_dim.y))) +
        step(PRECISION, texture_mask(vec2(texture_outline_dim.x, texture_outline_dim.y)))
    );

    // (outline_color * show_outline) if show_texture == 1.0 else texture_colors
    // vec4(0.67, 0.84, 0.32, 1.0);
    // vec4(0.64, 0.82, 0.29, 1.0)

    vec4 final_color1 = mix(color1, vec4(flood_color1.rgb, 1.0),
                            flood_wave(texture_coords.y, flood_color1.a));
    vec4 final_color2 = mix(color2, vec4(flood_color2.rgb, 1.0),
                            flood_wave(texture_coords.y, flood_color1.a));

    vec4 checkerboard_color = mix(final_color1, final_color2,
        mod(mod(floor(texture_coords.x / tile_dim.x), 2.) +
            mod(floor((1. - texture_coords.y) / tile_dim.y), 2.),
            2.)
    );

    final_colors = mix((outline_color * show_outline), mix(checkerboard_color, cleared_color, cleared_color.a), show_texture) * vertex_colors;
}