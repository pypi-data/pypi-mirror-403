
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
from matplotlib.path import Path
from matplotlib.transforms import Affine2D
from typing import List, Tuple, Optional, Any
import warnings

try:
    import uharfbuzz as hb
    from fontTools.ttLib import TTFont
    from fontTools.pens.basePen import BasePen
    HAS_HARFBUZZ = True
except ImportError:
    HAS_HARFBUZZ = False

class MatplotlibPathPen(BasePen):
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.verts = []
        self.codes = []

    def _moveTo(self, p):
        self.verts.append(p)
        self.codes.append(Path.MOVETO)

    def _lineTo(self, p):
        self.verts.append(p)
        self.codes.append(Path.LINETO)

    def _curveToOne(self, p1, p2, p3):
        self.verts.extend([p1, p2, p3])
        self.codes.extend([Path.CURVE4, Path.CURVE4, Path.CURVE4])

    def _qCurveToOne(self, p1, p2):
        self.verts.extend([p1, p2])
        self.codes.extend([Path.CURVE3, Path.CURVE3])

    def _closePath(self):
        self.verts.append((0, 0))
        self.codes.append(Path.CLOSEPOLY)

class HarfbuzzShaper:
    def __init__(self, font_path: str):
        if not HAS_HARFBUZZ:
            raise ImportError("uharfbuzz and fonttools are required for manual shaping.")
            
        self.font_path = font_path
        
        # Load for HarfBuzz
        with open(font_path, 'rb') as f:
            self.font_data = f.read()
        self.face = hb.Face(self.font_data)
        self.font = hb.Font(self.face)
        self.upem = self.face.upem
        self.font.scale = (self.upem, self.upem)
        
        # Load for Path Extraction
        self.ttfont = TTFont(font_path)
        self.glyph_set = self.ttfont.getGlyphSet()
        self.glyph_order = self.ttfont.getGlyphOrder()

    def shape(self, text: str) -> Tuple[List[Any], List[Any]]:
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf)
        return buf.glyph_infos, buf.glyph_positions

    def get_text_width(self, text: str, fontsize: float) -> float:
        infos, positions = self.shape(text)
        total_advance_units = sum(pos.x_advance for pos in positions)
        return total_advance_units * (fontsize / self.upem)

    def get_font_height(self, fontsize: float) -> float:
        # Get ascender/descender from fontTools hhea table
        hhea = self.ttfont.get('hhea')
        if hhea:
            ascender = hhea.ascent
            descender = hhea.descent  # Usually negative
            return (ascender - descender) * (fontsize / self.upem)
        else:
            # Fallback: approximate based on upem 
            return fontsize * 1.2  # Rough approximation

    def get_ascent(self, fontsize: float) -> float:
        """Get ascent (baseline to top) in scaled units."""
        hhea = self.ttfont.get('hhea')
        if hhea:
            return hhea.ascent * (fontsize / self.upem)
        else:
            return fontsize * 0.8  # Rough approximation

    def get_shaped_paths(self, text: str) -> List[Tuple[Path, float, float, float]]:
        """
        Returns list of (Path, x_pos, y_pos, scale_factor)
        Path is in Font Units.
        Pos is in Font Units.
        """
        infos, positions = self.shape(text)
        
        results = []
        current_x = 0
        current_y = 0
        
        for info, pos in zip(infos, positions):
            gid = info.codepoint
            try:
                glyph_name = self.glyph_order[gid]
            except IndexError:
                continue
                
            pen = MatplotlibPathPen(self.glyph_set)
            self.glyph_set[glyph_name].draw(pen)
            
            if pen.verts:
                path = Path(pen.verts, pen.codes)
                
                # We return position relative to start of string
                # x = cursor + off_x
                # y = cursor + off_y
                x = current_x + pos.x_offset
                y = current_y + pos.y_offset
                
                results.append((path, x, y))
                
            current_x += pos.x_advance
            current_y += pos.y_advance
            
        return results

from matplotlib.text import Text
from matplotlib.transforms import Affine2D

