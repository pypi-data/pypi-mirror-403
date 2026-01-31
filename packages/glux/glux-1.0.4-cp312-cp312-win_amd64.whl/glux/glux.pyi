
from typing import overload, Tuple, Callable, List, Optional

class imgui:

    def begin(name: str, p_open: bool = True, flags: int = 0) -> Tuple[bool, bool]: ...
    def end() -> None: ...

    def text(text: str) -> None: ...
    def text_colored(color: imgui.Vec4, text: str) -> None: ...

    def push_style_color(idx: int, color: imgui.Vec4) -> None: ...
    def push_style_var_float(idx: int, value: float) -> None: ...
    def push_style_var_vec2(idx: int, value: imgui.Vec2) -> None: ...
    def pop_style_var(count: int = 1) -> None: ...
    def pop_style_color(count: int = 1) -> None: ...
    def push_item_width(width: float) -> None: ...
    def pop_item_width() -> None: ...
    def set_next_item_width(width: float) -> None: ...
    def indent(indent_w: float) -> None: ...
    def unindent() -> None: ...
    def begin_group() -> None: ...
    def end_group() -> None: ...

    def same_line(x_offset: float = 0.0, spacing: float = 0.0) -> None: ...
    def dummy(size: imgui.Vec2) -> None: ...
    def separator() -> None: ...
    def spacing() -> None: ...

    def set_next_window_pos(pos: imgui.Vec2, cond: int = 0, pivot: imgui.Vec2 = imgui.Vec2(0.0, 0.0)) -> None: ...
    def set_next_window_size(size: imgui.Vec2, cond: int = 0) -> None: ...
    def set_next_window_size_constraints(size_min: imgui.Vec2, size_max: imgui.Vec2) -> None: ...
    def set_next_window_content_size(size: imgui.Vec2) -> None: ...
    def set_next_window_collapsed(collapsed: bool, cond: int = 0) -> None: ...
    def set_next_window_focus() -> None: ...

    def set_cursor_pos(local_pos: imgui.Vec2) -> None: ...
    def set_cursor_screen_pos(screen_pos: imgui.Vec2) -> None: ...
    def set_item_default_focus() -> None: ...

    def button(label: str, size: imgui.Vec2 = imgui.Vec2(0.0, 0.0)) -> bool: ...
    def color_button(desc_id: str, color: imgui.Vec4, flags: int = 0, size: imgui.Vec2 = imgui.Vec2(0.0, 0.0)) -> bool: ...
    def small_button(label: str) -> bool: ...
    def arrow_button(str_id: str, dir: int) -> bool: ...
    def invisible_button(str_id: str, size: imgui.Vec2, flags: int = 0) -> bool: ...
    def checkbox(label: str, value: bool) -> bool: ...

    def radio_button(label: str, current_value: int, button_value: int) -> Tuple[bool, int]: ...

    def input_text(label: str, text: str, flags: int = 0) -> Tuple[bool, str]: ...
    def input_text_with_hint(label: str, hint: str, text: str, flags: int = 0) -> Tuple[bool, str]: ...
    def input_text_multiline(label: str, text: str, size: imgui.Vec2 = imgui.Vec2(0.0, 0.0), flags: int = 0) -> Tuple[bool, str]: ...

    def input_float(label: str, value: float, step: float = 0.0, step_fast: float = 0.0, format: str = "%.3f") -> Tuple[bool, float]: ...
    def input_int(label: str, value: int, step: int = 1, step_fast: int = 100) -> Tuple[bool, int]: ...

    def slider_float(label: str, value: float, min: float, max: float, format: str = "%.3f") -> Tuple[bool, float]: ...
    def slider_int(label: str, value: int, min: int, max: int) -> Tuple[bool, int]: ...

    def drag_float(label: str, value: float, speed: float = 1.0, min: float = 0.0, max: float = 0.0, format: str = "%.3f", flags: int = 0) -> Tuple[bool, float]: ...
    def drag_float2(label: str, value: Tuple[float, float], speed: float = 1.0, min: float = 0.0, max: float = 0.0, format: str = "%.3f", flags: int = 0) -> Tuple[bool, Tuple[float, float]]: ...
    def drag_float3(label: str, value: Tuple[float, float, float], speed: float = 1.0, min: float = 0.0, max: float = 0.0, format: str = "%.3f", flags: int = 0) -> Tuple[bool, Tuple[float, float, float]]: ...
    def drag_float4(label: str, value: Tuple[float, float, float, float], speed: float = 1.0, min: float = 0.0, max: float = 0.0, format: str = "%.3f", flags: int = 0) -> Tuple[bool, Tuple[float, float, float, float]]: ...

    def drag_int(label: str, value: int, speed: float = 1.0, min: int = 0, max: int = 0, format: str = "%d", flags: int = 0) -> Tuple[bool, int]: ...
    def drag_int2(label: str, value: Tuple[int, int], speed: float = 1.0, min: int = 0, max: int = 0, format: str = "%d", flags: int = 0) -> Tuple[bool, Tuple[int, int]]: ...
    def drag_int3(label: str, value: Tuple[int, int, int], speed: float = 1.0, min: int = 0, max: int = 0, format: str = "%d", flags: int = 0) -> Tuple[bool, Tuple[int, int, int]]: ...
    def drag_int4(label: str, value: Tuple[int, int, int, int], speed: float = 1.0, min: int = 0, max: int = 0, format: str = "%d", flags: int = 0) -> Tuple[bool, Tuple[int, int, int, int]]: ...

    def combo(label: str, current_item: int, items: List[str]) -> Tuple[bool, int]: ...

    def color_edit3(label: str, color: imgui.Vec4) -> Tuple[bool, imgui.Vec4]: ...
    def color_edit4(label: str, color: imgui.Vec4, flags: int = 0) -> Tuple[bool, imgui.Vec4]: ...
    def color_picker3(label: str, color: imgui.Vec4, flags: int = 0) -> Tuple[bool, imgui.Vec4]: ...
    def color_picker4(label: str, color: imgui.Vec4, flags: int = 0) -> Tuple[bool, imgui.Vec4]: ...

    def get_window_draw_list() -> imgui.DrawList: ...
    def get_background_draw_list() -> imgui.DrawList: ...
    def get_foreground_draw_list() -> imgui.DrawList: ...

    def get_main_viewport() -> Viewport: ...

    def image(texture_id: int, width: float, height: float, uv0: imgui.Vec2, uv1: imgui.Vec2) -> None: ...
    
    def calc_text_size(text: str) -> Tuple[float, float]: ...
    def get_available_region() -> Tuple[float, float]: ...

    def get_glyph_ranges_default() -> List[int]: ...
    def get_glyph_ranges_greek() -> List[int]: ...
    def get_glyph_ranges_korean() -> List[int]: ...
    def get_glyph_ranges_japanese() -> List[int]: ...
    def get_glyph_ranges_chinese_full() -> List[int]: ...
    def get_glyph_ranges_chinese_simplified_common() -> List[int]: ...
    def get_glyph_ranges_cyrillic() -> List[int]: ...
    def get_glyph_ranges_thai() -> List[int]: ...
    def get_glyph_ranges_vietnamese() -> List[int]: ...

    def push_font(font: imgui.Font) -> None: ...
    def pop_font() -> None: ...

    def begin_table(str_id: str, column_count: int, flags: int = 0, outer_size: imgui.Vec2 = imgui.Vec2(0.0, 0.0), inner_width: float = 0.0) -> bool: ...
    def end_table() -> None: ...

    def table_next_row(row_flags: int = 0, min_row_height: float = 0.0) -> bool: ...
    def table_next_column() -> bool: ...
    def table_set_column_index(column_n: int) -> None: ...
    def table_setup_column(label: str, flags: int = 0, init_width_or_weight: float = 0.0, user_id: int = 0) -> None: ...
    def table_setup_scroll_freeze(cols: int, rows: int) -> None: ...
    def table_headers_row() -> None: ...
    def table_header(label: str) -> None: ...

    def table_get_sort_specs() -> List[Tuple[int, int, int]]: ...
    def table_get_column_count() -> int: ...
    def table_get_column_index() -> int: ...
    def table_get_row_index() -> int: ...
    def table_get_column_flags(column_n: int = -1) -> int: ...
    def table_set_column_enabled(column_n: int, enabled: bool) -> None: ...
    def table_set_bg_color(target: int, color: int, column_n: int = -1) -> None: ...

    def tree_node(label: str) -> bool: ...
    def tree_node_ex(label: str, flags: int = 0) -> bool: ...
    def tree_pop() -> None: ...
    def collapsing_header(label: str, flags: int = 0) -> bool: ...
    def set_next_item_open(is_open: bool, cond: int = 0) -> None: ...
    def tree_push(str_id: str) -> None: ...
    def get_tree_node_to_label_spacing() -> float: ...

    def begin_menu_bar() -> bool: ...
    def end_menu_bar() -> None: ...
    def begin_main_menu_bar() -> bool: ...
    def end_main_menu_bar() -> None: ...
    def begin_menu(label: str, enabled: bool = True) -> bool: ...
    def end_menu() -> None: ...
    def menu_item(label: str, shortcut: str = "", selected: bool = False, enabled: bool = True) -> bool: ...

    def open_popup(str_id: str, flags: int = 0) -> None: ...
    def begin_popup(str_id: str, flags: int = 0) -> bool: ...
    def begin_popup_modal(name: str, p_open: Optional[bool] = None, flags: int = 0) -> bool: ...
    def end_popup() -> None: ...
    def begin_popup_context_item(str_id: str = "", flags: int = 0) -> bool: ...
    def begin_popup_context_window(str_id: str = "", flags: int = 0) -> bool: ...
    def begin_popup_context_void(str_id: str = "", flags: int = 0) -> bool: ...
    def is_popup_open(str_id: str, flags: int = 0) -> bool: ...

    def selectable(label: str, selected: bool = False, flags: int = 0, size: imgui.Vec2 = imgui.Vec2(0.0, 0.0)) -> bool: ...

    def is_item_hovered(flags: int = 0) -> bool: ...
    def is_item_active() -> bool: ...
    def is_item_focused() -> bool: ...
    def is_item_clicked(mouse_button: int = 0) -> bool: ...
    def is_item_visible() -> bool: ...
    def is_item_edited() -> bool: ...
    def is_item_activated() -> bool: ...
    def is_item_deactivated() -> bool: ...
    def is_item_deactivated_after_edit() -> bool: ...
    def is_item_toggled_open() -> bool: ...
    def get_item_rect_min() -> Tuple[float, float]: ...
    def get_item_rect_max() -> Tuple[float, float]: ...
    def get_item_rect_size() -> Tuple[float, float]: ...

    def is_window_focused(flags: int = 0) -> bool: ...
    def is_window_hovered(flags: int = 0) -> bool: ...

    def is_mouse_down(button: int = 0) -> bool: ...
    def is_mouse_clicked(button: int = 0, repeat: bool = False) -> bool: ...
    def is_mouse_released(button: int = 0) -> bool: ...
    def is_mouse_double_clicked(button: int = 0) -> bool: ...
    def get_mouse_pos() -> Tuple[float, float]: ...
    def get_mouse_delta() -> Tuple[float, float]: ...
    def get_mouse_drag_delta(button: int = 0, lock_threshold: float = -1.0) -> Tuple[float, float]: ...
    def reset_mouse_drag_delta(button: int = 0) -> None: ...
    def is_mouse_hovering_rect(min: imgui.Vec2, max: imgui.Vec2, clip: bool = True) -> bool: ...
    def is_mouse_pos_valid(pos: Tuple[float, float] = (0.0, 0.0)) -> bool: ...

    def is_key_down(key: int) -> bool: ...
    def is_key_pressed(key: int, repeat: bool = True) -> bool: ...
    def is_key_released(key: int) -> bool: ...
    def get_key_pressed_amount(key: int, repeat_delay: float, rate: float) -> int: ...

    def set_keyboard_focus_here(offset: int = 0) -> None: ...

    def get_time() -> float: ...
    def get_frame_count() -> int: ...

    def get_frame_height() -> float: ...
    def get_frame_height_with_spacing() -> float: ...

    def get_display_size() -> Tuple[float, float]: ...
    def get_display_framebuffer_scale() -> Tuple[float, float]: ...

    def get_cursor_pos() -> Tuple[float, float]: ...
    def get_cursor_start_pos() -> Tuple[float, float]: ...
    def get_cursor_screen_pos() -> Tuple[float, float]: ...
    def get_text_line_height() -> float: ...
    def get_text_line_height_with_spacing() -> float: ...

    def get_color_u32(col: imgui.Vec4) -> int: ...
    def get_color_u32_indexed(idx: int, alpha_mul: float = 1.0) -> int: ...

    def get_font_size() -> float: ...
    def get_font_tex_uv_white_pixel() -> Tuple[float, float]: ...
    def get_style() -> imgui.Style: ...

    def get_clipboard_text() -> str: ...
    def set_clipboard_text(text: str) -> None: ...

    def drawlist_add_line(drawlist: imgui.DrawList, p1: imgui.Vec2, p2: imgui.Vec2, col: int, thickness: float = 1.0) -> None: ...
    def drawlist_add_rect(drawlist: imgui.DrawList, p_min: imgui.Vec2, p_max: imgui.Vec2, col: int, rounding: float = 0.0, flags: int = 0, thickness: float = 1.0) -> None: ...
    def drawlist_add_rect_filled(drawlist: imgui.DrawList, p_min: imgui.Vec2, p_max: imgui.Vec2, col: int, rounding: float = 0.0, flags: int = 0) -> None: ...
    def drawlist_add_circle(drawlist: imgui.DrawList, center: imgui.Vec2, radius: float, col: int, num_segments: int = 0, thickness: float = 1.0) -> None: ...
    def drawlist_add_circle_filled(drawlist: imgui.DrawList, center: imgui.Vec2, radius: float, col: int, num_segments: int = 0) -> None: ...
    def drawlist_add_text(drawlist: imgui.DrawList, pos: imgui.Vec2, col: int, text: str) -> None: ...
    def drawlist_add_triangle(drawlist: imgui.DrawList, p1: imgui.Vec2, p2: imgui.Vec2, p3: imgui.Vec2, col: int, thickness: float = 1.0) -> None: ...
    def drawlist_add_triangle_filled(drawlist: imgui.DrawList, p1: imgui.Vec2, p2: imgui.Vec2, p3: imgui.Vec2, col: int) -> None: ...
    def drawlist_add_image(drawlist: imgui.DrawList, texture_id: int, p_min: imgui.Vec2, p_max: imgui.Vec2,
                        uv_min: imgui.Vec2 = ..., uv_max: imgui.Vec2 = ..., col: int = ...) -> None: ...

    class Vec2:

        def __init__(self, x: float, y: float) -> imgui.Vec2: ...
        x: int
        y: int

    class Vec4:

        def __init__(self, x: float, y: float, z: float, w: float) -> imgui.Vec4: ...
        x: int
        y: int
        z: int
        w: int

    class Color:

        r: float
        g: float
        b: float
        a: float
        value: imgui.Vec4
        
        @overload
        def __init__(self, r: float, g: float, b: float, a: float = 1.0) -> imgui.Color: ...
        
        @overload
        def __init__(self, vec4: imgui.Vec4) -> imgui.Color: ...
        
        def to_vec4(self) -> imgui.Vec4: ...
        

    class DrawList:
        flags: int

        def add_line(self, p1: imgui.Vec2, p2: imgui.Vec2, color: imgui.Color,
                    thickness: float = 1.0) -> None: ...

        def add_rect(self, p_min: imgui.Vec2, p_max: imgui.Vec2, color: imgui.Color,
                    rounding: float = 0.0, flags: int = 0,
                    thickness: float = 1.0) -> None: ...

        def add_rect_filled(self, p_min: imgui.Vec2, p_max: imgui.Vec2, color: imgui.Color,
                            rounding: float = 0.0, flags: int = 0) -> None: ...

        def add_circle(self, center: imgui.Vec2, radius: float, color: imgui.Color,
                    num_segments: int = 0, thickness: float = 1.0) -> None: ...

        def add_circle_filled(self, center: imgui.Vec2, radius: float, color: imgui.Color,
                            num_segments: int = 0) -> None: ...

        def add_triangle(self, p1: imgui.Vec2, p2: imgui.Vec2, p3: imgui.Vec2, color: imgui.Color,
                        thickness: float = 1.0) -> None: ...

        def add_triangle_filled(self, p1: imgui.Vec2, p2: imgui.Vec2, p3: imgui.Vec2,
                                color: imgui.Color) -> None: ...

        def add_ngon(self, center: imgui.Vec2, radius: float, color: imgui.Color,
                    num_segments: int, thickness: float = 1.0) -> None: ...

        def add_ngon_filled(self, center: imgui.Vec2, radius: float, color: imgui.Color,
                            num_segments: int) -> None: ...

        def add_quad(self, p1: imgui.Vec2, p2: imgui.Vec2, p3: imgui.Vec2, p4: imgui.Vec2,
                    color: imgui.Color, thickness: float = 1.0) -> None: ...

        def add_quad_filled(self, p1: imgui.Vec2, p2: imgui.Vec2, p3: imgui.Vec2, p4: imgui.Vec2,
                            color: imgui.Color) -> None: ...

        def add_text(self, pos: imgui.Vec2, color: imgui.Color, text: str) -> None: ...

        def add_bezier_cubic(self, p1: imgui.Vec2, p2: imgui.Vec2, p3: imgui.Vec2, p4: imgui.Vec2,
                            color: imgui.Color, thickness: float,
                            num_segments: int = 0) -> None: ...

        def add_bezier_quadratic(self, p1: imgui.Vec2, p2: imgui.Vec2, p3: imgui.Vec2,
                                color: imgui.Color, thickness: float,
                                num_segments: int = 0) -> None: ...

        def push_clip_rect(self, min: imgui.Vec2, max: imgui.Vec2,
                        intersect_with_current: bool = False) -> None: ...
        def pop_clip_rect(self) -> None: ...
        def get_clip_rect_min(self) -> imgui.Vec2: ...
        def get_clip_rect_max(self) -> imgui.Vec2: ...

        def push_texture_id(self, texture_id: int) -> None: ...
        def pop_texture_id(self) -> None: ...

        def path_clear(self) -> None: ...
        def path_line_to(self, pos: imgui.Vec2) -> None: ...
        def path_fill_convex(self) -> None: ...
        def path_stroke(self, color: imgui.Color, flags: int = 0,
                        thickness: float = 1.0) -> None: ...

        def clone_output(self) -> imgui.DrawList: ...

    class Viewport:

        id: int
        flags: int
        platform_handle: int
        platform_handle_raw: int

        pos: imgui.Vec2
        size: imgui.Vec2
        work_pos: imgui.Vec2
        work_size: imgui.Vec2

        def get_center(self) -> imgui.Vec2: ...
        def get_work_center(self) -> imgui.Vec2: ...

    class FontGlyph:

        @property
        def colored(self) -> bool: ...
        @colored.setter
        def colored(self, value: bool) -> None: ...

        @property
        def visible(self) -> bool: ...
        @visible.setter
        def visible(self, value: bool) -> None: ...

        @property
        def codepoint(self) -> int: ...
        @codepoint.setter
        def codepoint(self, value: int) -> None: ...

        advance_x: float
        x0: float
        y0: float
        x1: float
        y1: float
        u0: float
        v0: float
        u1: float
        v1: float

    class FontGlyphRangesBuilder:

        def __init__(self) -> None: ...

        def clear(self) -> None: ...
        def get_bit(self, c: int) -> bool: ...
        def set_bit(self, c: int) -> None: ...
        def add_char(self, c: int) -> None: ...
        def add_text(self, text: str, text_end: Optional[str] = None) -> None: ...
        def add_ranges(self, ranges: List[int]) -> None: ...

        def build_ranges(self) -> List[int]: ...

    class FontConfig:

        def __init__(self) -> None: ...

        font_data: Optional[bytes]
        font_data_size: int
        font_data_owned_by_atlas: bool
        merge_mode: bool
        pixel_snap_h: bool
        font_no: int
        oversample_h: int
        oversample_v: int
        size_pixels: float
        glyph_offset: imgui.Vec2
        glyph_ranges: Optional[List[int]]
        glyph_min_advance_x: float
        glyph_max_advance_x: float
        glyph_extra_advance_x: float
        font_builder_flags: int
        rasterizer_multiply: float
        rasterizer_density: float
        ellipsis_char: int
        dst_font: Optional[imgui.Font]

        @property
        def name(self) -> str: ...
        @name.setter
        def name(self, val: str) -> None: ...

    class Font:

        def find_glyph(self, c: int) -> imgui.FontGlyph: ...
        def find_glyph_no_fallback(self, c: int) -> imgui.FontGlyph: ...
        def get_char_advance(self, c: int) -> float: ...
        def is_loaded(self) -> bool: ...
        def get_debug_name(self) -> str: ...
        def calc_text_size_a(
            self,
            size: float,
            max_width: float,
            wrap_width: float,
            text: str,
            text_end: Optional[str] = None
        ) -> imgui.Vec2: ...
        def render_char(
            self,
            draw_list: imgui.DrawList,
            size: float,
            pos: imgui.Vec2,
            col: int,
            c: int,
            clip_rect: Optional[imgui.Vec4] = None
        ) -> None: ...
        def render_text(
            self,
            draw_list: imgui.DrawList,
            size: float,
            pos: imgui.Vec2,
            col: int,
            clip_rect: Optional[imgui.Vec4],
            text_begin: str,
            text_end: str,
            wrap_width: float = 0.0,
            cpu_fine_clip: bool = False
        ) -> None: ...

        fallback_advance_x: float
        font_size: float
        fallback_glyph: imgui.FontGlyph
        fallback_char: int
        scale: float
        ascent: float
        descent: float
        ellipsis_char: int
        ellipsis_char_count: int
        ellipsis_width: float
        ellipsis_char_step: float
        metrics_total_surface: float
        dirty_lookup_tables: bool

    class FontAtlasCustomRect:

        def __init__(self) -> None: ...

        x: int
        y: int
        width: int
        height: int

        @property
        def glyph_id(self) -> int: ...
        @glyph_id.setter
        def glyph_id(self, val: int) -> None: ...

        @property
        def glyph_colored(self) -> bool: ...
        @glyph_colored.setter
        def glyph_colored(self, val: bool) -> None: ...

        glyph_advance_x: float
        glyph_offset: imgui.Vec2
        font: Optional[imgui.Font]

        def is_packed(self) -> bool: ...


    class FontAtlas:

        def __init__(self) -> None: ...

        def add_font(self, font_cfg: imgui.FontConfig) -> imgui.Font: ...
        def add_font_default(self, font_cfg: Optional[imgui.FontConfig] = None) -> imgui.Font: ...
        def add_font_from_file_ttf(
            self,
            filename: str,
            size_pixels: float,
            font_cfg: Optional[imgui.FontConfig] = None,
            glyph_ranges: Optional[List[int]] = None
        ) -> imgui.Font: ...
        def add_font_from_memory_ttf(
            self,
            font_data: bytes,
            size_pixels: float,
            font_cfg: Optional[imgui.FontConfig] = None,
            glyph_ranges: Optional[List[int]] = None
        ) -> imgui.Font: ...
        def add_font_from_memory_compressed_ttf(
            self,
            data: bytes,
            size_pixels: float,
            font_cfg: Optional[imgui.FontConfig] = None,
            glyph_ranges: Optional[List[int]] = None
        ) -> imgui.Font: ...
        def add_font_from_memory_compressed_base85_ttf(
            self,
            base85: str,
            size_pixels: float,
            font_cfg: Optional[imgui.FontConfig] = None,
            glyph_ranges: Optional[List[int]] = None
        ) -> imgui.Font: ...

        def get_glyph_ranges_default(self) -> List[int]: ...
        def get_glyph_ranges_greek(self) -> List[int]: ...
        def get_glyph_ranges_korean(self) -> List[int]: ...
        def get_glyph_ranges_japanese(self) -> List[int]: ...
        def get_glyph_ranges_chinese_full(self) -> List[int]: ...
        def get_glyph_ranges_chinese_simplified_common(self) -> List[int]: ...
        def get_glyph_ranges_cyrillic(self) -> List[int]: ...
        def get_glyph_ranges_thai(self) -> List[int]: ...
        def get_glyph_ranges_vietnamese(self) -> List[int]: ...

        def get_tex_data_as_rgba32(self) -> bytes: ...
        def get_tex_data_as_alpha8(self) -> bytes: ...

        def is_built(self) -> bool: ...
        def set_tex_id(self, tex_id: int) -> None: ...
        def clear(self) -> None: ...
        def clear_fonts(self) -> None: ...
        def clear_input_data(self) -> None: ...
        def clear_tex_data(self) -> None: ...
        def build(self) -> None: ...
        def add_custom_rect_regular(self, id: int, width: float, height: float, advance_x: float, offset: imgui.Vec2 = imgui.Vec2()) -> None: ...
        def add_custom_rect_font_glyph(self, font: imgui.Font, id: int, width: float, height: float, advance_x: float, offset: imgui.Vec2 = imgui.Vec2()) -> None: ...
        def get_custom_rect_by_index(self, index: int) -> imgui.FontAtlasCustomRect: ...

        flags: int
        tex_id: int
        tex_desired_width: int
        tex_glyph_padding: int
        user_data: int
        tex_width: int
        tex_height: int
        tex_uv_scale: imgui.Vec2
        tex_uv_white_pixel: imgui.Vec2
        fonts: List[imgui.Font]
        custom_rects: List[imgui.FontAtlasCustomRect]
        sources: List[imgui.FontConfig]
    
    class IO:
        
        display_size: imgui.Vec2
        delta_time: float
        ini_saving_rate: float
        font_global_scale: float
        display_framebuffer_scale: imgui.Vec2
        mouse_draw_cursor: bool
        mouse_wheel: float
        mouse_wheel_h: float
        key_ctrl: bool
        key_shift: bool
        key_alt: bool
        key_super: bool
        want_set_mouse_pos: bool

        config_flags: int
        backend_flags: int
        config_nav_swap_gamepad_buttons: bool
        config_nav_move_set_mouse_pos: bool
        config_nav_capture_keyboard: bool
        config_nav_escape_clear_focus_item: bool
        config_nav_escape_clear_focus_window: bool
        config_nav_cursor_visible_auto: bool
        config_nav_cursor_visible_always: bool

        config_input_trickle_event_queue: bool
        config_input_text_cursor_blink: bool
        config_input_text_enter_keep_active: bool
        config_drag_click_to_input_text: bool
        config_windows_resize_from_edges: bool
        config_windows_move_from_title_bar_only: bool
        config_scrollbar_scroll_by_page: bool

        mouse_double_click_time: float
        mouse_double_click_max_dist: float
        mouse_drag_threshold: float
        key_repeat_delay: float
        key_repeat_rate: float

        @property
        def framerate(self) -> float: ...
        @property
        def want_capture_mouse(self) -> bool: ...
        @property
        def want_capture_keyboard(self) -> bool: ...
        @property
        def want_text_input(self) -> bool: ...
        @property
        def nav_active(self) -> bool: ...
        @property
        def nav_visible(self) -> bool: ...

        @property
        def font_default(self) -> Optional[imgui.Font]: ...
        @font_default.setter
        def font_default(self, font: Optional[imgui.Font]) -> None: ...

        @property
        def fonts(self) -> imgui.FontAtlas: ...

        @property
        def mouse_down(self) -> List[bool]: ...
        @mouse_down.setter
        def mouse_down(self, value: List[bool]) -> None: ...

        @property
        def ini_filename(self) -> str: ...
        @ini_filename.setter
        def ini_filename(self, value: str) -> None: ...

        @property
        def log_filename(self) -> str: ...
        @log_filename.setter
        def log_filename(self, value: str) -> None: ...

    def get_io() -> imgui.IO: ...

    class Style:

        alpha: float
        disabled_alpha: float
        window_rounding: float
        window_border_size: float
        window_border_hover_padding: float
        child_rounding: float
        child_border_size: float
        popup_rounding: float
        popup_border_size: float
        frame_rounding: float
        frame_border_size: float
        indent_spacing: float
        columns_min_spacing: float
        scrollbar_size: float
        scrollbar_rounding: float
        grab_min_size: float
        grab_rounding: float
        log_slider_deadzone: float
        image_border_size: float
        tab_rounding: float
        tab_border_size: float
        tab_close_button_min_width_selected: float
        tab_close_button_min_width_unselected: float
        tab_bar_border_size: float
        tab_bar_overline_size: float
        table_angled_headers_angle: float
        tree_lines_size: float
        tree_lines_rounding: float
        separator_text_border_size: float
        mouse_cursor_scale: float
        curve_tessellation_tol: float
        circle_tessellation_max_error: float
        hover_stationary_delay: float
        hover_delay_short: float
        hover_delay_normal: float

        anti_aliased_lines: bool
        anti_aliased_lines_use_tex: bool
        anti_aliased_fill: bool

        mouse_draw_cursor: bool

        window_padding: imgui.Vec2
        window_min_size: imgui.Vec2
        window_title_align: imgui.Vec2
        frame_padding: imgui.Vec2
        item_spacing: imgui.Vec2
        item_inner_spacing: imgui.Vec2
        cell_padding: imgui.Vec2
        touch_extra_padding: imgui.Vec2
        table_angled_headers_text_align: imgui.Vec2
        button_text_align: imgui.Vec2
        selectable_text_align: imgui.Vec2
        separator_text_align: imgui.Vec2
        separator_text_padding: imgui.Vec2
        display_window_padding: imgui.Vec2
        display_safe_area_padding: imgui.Vec2

        window_menu_button_position: int
        color_button_position: int
        tree_lines_flags: int
        hover_flags_for_tooltip_mouse: int
        hover_flags_for_tooltip_nav: int

        @property
        def colors(self) -> List[imgui.Vec4]: ...
        @colors.setter
        def colors(self, value: List[imgui.Vec4]) -> None: ...

        def scale_all_sizes(self) -> None: ...

    def get_style() -> Style: ...

    class ButtonFlags:
        EnableNav: int
        MouseButtonLeft: int
        MouseButtonMask_: int
        MouseButtonMiddle: int
        MouseButtonRight: int
        None_: int

    class ChildFlags:
        AlwaysAutoResize: int
        AlwaysUseWindowPadding: int
        AutoResizeX: int
        AutoResizeY: int
        Borders: int
        FrameStyle: int
        None_: int
        ResizeX: int
        ResizeY: int

    class ColorEditFlags:
        AlphaBar: int
        AlphaMask_: int
        AlphaNoBg: int
        AlphaOpaque: int
        AlphaPreviewHalf: int
        DataTypeMask_: int
        DefaultOptions_: int
        DisplayHSV: int
        DisplayHex: int
        DisplayMask_: int
        DisplayRGB: int
        Float: int
        HDR: int
        InputHSV: int
        InputMask_: int
        InputRGB: int
        NoAlpha: int
        NoBorder: int
        NoDragDrop: int
        NoInputs: int
        NoLabel: int
        NoOptions: int
        NoPicker: int
        NoSidePreview: int
        NoSmallPreview: int
        NoTooltip: int
        None_: int
        PickerHueBar: int
        PickerHueWheel: int
        PickerMask_: int
        Uint8: int

    class ComboFlags:
        HeightLarge: int
        HeightLargest: int
        HeightMask_: int
        HeightRegular: int
        HeightSmall: int
        NoArrowButton: int
        NoPreview: int
        None_: int
        PopupAlignLeft: int
        WidthFitPreview: int

    class ConfigFlags:
        NavEnableGamepad: int
        NavEnableKeyboard: int
        NoKeyboard: int
        NoMouse: int
        NoMouseCursorChange: int
        None_: int

    class DragDropFlags:
        AcceptBeforeDelivery: int
        AcceptNoDrawDefaultRect: int
        AcceptNoPreviewTooltip: int
        AcceptPeekOnly: int
        None_: int
        PayloadAutoExpire: int
        PayloadNoCrossContext: int
        PayloadNoCrossProcess: int
        SourceAllowNullID: int
        SourceExtern: int
        SourceNoDisableHover: int
        SourceNoHoldToOpenOthers: int
        SourceNoPreviewTooltip: int

    class DrawFlags:
        Closed: int
        None_: int
        RoundCornersAll: int
        RoundCornersBottom: int
        RoundCornersBottomLeft: int
        RoundCornersBottomRight: int
        RoundCornersDefault_: int
        RoundCornersLeft: int
        RoundCornersMask_: int
        RoundCornersNone: int
        RoundCornersRight: int
        RoundCornersTop: int
        RoundCornersTopLeft: int
        RoundCornersTopRight: int

    class DrawListFlags:
        AllowVtxOffset: int
        AntiAliasedFill: int
        AntiAliasedLines: int
        AntiAliasedLinesUseTex: int
        None_: int

    class FocusedFlags:
        AnyWindow: int
        ChildWindows: int
        NoPopupHierarchy: int
        None_: int
        RootAndChildWindows: int
        RootWindow: int

    class FontAtlasFlags:
        NoBakedLines: int
        NoMouseCursors: int
        NoPowerOfTwoHeight: int
        None_: int

    class HoveredFlags:
        AllowWhenBlockedByActiveItem: int
        AllowWhenBlockedByPopup: int
        AllowWhenDisabled: int
        AllowWhenOverlapped: int
        AllowWhenOverlappedByItem: int
        AllowWhenOverlappedByWindow: int
        AnyWindow: int
        ChildWindows: int
        DelayNone: int
        DelayNormal: int
        DelayShort: int
        ForTooltip: int
        NoNavOverride: int
        NoPopupHierarchy: int
        NoSharedDelay: int
        None_: int
        RectOnly: int
        RootAndChildWindows: int
        RootWindow: int
        Stationary: int

    class InputFlags:
        None_: int
        Repeat: int
        RouteActive: int
        RouteAlways: int
        RouteFocused: int
        RouteFromRootWindow: int
        RouteGlobal: int
        RouteOverActive: int
        RouteOverFocused: int
        RouteUnlessBgFocused: int
        Tooltip: int

    class InputTextFlags:
        AllowTabInput: int
        AlwaysOverwrite: int
        AutoSelectAll: int
        CallbackAlways: int
        CallbackCharFilter: int
        CallbackCompletion: int
        CallbackEdit: int
        CallbackHistory: int
        CallbackResize: int
        CharsDecimal: int
        CharsHexadecimal: int
        CharsNoBlank: int
        CharsScientific: int
        CharsUppercase: int
        CtrlEnterForNewLine: int
        DisplayEmptyRefVal: int
        ElideLeft: int
        EnterReturnsTrue: int
        EscapeClearsAll: int
        NoHorizontalScroll: int
        NoUndoRedo: int
        None_: int
        ParseEmptyRefVal: int
        Password: int
        ReadOnly: int

    class ItemFlags:
        AllowDuplicateId: int
        AutoClosePopups: int
        ButtonRepeat: int
        NoNav: int
        NoNavDefaultFocus: int
        NoTabStop: int
        None_: int

    class MultiSelectFlags:
        BoxSelect1d: int
        BoxSelect2d: int
        BoxSelectNoScroll: int
        ClearOnClickVoid: int
        ClearOnEscape: int
        NoAutoClear: int
        NoAutoClearOnReselect: int
        NoAutoSelect: int
        NoRangeSelect: int
        NoSelectAll: int
        None_: int
        ScopeRect: int
        ScopeWindow: int
        SelectOnClick: int
        SelectOnClickRelease: int
        SingleSelect: int

    class PopupFlags:
        AnyPopup: int
        AnyPopupId: int
        AnyPopupLevel: int
        MouseButtonDefault_: int
        MouseButtonLeft: int
        MouseButtonMask_: int
        MouseButtonMiddle: int
        MouseButtonRight: int
        NoOpenOverExistingPopup: int
        NoOpenOverItems: int
        NoReopen: int
        None_: int

    class SelectableFlags:
        AllowDoubleClick: int
        AllowOverlap: int
        Disabled: int
        Highlight: int
        NoAutoClosePopups: int
        None_: int
        SpanAllColumns: int

    class SliderFlags:
        AlwaysClamp: int
        ClampOnInput: int
        ClampZeroRange: int
        InvalidMask_: int
        Logarithmic: int
        NoInput: int
        NoRoundToFormat: int
        NoSpeedTweaks: int
        None_: int
        WrapAround: int

    class TabBarFlags:
        AutoSelectNewTabs: int
        DrawSelectedOverline: int
        FittingPolicyDefault_: int
        FittingPolicyMask_: int
        FittingPolicyResizeDown: int
        FittingPolicyScroll: int
        NoCloseWithMiddleMouseButton: int
        NoTabListScrollingButtons: int
        NoTooltip: int
        None_: int
        Reorderable: int
        TabListPopupButton: int

    class TabItemFlags:
        Leading: int
        NoAssumedClosure: int
        NoCloseWithMiddleMouseButton: int
        NoPushId: int
        NoReorder: int
        NoTooltip: int
        None_: int
        SetSelected: int
        Trailing: int
        UnsavedDocument: int

    class TableColumnFlags:
        AngledHeader: int
        DefaultHide: int
        DefaultSort: int
        Disabled: int
        IndentDisable: int
        IndentEnable: int
        IsEnabled: int
        IsHovered: int
        IsSorted: int
        IsVisible: int
        NoClip: int
        NoHeaderLabel: int
        NoHeaderWidth: int
        NoHide: int
        NoReorder: int
        NoResize: int
        NoSort: int
        NoSortAscending: int
        NoSortDescending: int
        None_: int
        PreferSortAscending: int
        PreferSortDescending: int
        WidthFixed: int
        WidthStretch: int

    class TableFlags:
        Borders: int
        BordersH: int
        BordersInner: int
        BordersInnerH: int
        BordersInnerV: int
        BordersOuter: int
        BordersOuterH: int
        BordersOuterV: int
        BordersV: int
        ContextMenuInBody: int
        Hideable: int
        HighlightHoveredColumn: int
        NoBordersInBody: int
        NoBordersInBodyUntilResize: int
        NoClip: int
        NoHostExtendX: int
        NoHostExtendY: int
        NoKeepColumnsVisible: int
        NoPadInnerX: int
        NoPadOuterX: int
        NoSavedSettings: int
        None_: int
        PadOuterX: int
        PreciseWidths: int
        Reorderable: int
        Resizable: int
        RowBg: int
        ScrollX: int
        ScrollY: int
        SizingFixedFit: int
        SizingFixedSame: int
        SizingStretchProp: int
        SizingStretchSame: int
        SortMulti: int
        SortTristate: int
        Sortable: int

    class TableRowFlags:
        Headers: int
        None_: int

    class TreeNodeFlags:
        AllowOverlap: int
        Bullet: int
        CollapsingHeader: int
        DefaultOpen: int
        FramePadding: int
        Framed: int
        LabelSpanAllColumns: int
        Leaf: int
        NavLeftJumpsToParent: int
        NoAutoOpenOnLog: int
        NoTreePushOnOpen: int
        None_: int
        OpenOnArrow: int
        OpenOnDoubleClick: int
        Selected: int
        SpanAllColumns: int
        SpanAvailWidth: int
        SpanFullWidth: int
        SpanLabelWidth: int

    class WindowFlags:
        AlwaysAutoResize: int
        AlwaysHorizontalScrollbar: int
        AlwaysVerticalScrollbar: int
        HorizontalScrollbar: int
        MenuBar: int
        NoBackground: int
        NoBringToFrontOnFocus: int
        NoCollapse: int
        NoDecoration: int
        NoFocusOnAppearing: int
        NoInputs: int
        NoMouseInputs: int
        NoMove: int
        NoNav: int
        NoNavFocus: int
        NoNavInputs: int
        NoResize: int
        NoSavedSettings: int
        NoScrollWithMouse: int
        NoScrollbar: int
        NoTitleBar: int
        None_: int
        UnsavedDocument: int

    class DataType:
        Bool: int
        Double: int
        Float: int
        S16: int
        S32: int
        S64: int
        S8: int
        String: int
        U16: int
        U32: int
        U64: int
        U8: int

    class Dir:
        Down: int
        Left: int
        None_: int
        Right: int
        Up: int

    class SortDirection:
        Ascending: int
        Descending: int
        None_: int

    class Key:
        K_0: int
        K_1: int
        K_2: int
        K_3: int
        K_4: int
        K_5: int
        K_6: int
        K_7: int
        K_8: int
        K_9: int
        K_A: int
        K_Apostrophe: int
        K_AppBack: int
        K_AppForward: int
        K_B: int
        K_Backslash: int
        K_Backspace: int
        K_C: int
        K_CapsLock: int
        K_Comma: int
        K_D: int
        K_Delete: int
        K_DownArrow: int
        K_E: int
        K_End: int
        K_Enter: int
        K_Equal: int
        K_Escape: int
        K_F: int
        K_F1: int
        K_F10: int
        K_F11: int
        K_F12: int
        K_F13: int
        K_F14: int
        K_F15: int
        K_F16: int
        K_F17: int
        K_F18: int
        K_F19: int
        K_F2: int
        K_F20: int
        K_F21: int
        K_F22: int
        K_F23: int
        K_F24: int
        K_F3: int
        K_F4: int
        K_F5: int
        K_F6: int
        K_F7: int
        K_F8: int
        K_F9: int
        K_G: int
        K_GamepadBack: int
        K_GamepadDpadDown: int
        K_GamepadDpadLeft: int
        K_GamepadDpadRight: int
        K_GamepadDpadUp: int
        K_GamepadFaceDown: int
        K_GamepadFaceLeft: int
        K_GamepadFaceRight: int
        K_GamepadFaceUp: int
        K_GamepadL1: int
        K_GamepadL2: int
        K_GamepadL3: int
        K_GamepadLStickDown: int
        K_GamepadLStickLeft: int
        K_GamepadLStickRight: int
        K_GamepadLStickUp: int
        K_GamepadR1: int
        K_GamepadR2: int
        K_GamepadR3: int
        K_GamepadRStickDown: int
        K_GamepadRStickLeft: int
        K_GamepadRStickRight: int
        K_GamepadRStickUp: int
        K_GamepadStart: int
        K_GraveAccent: int
        K_H: int
        K_Home: int
        K_I: int
        K_Insert: int
        K_J: int
        K_K: int
        K_Keypad0: int
        K_Keypad1: int
        K_Keypad2: int
        K_Keypad3: int
        K_Keypad4: int
        K_Keypad5: int
        K_Keypad6: int
        K_Keypad7: int
        K_Keypad8: int
        K_Keypad9: int
        K_KeypadAdd: int
        K_KeypadDecimal: int
        K_KeypadDivide: int
        K_KeypadEnter: int
        K_KeypadEqual: int
        K_KeypadMultiply: int
        K_KeypadSubtract: int
        K_L: int
        K_LeftAlt: int
        K_LeftArrow: int
        K_LeftBracket: int
        K_LeftCtrl: int
        K_LeftShift: int
        K_LeftSuper: int
        K_M: int
        K_Menu: int
        K_Minus: int
        K_MouseLeft: int
        K_MouseMiddle: int
        K_MouseRight: int
        K_MouseWheelX: int
        K_MouseWheelY: int
        K_MouseX1: int
        K_MouseX2: int
        K_N: int
        K_NumLock: int
        K_O: int
        K_Oem102: int
        K_P: int
        K_PageDown: int
        K_PageUp: int
        K_Pause: int
        K_Period: int
        K_PrintScreen: int
        K_Q: int
        K_R: int
        K_RightAlt: int
        K_RightArrow: int
        K_RightBracket: int
        K_RightCtrl: int
        K_RightShift: int
        K_RightSuper: int
        K_S: int
        K_ScrollLock: int
        K_Semicolon: int
        K_Slash: int
        K_Space: int
        K_T: int
        K_Tab: int
        K_U: int
        K_UpArrow: int
        K_V: int
        K_W: int
        K_X: int
        K_Y: int
        K_Z: int
        Mod_Alt: int
        Mod_Ctrl: int
        Mod_Mask_: int
        Mod_None_: int
        Mod_Shift: int
        Mod_Super: int
        None_: int

    class Col:
        Border: int
        BorderShadow: int
        Button: int
        ButtonActive: int
        ButtonHovered: int
        CheckMark: int
        ChildBg: int
        DragDropTarget: int
        FrameBg: int
        FrameBgActive: int
        FrameBgHovered: int
        Header: int
        HeaderActive: int
        HeaderHovered: int
        InputTextCursor: int
        MenuBarBg: int
        ModalWindowDimBg: int
        NavCursor: int
        NavWindowingDimBg: int
        NavWindowingHighlight: int
        PlotHistogram: int
        PlotHistogramHovered: int
        PlotLines: int
        PlotLinesHovered: int
        PopupBg: int
        ResizeGrip: int
        ResizeGripActive: int
        ResizeGripHovered: int
        ScrollbarBg: int
        ScrollbarGrab: int
        ScrollbarGrabActive: int
        ScrollbarGrabHovered: int
        Separator: int
        SeparatorActive: int
        SeparatorHovered: int
        SliderGrab: int
        SliderGrabActive: int
        Tab: int
        TabDimmed: int
        TabDimmedSelected: int
        TabDimmedSelectedOverline: int
        TabHovered: int
        TabSelected: int
        TabSelectedOverline: int
        TableBorderLight: int
        TableBorderStrong: int
        TableHeaderBg: int
        TableRowBg: int
        TableRowBgAlt: int
        Text: int
        TextDisabled: int
        TextLink: int
        TextSelectedBg: int
        TitleBg: int
        TitleBgActive: int
        TitleBgCollapsed: int
        TreeLines: int
        WindowBg: int

    class StyleVar:
        Alpha: int
        ButtonTextAlign: int
        CellPadding: int
        ChildBorderSize: int
        ChildRounding: int
        DisabledAlpha: int
        FrameBorderSize: int
        FramePadding: int
        FrameRounding: int
        GrabMinSize: int
        GrabRounding: int
        ImageBorderSize: int
        IndentSpacing: int
        ItemInnerSpacing: int
        ItemSpacing: int
        PopupBorderSize: int
        PopupRounding: int
        ScrollbarRounding: int
        ScrollbarSize: int
        SelectableTextAlign: int
        SeparatorTextAlign: int
        SeparatorTextBorderSize: int
        SeparatorTextPadding: int
        TabBarBorderSize: int
        TabBarOverlineSize: int
        TabBorderSize: int
        TabRounding: int
        TableAngledHeadersAngle: int
        TableAngledHeadersTextAlign: int
        TreeLinesRounding: int
        TreeLinesSize: int
        WindowBorderSize: int
        WindowMinSize: int
        WindowPadding: int
        WindowRounding: int
        WindowTitleAlign: int

    class MouseButton:
        Left: int
        Middle: int
        Right: int

    class MouseCursor:
        Arrow: int
        Hand: int
        None_: int
        NotAllowed: int
        Progress: int
        ResizeAll: int
        ResizeEW: int
        ResizeNESW: int
        ResizeNS: int
        ResizeNWSE: int
        TextInput: int
        Wait: int

    class Cond:
        Always: int
        Appearing: int
        FirstUseEver: int
        None_: int
        Once: int

    class TableBgTarget:
        CellBg: int
        None_: int
        RowBg0: int
        RowBg1: int

    class SelectionRequestType:
        None_: int
        SetAll: int
        SetRange: int

