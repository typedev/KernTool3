import tdKernObserver
import importlib
from fontParts.world import CurrentFont
importlib.reload(tdKernObserver)
from tdKernObserver import KernObserver
# fix layer color for GlyphCollectionView
# CurrentFont().getLayer('foreground').color = (0, 0, 0, 1)
KernObserver()
