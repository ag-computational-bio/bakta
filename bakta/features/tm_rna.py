
import logging
import subprocess as sp
from collections import OrderedDict

from Bio.Seq import Seq

import bakta.config as cfg
import bakta.constants as bc

log = logging.getLogger('features:tm_rna')


def predict_tm_rnas(data, contigs_path):
    """Search for tmRNA sequences."""

    contigs = {c['id']: c for c in data['contigs']}
    txt_output_path = cfg.tmp_path.joinpath('tmrna.tsv')
    cmd = [
        'aragorn',
        '-m',  # detect tmRNAs
        '-gcbact',
        '-w',  # batch mode
        '-o', str(txt_output_path),
        str(contigs_path)
    ]
    if(cfg.complete == True):
        cmd.append('-c')  # complete circular sequence(s)
    else:
        cmd.append('-l')  # linear sequence(s)
    
    log.debug('cmd=%s', cmd)
    proc = sp.run(
        cmd,
        cwd=str(cfg.tmp_path),
        env=cfg.env,
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        universal_newlines=True
    )
    if(proc.returncode != 0):
        log.debug('stdout=\'%s\', stderr=\'%s\'', proc.stdout, proc.stderr)
        log.warning('tmRNAs failed! aragorn-error-code=%d', proc.returncode)
        raise Exception("aragorn error! error code: %i" % proc.returncode)

    tmrnas = []
    with txt_output_path.open() as fh:
        for line in fh:
            line = line.strip()
            cols = line.split()
            if(line[0] == '>'):
                contig = cols[0][1:]
            elif( len(cols) == 5 ):
                (nr, type, location, tag_location, tag_aa) = line.split()
                strand = bc.STRAND_FORWARD
                if(location[0] == 'c'):
                    strand = bc.STRAND_REVERSE
                    location = location[1:]
                (start, stop) = location[1:-1].split(',')
                start = int(start)
                stop = int(stop)

                # extract sequence
                seq = contigs[contig]['sequence'][start:stop]
                if(strand == bc.STRAND_REVERSE):
                    seq = str(Seq(seq).reverse_complement())
                
                tmrna = OrderedDict()
                tmrna['type'] = bc.FEATURE_TM_RNA
                tmrna['contig'] = contig
                tmrna['start'] = start
                tmrna['stop'] = stop
                tmrna['strand'] = strand
                tmrna['gene'] = 'ssrA'
                tmrna['product'] = 'transfer-messenger RNA, SsrA'
                tmrna['db_xrefs'] = ['SO:0000584']
                tmrna['sequence'] = seq
                
                tmrnas.append(tmrna)
                log.info(
                    'contig=%s, gene=%s, start=%i, stop=%i, strand=%s',
                    tmrna['contig'], tmrna['gene'], tmrna['start'], tmrna['stop'], tmrna['strand']
                )
    log.info('# %i', len(tmrnas))
    return tmrnas