class CursorMode:

    Normal: int
    Hidden: int
    Disabled: int

class Window:

    def __init__(self, width: int, height: int, title: str = "GLUX", gl_major: int = 3, gl_minor: int = 3, vsync: bool = True, y_up: bool = True) -> Window: ...
    def run(self) -> None: ...
    def get_size(self) -> Tuple[int, int]: ...
    def get_framebuffer_size(self) -> Tuple[int, int]: ...
    def get_position(self) -> Tuple[int, int]: ...
    def get_title(self) -> str: ...
    def is_y_up(self) -> bool: ...
    def is_vsync(self) -> bool: ...
    def is_fullscreen(self) -> bool: ...
    def should_close(self) -> bool: ...
    def screenshot(self, flip_vertically: bool) -> bytes: ...
    def set_size(self, width: int, height: int) -> None: ...
    def set_title(self, title: str) -> None: ...
    def set_vsync(self, vsync: bool) -> None: ...
    def set_y_up(self, y_up: bool) -> None: ...
    def set_position(self, x: int, y: int) -> None: ...
    def set_fullscreen(self, fullscreen: bool) -> None: ...
    def set_opacity(self, alpha: float) -> None: ...
    def set_resizable(self, resizable: bool) -> None: ...
    def set_decorated(self, decorated: bool) -> None: ...
    def set_floating(self, floating: bool) -> None: ...
    def set_icon(self, data: bytes, width: int, height: int) -> None: ...
    def close(self) -> None: ...
    def set_events_callback(self, callback: Callable[[], None]) -> None: ...
    def set_process_callback(self, callback: Callable[[], None]) -> None: ...
    def set_render_callback(self, callback: Callable[[], None]) -> None: ...
    def set_render_ui_callback(self, callback: Callable[[], None]) -> None: ...

