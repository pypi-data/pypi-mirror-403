import pandas as pd
import numpy as np
import gc
import re
from multiprocessing import Pool
from dataclasses import dataclass
from typing import Literal, Tuple

from rich.progress import Progress

from ezwgd.utils.parse import Genome, GenomeLight
from ezwgd.coll._corecoll import Collinearity
from ezwgd import console

@dataclass(kw_only=True, )
class DoCollinearity:
    # Parameters need receive
    genome1: Genome | GenomeLight
    genome2: Genome | GenomeLight
    blast: pd.DataFrame
    savefile: str

    # Initialize parameters with default values
    repeat_number = 10
    multiple: int = 1
    score: int = 100
    evalue: float = 1e-5
    blast_reverse: bool = False
    over_gap: int = 15
    comparison: Literal['genomes', 'chromosomes'] = 'genomes'
    position: Literal['order', 'end'] = 'order'
    grading: Tuple[int, int, int] = (50, 40, 25)
    mg: Tuple[int, int] = (40, 40)
    processes_num: int = 4
    coverage_ratio: float = 0.8
    gap_penalty: int = 0
    over_length: int = 0
    pvalue_min: float = 1

    options = {
        'gap_penalty': gap_penalty,
        'over_length': over_length,
        'pvalue_min': pvalue_min,
        'over_gap': over_gap,
        'coverage_ratio': coverage_ratio,
        'grading': grading,
        'mg': mg,
    }

    def _deal_blast_for_chromosomes(
            self,
            blast: pd.DataFrame,
            rednum: int,
            repeat_number: int,
    ):
        bluenum = rednum
        blast = blast.sort_values(by=['gene1', 'bitscore'], ascending=[True, False])

        def assign_grading(group):
            group['cumcount'] = group.groupby(1).cumcount()
            group = group[group['cumcount'] <= repeat_number]
            group['grading'] = pd.cut(
                group['cumcount'],
                bins=[-1, 0, bluenum, repeat_number],
                labels=self.grading,
                right=True
            )
            return group

        newblast = blast.groupby(['chr1', 'chr2']).apply(assign_grading).reset_index(drop=True)
        newblast['grading'] = newblast['grading'].astype(int)
        return newblast[newblast['grading'] > 0]

    def _deal_blast_for_genomes(
            self,
            blast: pd.DataFrame,
            rednum: int,
            repeat_number: int,
    ):
        # Initialize the grading column
        blast['grading'] = 0

        # Define the blue number as the sum of rednum and the predefined constant
        bluenum = 4 + rednum

        # Get the indices for each group by sorting the 11th column (bitscore) in descending order
        index = [group.sort_values(by=['bitscore'], ascending=[False])[:repeat_number].index.tolist()
                 for name, group in blast.groupby(['gene1'])]

        # Split the indices into red, blue, and gray groups
        reddata = np.array([k[:rednum] for k in index], dtype=object)
        bluedata = np.array([k[rednum:bluenum] for k in index], dtype=object)
        graydata = np.array([k[bluenum:repeat_number] for k in index], dtype=object)

        # Concatenate the results into flat lists
        redindex = np.concatenate(reddata) if reddata.size else []
        blueindex = np.concatenate(bluedata) if bluedata.size else []
        grayindex = np.concatenate(graydata) if graydata.size else []

        # Update the grading column based on the group indices
        blast.loc[redindex, 'grading'] = self.grading[0]
        blast.loc[blueindex, 'grading'] = self.grading[1]
        blast.loc[grayindex, 'grading'] = self.grading[2]

        # Return only the rows with non-zero grading
        return blast[blast['grading'] > 0]

    def run(self):
        # Read simplified gff data
        gff1 = self.genome1.simp_gff
        gff2 = self.genome2.simp_gff

        # Processing blast data
        blast = self.blast[(self.blast['gene1'].isin(self.genome1.genelist)) & (self.blast['gene2'].isin(self.genome2.genelist))]
        # Map positions and chromosome information
        blast['loc1'] = blast['gene1'].map(dict(zip(gff1['gene_id'], gff1[self.position])))
        blast['loc2'] = blast['gene2'].map(dict(zip(gff2['gene_id'], gff2[self.position])))
        blast['chr1'] = blast['gene1'].map(dict(zip(gff1['gene_id'], gff1['chr'])))
        blast['chr2'] = blast['gene2'].map(dict(zip(gff2['gene_id'], gff2['chr'])))

        # Apply blast filtering and grading
        if self.comparison.lower() == 'genomes':
            blast = self._deal_blast_for_genomes(blast, int(self.multiple), int(self.repeat_number))
        if self.comparison.lower() == 'chromosomes':
            blast = self._deal_blast_for_chromosomes(blast, int(self.multiple), int(self.repeat_number))

        if len(blast) == 0:
            raise RuntimeError('GFF3 and BLAST result do not seem to match.')

        console.log(f'The filtered homologous gene pairs are {len(blast)}.')

        # Group blast data by 'chr1' and 'chr2'
        total = [((chr1, chr2), group) for (chr1, chr2), group in blast.groupby(['chr1', 'chr2'])]
        del blast
        gc.collect()
        # Determine chunk size for multiprocessing
        chunks_size = int(np.ceil(len(total) / float(self.processes_num)))

        # Running with multi-processes
        result, data = '', []

        with Progress() as progress:
            task = progress.add_task('CollinearScan running.', total=len(total))

            with Pool(processes=self.processes_num) as pool:
                async_results = [
                    pool.apply_async(self._single_pool, (group, gff1, gff2,),
                                     callback=lambda _: progress.update(task, advance=1, chunks = chunks_size))
                    for group in total
                ]
                data = [ar.get() for ar in async_results]

        for k in data:
            # Collect results from async tasks
            if k:
                result += k
        # Write final output to file
        result = re.split('\n', result)
        fout = open(self.savefile, 'w')
        num = 1
        for line in result:
            if re.match(r"# Alignment", line):
                # Replace alignment number
                s = f'# Alignment {num}:'
                fout.write(s + line.split(':')[1] + '\n')
                num += 1
                continue
            if len(line) > 0:
                fout.write(line + '\n')
        fout.close()

    def _single_pool(self, group, gff1, gff2):
        text = ''
        chr1, chr2 = str(group[0][0]), str(group[0][1])
        print(f'Running {chr1} vs {chr2}')
        # Extract and sort points
        points = group[1][['loc1', 'loc2', 'grading']].sort_values(
            by=['loc1', 'loc2'], ascending=[True, True]
        )
        # Initialize collinearity analysis
        collinearity = Collinearity(
            points=points,
            **self.options
        )
        data = collinearity.run()
        # Extract gene information
        gf1 = gff1[gff1['chr'] == chr1].reset_index().set_index('order')[['gene_id', 'strand']]
        gf2 = gff2[gff2['chr'] == chr2].reset_index().set_index('order')[['gene_id', 'strand']]
        n = 1
        for block, evalue, score in data:
            if len(block) < self.over_gap:
                continue
            # Map gene names and strands
            block['name1'] = block['loc1'].map(gf1['gene_id'])
            block['name2'] = block['loc2'].map(gf2['gene_id'])
            block['strand1'] = block['loc1'].map(gf1['strand'])
            block['strand2'] = block['loc2'].map(gf2['strand'])
            block['strand'] = np.where(
                block['strand1'] == block['strand2'], '1', '-1'
            )
            # Prepare text output
            block['text'] = block.apply(
                lambda x: f"{x['name1']} {x['loc1']} {x['name2']} {x['loc2']} {x['strand']}\n",
                axis=1
            )
            # Determine alignment mark
            a, b = block['loc2'].head(2).values
            mark = 'plus' if a < b else 'minus'
            # Append alignment information
            text += f'# Alignment {n}: score={score} pvalue={evalue} N={len(block)} {chr1}&{chr2} {mark}\n'
            text += ''.join(block['text'].values)
            n += 1
        return text
