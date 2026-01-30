import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.text import Text
from matplotlib.lines import Line2D
from matplotlib.lines import Line2D
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties, findfont
from typing import List, Optional, Tuple, Union, Dict, Any

from .shaping import ShapedText, HarfbuzzShaper, HAS_HARFBUZZ

def _needs_complex_shaping(text: str) -> bool:
    """
    Check if text contains characters from complex scripts that need HarfBuzz shaping.
    Currently checks for Devanagari (used for Nepali, Hindi, Sanskrit, etc.)
    """
    for char in text:
        code = ord(char)
        # Devanagari: U+0900 to U+097F
        # Devanagari Extended: U+A8E0 to U+A8FF  
        # Vedic Extensions: U+1CD0 to U+1CFF
        if (0x0900 <= code <= 0x097F or 
            0xA8E0 <= code <= 0xA8FF or
            0x1CD0 <= code <= 0x1CFF):
            return True
    return False

def _resolve_font_path(kwargs: Dict[str, Any]) -> Optional[str]:
    """Helper to resolve font file path from text kwargs."""
    fp = kwargs.get('fontproperties')
    if fp:
        return findfont(fp)
        
    font = kwargs.get('fontfamily') or kwargs.get('family')
    if not font:
        # Fallback to default
        font = plt.rcParams['font.family'][0]
    
    if isinstance(font, list):
        font = font[0]
        
    try:
        fp = FontProperties(family=font)
        return findfont(fp)
    except Exception:
        return None

def richtext(
    x: float,
    y: float,
    strings: List[str],
    colors: Optional[Union[str, List[Any], Dict[Any, Any]]] = None,
    ax: Optional[Axes] = None,
    **kwargs
) -> List[Text]:
    """
    Display text with different colors and properties for each string, supporting word wrapping and alignment.
    Supports complex scripts (e.g. Nepali) via manual shaping if uharfbuzz is installed.

    Parameters
    ----------
    x, y : float
        Starting position of the text block.
    strings : List[str]
        List of text strings to display.
    colors : Union[str, List[str], Dict[int, str]]
        Color for the text. Can be:
        - A single string: Applied to all strings.
        - A list of colors: Corresponding to each string (dynamic extension supported).
        - A dictionary: Mapping indices to colors (e.g., {1: 'red'}). Unspecified indices use default/black.
    ax : matplotlib.axes.Axes, optional
        The axes to draw on. If None, uses the current axes.
    **kwargs : dict
        Additional arguments passed to `ax.text`.
        
        Global arguments (applied to the whole block):
        - box_width (float): Maximum width of the text block for wrapping. If None, no wrapping occurs.
        - linespacing (float): Line spacing multiplier (default: 1.5).
        - ha (str): Horizontal alignment ('left', 'center', 'right').
        - va (str): Vertical alignment ('top', 'center', 'bottom').
        - zorder (int): Z-order for the text.
        - transform: Transform for the text.

        Per-segment arguments:
        - Any other text property (e.g., fontsize, fontweight, fontproperties) can be:
          - A single value: Applied to all strings.
          - A list of values: Corresponding to each string (dynamic extension supported).
          - A dictionary: Mapping indices to values (e.g., {1: 20}).
          - underline (bool): If True, draws a line below the text.

    Returns
    -------
    List[matplotlib.text.Text]
        A list of the created Text objects.

    Raises
    ------
    ValueError
        If inputs are invalid.
    """
    if ax is None:
        ax = plt.gca()

    # Extract global special kwargs
    box_width: Optional[float] = kwargs.pop('box_width', None)
    linespacing: float = kwargs.pop('linespacing', 1.5)
    if 'spacing' in kwargs:
        linespacing = kwargs.pop('spacing')
    
    ha = kwargs.pop('ha', kwargs.pop('horizontalalignment', 'left'))
    va = kwargs.pop('va', kwargs.pop('verticalalignment', 'center'))
    transform = kwargs.pop('transform', ax.transData)
    zorder = kwargs.pop('zorder', 1)
    
    # Normalize properties for each string segment
    segment_properties = _normalize_properties(strings, colors, **kwargs)

    # Get renderer for measuring text
    fig = ax.get_figure()
    if fig == None:
         raise ValueError("The axes must be associated with a figure.")
         
    try:
        renderer = fig.canvas.get_renderer()
    except Exception:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()

    # Logic separation: Wrapping vs Non-Wrapping
    if box_width is not None:
        # 1. Tokenize into words with properties
        words = _tokenize_strings(strings, segment_properties)
        # 2. Build lines with wrapping
        lines = _build_lines_wrapped(words, ax, renderer, box_width)
    else:
        # 1. Treat strings as segments
        # 2. Build a single line
        lines = [_build_line_seamless(strings, segment_properties, ax, renderer)]

    # 3. Draw lines
    text_objects = _draw_lines(
        lines, x, y, ax, renderer, 
        linespacing=linespacing, ha=ha, va=va, 
        transform=transform, zorder=zorder
    )

    return text_objects