class Keyboard:

    key: int
    scancode: int
    action: int
    mods: int
    def held(self, key: int) -> bool: ...

keyboard: Keyboard

class Mouse:

    button: int
    action: int
    mod: int
    xoffset : int
    yoffset : int
    def held(self, button: int) -> bool: ...

mouse: Mouse

class Cursor:

    x: float
    y: float
    def set_mode(self, mode: any) -> None: ...
    def set_visible(self, visible: bool) -> None: ...
    def set_pos(self, x: float, y: float) -> None: ...

cursor: Cursor

class mods:

    SHIFT: int
    CONTROL: int
    ALT: int
    SUPER: int
    CAPS_LOCK: int
    NUM_LOCK: int

class actions:

    PRESS: int
    RELEASE: int
    REPEAT: int

class scancodes:

    KEY_UNKNOWN: int

class keys:

    K_SPACE: int
    K_APOSTROPHE: int
    K_COMMA: int
    K_MINUS: int
    K_PERIOD: int
    K_SLASH: int
    K_0: int
    K_1: int
    K_2: int
    K_3: int
    K_4: int
    K_5: int
    K_6: int
    K_7: int
    K_8: int
    K_9: int
    K_SEMICOLON: int
    K_EQUAL: int
    K_A: int
    K_B: int
    K_C: int
    K_D: int
    K_E: int
    K_F: int
    K_G: int
    K_H: int
    K_I: int
    K_J: int
    K_K: int
    K_L: int
    K_M: int
    K_N: int
    K_O: int
    K_P: int
    K_Q: int
    K_R: int
    K_S: int
    K_T: int
    K_U: int
    K_V: int
    K_W: int
    K_X: int
    K_Y: int
    K_Z: int
    K_LEFT_BRACKET: int
    K_BACKSLASH: int
    K_RIGHT_BRACKET: int
    K_GRAVE_ACCENT: int
    K_WORLD_1: int
    K_WORLD_2: int
    K_ESCAPE: int
    K_ENTER: int
    K_TAB: int
    K_BACKSPACE: int
    K_INSERT: int
    K_DELETE: int
    K_RIGHT: int
    K_LEFT: int
    K_DOWN: int
    K_UP: int
    K_PAGE_UP: int
    K_PAGE_DOWN: int
    K_HOME: int
    K_END: int
    K_CAPS_LOCK: int
    K_SCROLL_LOCK: int
    K_NUM_LOCK: int
    K_PRINT_SCREEN: int
    K_PAUSE: int
    K_F1: int
    K_F2: int
    K_F3: int
    K_F4: int
    K_F5: int
    K_F6: int
    K_F7: int
    K_F8: int
    K_F9: int
    K_F10: int
    K_F11: int
    K_F12: int
    K_F13: int
    K_F14: int
    K_F15: int
    K_F16: int
    K_F17: int
    K_F18: int
    K_F19: int
    K_F20: int
    K_F21: int
    K_F22: int
    K_F23: int
    K_F24: int
    K_F25: int
    K_KP_0: int
    K_KP_1: int
    K_KP_2: int
    K_KP_3: int
    K_KP_4: int
    K_KP_5: int
    K_KP_6: int
    K_KP_7: int
    K_KP_8: int
    K_KP_9: int
    K_KP_DECIMAL: int
    K_KP_DIVIDE: int
    K_KP_MULTIPLY: int
    K_KP_SUBTRACT: int
    K_KP_ADD: int
    K_KP_ENTER: int
    K_KP_EQUAL: int
    K_LEFT_SHIFT: int
    K_LEFT_CONTROL: int
    K_LEFT_ALT: int
    K_LEFT_SUPER: int
    K_RIGHT_SHIFT: int
    K_RIGHT_CONTROL: int
    K_RIGHT_ALT: int
    K_RIGHT_SUPER: int
    K_MENU: int

class buttons:

    M_1: int
    M_2: int
    M_3: int
    M_4: int
    M_5: int
    M_6: int
    M_7: int
    M_8: int
    M_LEFT: int
    M_RIGHT: int
    M_MIDDLE: int