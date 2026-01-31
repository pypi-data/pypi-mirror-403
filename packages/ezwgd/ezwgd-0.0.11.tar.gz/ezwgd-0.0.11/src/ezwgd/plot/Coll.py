#  Copyright (C) 2025-2026, HYLi360.
#  Free software distributed under the terms of the GNU GPL-3.0 license,
#  and comes with ABSOLUTELY NO WARRANTY.
#  See at <https://www.gnu.org/licenses/gpl-3.0.en.html>

from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

import pandas as pd

@dataclass
class CollPlot:
    genome_structure1: pd.DataFrame
    genome_structure2: pd.DataFrame
    species_name1: str
    species_name2: str
    anchor: zip

    h = (0.6, 0.4)
    x = (0.2, 0.9)
    spacing = 0.1

    chrnamels1 = None
    chrnamels2 = None
    savefile = None

    def make_plot(self):
        self._chro_init()
        self._collbox_init()

        palette = plt.get_cmap('tab10')

        canvas = plt.gca()

        # Chromosomes
        for start, length in self.chrls1:
            small_rect = patches.Rectangle((start, self.h[0]-0.003), width=length, height=0.006, fill=True, color=palette(0))
            canvas.add_patch(small_rect)
            border = patches.Rectangle((start, self.h[0]-0.01), width=length, height=0.02, fill=False, ec=(0.2,0.2,0.2,0.2))
            canvas.add_patch(border)

        for start, length in self.chrls2:
            small_rect = patches.Rectangle((start, self.h[1]-0.003), width=length, height=0.006, fill=True, color=palette(1))
            canvas.add_patch(small_rect)
            border = patches.Rectangle((start, self.h[1]-0.01), width=length, height=0.02, fill=False, ec=(0.2,0.2,0.2,0.2))
            canvas.add_patch(border)

        # Collinearity pairs
        for collbox in self.new_anchor:
            collbox_patch = self.get_bezier_ribbon(collbox[0],collbox[1],collbox[2],collbox[3], 'grey')
            canvas.add_patch(collbox_patch)

        # Add species name
        canvas.text(x=0.12, y=self.h[0], s='P. veris', size=15, ha='center', va='center', fontstyle='italic')
        canvas.text(x=0.12, y=self.h[1], s='P. vulgaris', size=15, ha='center', va='center', fontstyle='italic')

        # Close the axis
        plt.axis('off')

        plt.show()

    def _chro_init(self):
        """Preprocessing steps prior of plotting."""
        # set chromesome list.
        chrls1 = self.genome_structure1['chr'].drop_duplicates().tolist()
        if self.chrnamels1 is not None:
            self.chrnamels1 = [chro for chro in chrls1]
        else:
            self.chrnamels1 = chrls1

        chrls2 = self.genome_structure2['chr'].drop_duplicates().tolist()
        if self.chrnamels2 is not None:
            self.chrnamels2 = [chro for chro in chrls2]
        else:
            self.chrnamels2 = chrls2

        genes_num1 = len(self.genome_structure1[self.genome_structure1['chr'].isin(self.chrnamels1)])
        genes_num2 = len(self.genome_structure2[self.genome_structure2['chr'].isin(self.chrnamels2)])

        sf1 = (self.x[1] - self.x[0])/(genes_num1 * (1 + self.spacing))
        sf2 = (self.x[1] - self.x[0])/(genes_num2 * (1 + self.spacing))

        space_len1 = self.spacing * genes_num1 / (len(self.chrnamels1) - 1)
        space_len2 = self.spacing * genes_num2 / (len(self.chrnamels2) - 1)

        start1, length1, space_end1 = [], [], [self.x[0]]
        start2, length2, space_end2 = [], [], [self.x[0]]

        for chro in self.chrnamels1:
            start1.append(space_end1[-1])
            length1.append(len(self.genome_structure1[self.genome_structure1['chr'] == chro]) * sf1)
            space_end1.append(start1[-1] + length1[-1] + space_len1 * sf1)

        for chro in self.chrnamels2:
            start2.append(space_end2[-1])
            length2.append(len(self.genome_structure2[self.genome_structure2['chr'] == chro]) * sf2)
            space_end2.append(start2[-1] + length2[-1] + space_len2 * sf2)

        self.chrls1, self.chrls2, self.sf1, self.sf2 = tuple(zip(start1, length1)), tuple(zip(start2, length2)), sf1, sf2
        self.startd1, self.startd2 = dict(zip(self.chrnamels1, start1)), dict(zip(self.chrnamels2, start2))

    def _collbox_init(self):
        res = []
        for chr1, chr2, loc1start, loc1end, loc2start, loc2end in self.anchor:
            res.append([
                self.startd1[str(chr1)] + loc1start * self.sf1,
                self.startd1[str(chr1)] + loc1end * self.sf1,
                self.startd2[str(chr2)] + loc2start * self.sf2,
                self.startd2[str(chr2)] + loc2end * self.sf2,
            ])
        self.new_anchor = res

    def get_bezier_ribbon(self, x_top_start, x_top_end, x_bot_start, x_bot_end, color_code):
        mid_y = (self.h[0] + self.h[1]) / 2

        codes = [
            Path.MOVETO,
            Path.LINETO,

            Path.CURVE4,  # verts[2]
            Path.CURVE4,  # verts[3]
            Path.CURVE4,  # verts[4]

            Path.LINETO,

            Path.CURVE4,  # verts[6]
            Path.CURVE4,  # verts[7]
            Path.CURVE4,  # verts[8]

            Path.CLOSEPOLY,
        ]

        verts = [
            (x_top_start, self.h[0]-0.003),  # MOVETO
            (x_top_end, self.h[0]-0.003),    # LINETO

            (x_top_end, mid_y),              # CURVE4
            (x_bot_end, mid_y),              # CURVE4
            (x_bot_end, self.h[1]+0.003),    # CURVE4

            (x_bot_start, self.h[1]+0.003),  # LINETO

            (x_bot_start, mid_y),            # CURVE4
            (x_top_start, mid_y),            # CURVE4
            (x_top_start, self.h[0]-0.003),  # CURVE4

            (x_top_start, self.h[0]-0.003),  # CLOSEPOLY
        ]

        path = Path(verts, codes)
        patch = patches.PathPatch(path, facecolor=color_code, edgecolor='none', lw=0, alpha=0.5)
        return patch