def _normalize_properties(
    strings: List[str], 
    colors: Union[str, List[Any], Dict[Any, Any]], 
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Normalize colors and kwargs into a list of property dictionaries, one for each string.
    Supports:
    - Scalar values (applied globally).
    - Lists of values (dynamic extension).
    - Dictionaries with int/tuple keys (targeted overrides).
    - Lists of pairs [(indices, value)] (targeted overrides).
    - Plural arguments (e.g., fontsizes) overriding singular ones (e.g., fontsize).
    """
    n = len(strings)
    props_list = []
    
    # Helper to extend list to length n
    def extend_list(lst: List[Any], target_len: int) -> List[Any]:
        if not lst:
            return [None] * target_len 
        if len(lst) >= target_len:
            return lst[:target_len]
        last_val = lst[-1]
        extension = [last_val] * (target_len - len(lst))
        return lst + extension

    # Helper to parse mapping from dict or list-of-pairs
    def parse_mapping(val: Any) -> Optional[Dict[int, Any]]:
        flat_d = {}
        
        if isinstance(val, dict):
            for k, v in val.items():
                if isinstance(k, tuple):
                    for idx in k:
                        flat_d[idx] = v
                else:
                    flat_d[k] = v
            return flat_d
            
        if isinstance(val, list):
            if not val:
                return None
            first = val[0]
            if isinstance(first, (list, tuple)) and len(first) == 2:
                k, v = first
                if isinstance(k, int) or (isinstance(k, (list, tuple)) and all(isinstance(x, int) for x in k)):
                    for item in val:
                        if not (isinstance(item, (list, tuple)) and len(item) == 2):
                            return None 
                        k, v = item
                        if isinstance(k, (list, tuple)):
                            for idx in k:
                                flat_d[idx] = v
                        else:
                            flat_d[k] = v
                    return flat_d
            return None
        return None
    
    # Handle colors
    color_mapping = parse_mapping(colors)
    color_list = [None] * n
    
    if color_mapping is not None:
        pass 
    elif isinstance(colors, str):
        color_list = [colors] * n
    elif isinstance(colors, list):
        color_list = extend_list(colors, n)
    else:
        if colors is not None:
             raise ValueError("colors must be a string, a list, or a mapping.")
        
    # Handle other kwargs
    list_kwargs = {}
    mapping_kwargs = {}
    scalar_kwargs = {}
    
    # Map plural keys to singular keys
    plural_map = {
        'fontsizes': 'fontsize',
        'fontweights': 'fontweight',
        'fontfamilies': 'fontfamily',
        'fontstyles': 'fontstyle',
        'alphas': 'alpha',
        'backgroundcolors': 'backgroundcolor',
        'colors': 'color', # Special case if passed in kwargs
        'underlines': 'underline'
    }
    
    # Separate kwargs into types
    for k, v in kwargs.items():
        # Check for plural override first
        if k in plural_map:
            singular_k = plural_map[k]
            mapping = parse_mapping(v)
            if mapping is not None:
                if singular_k not in mapping_kwargs:
                    mapping_kwargs[singular_k] = {}
                mapping_kwargs[singular_k].update(mapping)
            elif isinstance(v, list):
                # If plural is a list, treat as list_kwargs for the singular key
                list_kwargs[singular_k] = extend_list(v, n)
            continue
            
        mapping = parse_mapping(v)
        if mapping is not None:
            mapping_kwargs[k] = mapping
        elif isinstance(v, list):
            list_kwargs[k] = extend_list(v, n)
        else:
            scalar_kwargs[k] = v
            
    for i in range(n):
        # 1. Start with scalar (global) properties
        props = scalar_kwargs.copy()
        
        # 2. Apply list-based properties (if any)
        for k, v_list in list_kwargs.items():
            props[k] = v_list[i]
            
        # 3. Apply color (specific overrides global)
        if color_list[i] is not None:
             props['color'] = color_list[i]
        
        if color_mapping and i in color_mapping:
            props['color'] = color_mapping[i]
        
        # 4. Apply mapping-based properties (specific overrides global & list)
        for k, v_map in mapping_kwargs.items():
            if i in v_map:
                props[k] = v_map[i]
                
        props_list.append(props)
        
    return props_list


def _tokenize_strings(
    strings: List[str], 
    properties: List[Dict[str, Any]]
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Split strings into words while preserving spaces and associating properties.
    Used ONLY when wrapping is enabled.
    """
    words: List[Tuple[str, Dict[str, Any]]] = []
    for string, props in zip(strings, properties):
        parts = string.split(' ')
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                words.append((part + ' ', props))
            else:
                if part:
                    words.append((part, props))
                elif not part and i > 0:
                     pass
    return words


def _get_text_width(text: str, ax: Axes, renderer, **text_kwargs) -> float:
    """Measure the width of a text string."""
    # Remove custom properties that ax.text doesn't understand
    kwargs = text_kwargs.copy()
    kwargs.pop('underline', None)
    
    # Try shaping if available
    if HAS_HARFBUZZ:
        font = kwargs.get('fontfamily') or kwargs.get('family') or plt.rcParams['font.family'][0]
        # Resolve font path
        try:
            # Handle fontfamily being None or list
            if not font:
                 font = plt.rcParams['font.family'][0]
            if isinstance(font, list):
                font = font[0]
                
            fp = FontProperties(family=font)
            path = findfont(fp)
            
            # Simple caching could go here
            if path:
                fontsize = kwargs.get('fontsize') or kwargs.get('size') or plt.rcParams['font.size']
                shaper = HarfbuzzShaper(path)
                width_points = shaper.get_text_width(text, fontsize)
                
                # Convert points -> pixels -> data
                # 1. Points to Pixels
                pixels = renderer.points_to_pixels(width_points)
                
                # 2. Pixels to Data
                # We can measure the width of a 0-width line vs 'pixels'-width line?
                # Or use proper transform math.
                # bbox width in pixels = 'pixels'.
                # We want width in data.
                
                # Create a bbox in display coords
                from matplotlib.transforms import Bbox
                bbox_display = Bbox.from_bounds(0, 0, pixels, 0)
                
                # Transform to data coords
                bbox_data = bbox_display.transformed(ax.transData.inverted())
                return bbox_data.width
        except Exception:
            pass # Fallback to native

    t = ax.text(0, 0, text, **kwargs)
    bbox = t.get_window_extent(renderer=renderer)
    bbox_data = bbox.transformed(ax.transData.inverted())
    w = bbox_data.width
    t.remove()
    return w


def _get_text_metrics(text: str, ax: Axes, renderer, **text_kwargs) -> tuple:
    """
    Get text metrics: (width, ascent) in data units.
    - width: horizontal extent
    - ascent: distance from baseline to top of text
    """
    kwargs = text_kwargs.copy()
    kwargs.pop('underline', None)
    
    # Try shaping if available
    # Only use HarfBuzz measurement if the text actually needs complex shaping.
    # Otherwise, trust Matplotlib's native measurement which handles font fallback (e.g. lists of fonts) better.
    if HAS_HARFBUZZ and _needs_complex_shaping(text):
        path = _resolve_font_path(kwargs)
        try:
            if path:
                fontsize = kwargs.get('fontsize') or kwargs.get('size') or plt.rcParams['font.size']
                shaper = HarfbuzzShaper(path)
                
                # Get width and ascent in points
                width_points = shaper.get_text_width(text, fontsize)
                ascent_points = shaper.get_ascent(fontsize)
                
                # Convert to pixels then to data units
                from matplotlib.transforms import Bbox
                
                width_px = renderer.points_to_pixels(width_points)
                ascent_px = renderer.points_to_pixels(ascent_points)
                
                # Width: horizontal conversion
                bbox_w = Bbox.from_bounds(0, 0, width_px, 0)
                width_data = bbox_w.transformed(ax.transData.inverted()).width
                
                # Ascent: vertical conversion
                bbox_a = Bbox.from_bounds(0, 0, 0, ascent_px)
                ascent_data = bbox_a.transformed(ax.transData.inverted()).height
                
                return (width_data, ascent_data)
        except Exception:
            pass  # Fallback to native
    
    # Native measurement
    t = ax.text(0, 0, text, **kwargs)
    bbox = t.get_window_extent(renderer=renderer)
    bbox_data = bbox.transformed(ax.transData.inverted())
    
    width_data = bbox_data.width
    # For native text, ascent ≈ height (simplified; baseline is at bottom of bbox)
    ascent_data = bbox_data.height
    
    t.remove()
    return (width_data, ascent_data)


def _get_text_height(text: str, ax: Axes, renderer, **text_kwargs) -> float:
    """Measure the height of a text string."""
    # Remove custom properties that ax.text doesn't understand
    kwargs = text_kwargs.copy()
    kwargs.pop('underline', None)

    # Try shaping-based height for Devanagari fonts
    # This avoids measuring with Latin chars that the font might not have
    if HAS_HARFBUZZ:
        path = _resolve_font_path(kwargs)
        try:
            # Check if this is a known Devanagari font (simplified check via path for now? 
            # Or assume if resolving worked and contained Devanagari chars earlier...
            # Actually valid logic: if we are here and path resolves, we trust it?
            # But the original code restricted it to known fonts.
            # Let's keep it generally open if path is found, OR check font name.
            
            if path:
                # Optional: check for Devanagari-likeness if needed, but path resolution implies intent.
                # However, for height specifically we only wanted this for specific fonts to avoid 'Hg'.
                # Let's be permissive if path is found since we use shaper now.
                
                fontsize = kwargs.get('fontsize') or kwargs.get('size') or plt.rcParams['font.size']
                shaper = HarfbuzzShaper(path)
                height_points = shaper.get_font_height(fontsize)
                
                # Convert points -> pixels -> data
                pixels = renderer.points_to_pixels(height_points)
                from matplotlib.transforms import Bbox
                bbox_display = Bbox.from_bounds(0, 0, 0, pixels)
                bbox_data = bbox_display.transformed(ax.transData.inverted())
                return bbox_data.height
        except Exception:
            pass  # Fallback to native

    # Use a representative character for height if text is empty or space
    # But we need the height of THIS specific font configuration.
    measure_text = text if text.strip() else "Hg"
    t = ax.text(0, 0, measure_text, **kwargs)
    bbox = t.get_window_extent(renderer=renderer)
    bbox_data = bbox.transformed(ax.transData.inverted())
    h = bbox_data.height
    t.remove()
    return h


def _build_lines_wrapped(
    words: List[Tuple[str, Dict[str, Any]]], 
    ax: Axes, 
    renderer, 
    box_width: float
) -> List[List[Tuple[str, Dict[str, Any], float, float]]]:
    """
    Group words into lines based on box_width.
    Returns: List of lines, where each line is List of (word, props, width, ascent).
    """
    lines: List[List[Tuple[str, Dict[str, Any], float, float]]] = []
    current_line: List[Tuple[str, Dict[str, Any], float, float]] = []
    current_line_width = 0.0

    for word, props in words:
        w, asc = _get_text_metrics(word, ax, renderer, **props)
        
        if current_line_width + w > box_width and current_line:
            # Wrap to new line
            lines.append(current_line)
            current_line = [(word, props, w, asc)]
            current_line_width = w
        else:
            current_line.append((word, props, w, asc))
            current_line_width += w
            
    if current_line:
        lines.append(current_line)
        
    return lines


def _build_line_seamless(
    strings: List[str],
    properties: List[Dict[str, Any]],
    ax: Axes,
    renderer
) -> List[Tuple[str, Dict[str, Any], float, float]]:
    """
    Build a single line from strings without splitting by spaces.
    Returns: List of (string, props, width, ascent).
    """
    line: List[Tuple[str, Dict[str, Any], float, float]] = []
    for string, props in zip(strings, properties):
        w, asc = _get_text_metrics(string, ax, renderer, **props)
        line.append((string, props, w, asc))
    return line


def _draw_lines(
    lines: List[List[Tuple[str, Dict[str, Any], float, float]]],
    x: float,
    y: float,
    ax: Axes,
    renderer,
    linespacing: float,
    ha: str,
    va: str,
    transform,
    zorder: int
) -> List[Text]:
    """
    Draw the lines of text onto the axes using baseline alignment.
    Each line item is (word, props, width, ascent).
    """
    text_objects: List[Text] = []
    
    # Calculate metrics for each line
    line_metrics = []
    for line in lines:
        # Find max ascent and max total height in this line
        max_ascent = max(item[3] for item in line) if line else 0.0
        max_height = 0.0
        for word, props, w, asc in line:
            h = _get_text_height(word, ax, renderer, **props)
            if h > max_height:
                max_height = h
        line_metrics.append((max_ascent, max_height * linespacing))
        
    total_block_height = sum(m[1] for m in line_metrics)
    
    # Calculate top Y position based on vertical alignment of the block
    if va == 'center':
        top_y = y + (total_block_height / 2)
    elif va == 'top':
        top_y = y
    elif va == 'bottom':
        top_y = y + total_block_height
    else: 
        top_y = y + (total_block_height / 2)

    current_y = top_y
    
    for i, line in enumerate(lines):
        max_ascent, line_height = line_metrics[i]
        
        # Calculate baseline position
        # Baseline is at: top of line - max_ascent
        baseline_y = current_y - max_ascent
        
        # Calculate line width for horizontal alignment
        line_width = sum(item[2] for item in line)
        
        if ha == 'center':
            line_start_x = x - (line_width / 2)
        elif ha == 'right':
            line_start_x = x - line_width
        else:  # left
            line_start_x = x
            
        current_x = line_start_x
        
        for word, props, w, asc in line:
            text_kwargs = props.copy()
            
            # Extract underline property
            underline = text_kwargs.pop('underline', False)
            
            # Use baseline alignment for all text
            text_kwargs.update({
                'va': 'baseline', 
                'ha': 'left',
                'transform': transform,
                'zorder': zorder
            })
            
            # Determine if we should use ShapedText
            used_shaper = False
            t = None
            
            if HAS_HARFBUZZ and _needs_complex_shaping(word):
                try:
                    path = _resolve_font_path(text_kwargs)
                    if path:
                        t = ShapedText(current_x, baseline_y, word, font_path=path, **text_kwargs)
                        ax.add_artist(t)
                        used_shaper = True
                except Exception as e:
                    pass
            
            if not used_shaper:
                t = ax.text(current_x, baseline_y, word, **text_kwargs)
                
            text_objects.append(t)
            
            # Draw underline if requested
            if underline:
                # Get the bounding box of the text we just drew
                # We can use the width w we already calculated
                # But for Y position, we want it slightly below the text
                
                # A simple approximation is to draw it at the bottom of the line band?
                # Or relative to the text baseline?
                # Since we used va='center', the text is centered at line_center_y.
                # The height is roughly line_height / linespacing.
                # Let's put the underline at line_center_y - (h/2) - padding?
                
                # Let's use the bbox of the text object to find the bottom
                # bbox = t.get_window_extent(renderer=renderer)
                # bbox_data = bbox.transformed(ax.transData.inverted())
                
                # y0 is the bottom of the text bbox
                # y_bottom = bbox_data.y0
                
                # Since ShapedText might behave differently with bbox, and we already know 'w'.
                # And we aligned 'va=center'.
                # Let's use the line_center_y and offset down.
                # Text Height approximation:
                fontsize = text_kwargs.get('fontsize', 12)
                # data_height approximation? 
                # This is risky if aspect ratio is not 1.
                # Fallback to bbox logic, assuming draw has happened?
                # ShapedText needs to be drawn to have a valid bbox?
                # In Matplotlib, get_window_extent() triggers a draw if needed? 
                # Or we can just trust the metrics.
                
                # For consistency with previous code, let's try getting bbox.
                try:
                    bbox = t.get_window_extent(renderer=renderer)
                    bbox_data = bbox.transformed(ax.transData.inverted())
                    y_bottom = bbox_data.y0
                except Exception:
                    # Fallback if renderer issue
                    y_bottom = line_center_y - 5 # arbitrary?
                
                # Draw line from current_x to current_x + w
                
                # Draw line from current_x to current_x + w
                # Use the same color as the text
                color = t.get_color()
                
                line = Line2D(
                    [current_x, current_x + w], 
                    [y_bottom, y_bottom], 
                    color=color, 
                    linewidth=1, # Maybe configurable?
                    transform=transform,
                    zorder=zorder
                )
                ax.add_line(line)
            
            current_x += w
            
        current_y -= line_height
        
    return text_objects
