import tdKernListView
import importlib
from fontParts.world import CurrentFont
importlib.reload(tdKernListView)
from tdKernListView import TDKernFinger
# fix layer color for GlyphCollectionView
# CurrentFont().getLayer('foreground').color = (0, 0, 0, 1)
TDKernFinger()