class ShapedText(Text):
    """
    A Text artist that uses manual HarfBuzz shaping.
    """
    def __init__(self, x, y, text, font_path, **kwargs):
        super().__init__(x, y, text, **kwargs)
        self.shaper = HarfbuzzShaper(font_path)
        
    def draw(self, renderer):
        if renderer is not None:
             self._renderer = renderer
        if not self.get_visible():
            return
            
        # 1. Basic Text Setup (properties)
        gc = renderer.new_gc()
        gc.set_foreground(self.get_color())
        gc.set_alpha(self.get_alpha())
        # gc.set_url(self.get_url())
        
        # 2. Get shaping results
        # Path is in Font Units (e.g. 1000 or 2048 UPEM)
        paths_and_pos = self.shaper.get_shaped_paths(self.get_text())
        
        # 3. Calculate Transform
        # Text transform: (Data X, Data Y) -> (Screen X, Screen Y)
        # We need to map: FontUnit -> ScreenUnit
        
        # Current Font Size in points
        fontsize_points = self.get_fontsize()
        # Pixels per point
        dpi = self.figure.dpi
        pixels_per_point = dpi / 72.0
        
        # Scale factor: FontUnit -> Pixels
        # 1 FontUnit = (1/UPEM) * (fontsize_points) * (pixels_per_point) pixels
        upem = self.shaper.upem
        scale = (1.0 / upem) * fontsize_points * pixels_per_point
        
        # Position transform
        # The (x,y) of the Text object is processed by self.get_transform()
        # This gives us the Screen Pixel coordinate of the text anchor.
        text_pos_screen = self.get_transform().transform([self.get_position()]) # [[x, y]]
        screen_x, screen_y = text_pos_screen[0]
        
        # We also need to handle Horizontal/Vertical Alignment (ha/va)
        # To do this, we need total width/height of the shaped text.
        total_width_font_units = self.shaper.get_text_width(self.get_text(), self.shaper.upem) # pass upem to get unscaled width
        total_width_pixels = total_width_font_units * scale
        
        # Height is approximately fontsize_pixels? Or bounding box?
        # For simplicity, approximate with fontsize for alignment??
        # Usually MPL uses bbox. We can calculate bbox from paths if needed.
        # Let's stick to basic alignment for now or assume baseline alignment (y=0).
        
        offset_x = 0
        if self.get_horizontalalignment() == 'center':
            offset_x = -total_width_pixels / 2
        elif self.get_horizontalalignment() == 'right':
            offset_x = -total_width_pixels
            
        # Vertical alignment
        # Matplotlib centers based on the bounding box of the text.
        # We need to calculate the bounding box of the shaped glyphs in Font Units.
        # Paths are (path, x, y).
        
        offset_y = 0
        va = self.get_verticalalignment()
        
        if va != 'baseline':
            # Calculate bounds
            min_y = float('inf')
            max_y = float('-inf')
            has_paths = False
            
            for path, gx, gy in paths_and_pos:
                if not path.vertices.size:
                    continue
                # Get extents of this path (in font units, relative to its origin 0,0)
                ext = path.get_extents()
                # Shift by glyph position
                # path.vertices are relative to glyph origin.
                # (gx, gy) is glyph origin relative to string origin.
                # So absolute y = vert_y + gy
                # extents are (xmin, ymin, xmax, ymax)
                
                # Careful: Bbox object behavior
                glyph_ymin = ext.ymin + gy
                glyph_ymax = ext.ymax + gy
                
                if glyph_ymin < min_y: min_y = glyph_ymin
                if glyph_ymax > max_y: max_y = glyph_ymax
                has_paths = True
            
            if not has_paths:
                # Fallback to font metrics if no glyphs (e.g. space) or bbox failure
                # height ~ ascender - descender?
                # Center ~ (ascender + descender) / 2
                asc = self.shaper.face.ascender
                desc = self.shaper.face.descender
                min_y = desc
                max_y = asc
            
            # Now determine offset (in Font Units)
            # We want to shift so that the reference point (e.g. center) is at 0.
            # Then our base transform places 0 at screen_y.
            
            if va == 'center':
                center_y = (min_y + max_y) / 2
                offset_y = -center_y * scale
            elif va == 'top':
                offset_y = -max_y * scale
            elif va == 'bottom':
                offset_y = -min_y * scale
            # baseline: offset_y = 0 (already set)
            
        # Actual Layout Transform:
        # 1. Scale path by `scale`
        # 2. Translate by (glyph_x * scale, glyph_y * scale) to assemble string
        # 3. Translate by (offset_x, offset_y) for alignment
        # 4. Translate by (screen_x, screen_y) to place on screen
        # 5. Rotate? self.get_rotation().
        
        # Matrix:
        # Scale(scale) * Translate(pos_x, pos_y) ...
        
        rotation = self.get_rotation()
        # Rotation usually happens around the anchor point (screen_x, screen_y).
        
        # Base transform for the whole text block (anchor at 0,0)
        # Font -> Screen (Calculated)
        base_transform = Affine2D().scale(scale)
        
        # Alignment translation
        align_transform = Affine2D().translate(offset_x, offset_y)
        
        # Rotation & Translation to Screen Position
        placement_transform = Affine2D().rotate_deg(rotation).translate(screen_x, screen_y)
        
        # Loop and draw
        for path, gx, gy in paths_and_pos:
            # Transform for this specific glyph
            # Move glyph to its place in the string (scaled)
            # Actually since we scale the whole coordinate system, gx/gy are in FontUnits.
            # So: Translate(gx, gy) -> Scale(scale) ...
            
            glyph_trans = Affine2D().translate(gx, gy) + base_transform + align_transform + placement_transform
            
            from matplotlib.colors import to_rgba
            rgba_color = to_rgba(self.get_color(), alpha=self.get_alpha())
            renderer.draw_path(gc, path, glyph_trans, rgbFace=rgba_color)
            
        gc.restore()



