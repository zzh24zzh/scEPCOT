import numpy as np
import torch,os
from util import check_region,predict_microc,predict_cage,predict_epis,filetobrowser,predict_hic,predict_epb
from scipy.sparse import load_npz
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

def predict_func(input_chrom, cop_type, input_region, input_file):
    if input_chrom == '' or cop_type == '':
        raise ValueError("Please specify a genomic region of interest")
    if input_file is None:
        raise ValueError("Please provide an ATAC-seq file")
    if not os.path.exists('refSeq/hg38/chr%s.npz'%input_chrom):
        raise ValueError("Please download the processed reference genome")
    # if len(input_file) != 2:
    #     raise ValueError("Please upload two files only, one for the reference genome and one for ATAC-seq")

    ref_genome = load_npz('refSeq/hg38/chr%s.npz'%input_chrom).toarray()
    atac_seq = load_npz(input_file.name).toarray()

    if cop_type == 'Micro-C (enter a 500 kb region)':
        chrom, start, end = check_region(input_chrom, input_region, ref_genome,500000)
    else:
        chrom, start, end = check_region(input_chrom, input_region, ref_genome,1000000)

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print(device)
    out_epi_binding = predict_epb(os.path.abspath('models/epi_bind.pt'), [start, end], ref_genome, atac_seq, device,
                               cop_type)
    out_cage = predict_cage(os.path.abspath('models/cage.pt'), [start, end], ref_genome, atac_seq, device, cop_type)

    out_epi = predict_epis(os.path.abspath('models/epi_track.pt'), [start, end], ref_genome, atac_seq, device, cop_type)

    if cop_type == 'Micro-C (enter a 500 kb region)':
        out_cop = predict_microc(os.path.abspath('models/microc.pt'), [start, end], ref_genome, atac_seq, device)
        np.savez_compressed( 'tmps/prediction_%s-%s-%s.npz' % (input_chrom, start+10000,end-10000),epb=out_epi_binding, epi=out_epi, cage=out_cage,
                            cop=out_cop)
        return ['tmps/prediction_%s-%s-%s.npz' % (input_chrom, start+10000,end-10000),
                filetobrowser(out_epi,out_cage,out_cop,input_chrom, start+10000,end-10000)]
    else:
        out_cop=predict_hic(os.path.abspath('models/hic.pt'), [start, end], ref_genome, atac_seq, device)
        np.savez_compressed('tmps/prediction_%s-%s-%s.npz' % (input_chrom, start + 20000, end - 20000),epb=out_epi_binding, epi=out_epi,
                            cage=out_cage,
                            cop=out_cop)

        return ['tmps/prediction_%s-%s-%s.npz' % (input_chrom, start + 20000, end - 20000),
                filetobrowser(out_epi,out_cage,out_cop,input_chrom, start + 20000, end - 20000)]


def make_plots(in_file,modal, maxv1, maxv2, epis):
    import matplotlib
    matplotlib.use("Agg")
    # matplotlib.pyplot.switch_backend('Agg')
    prediction = np.load(in_file.name)
    maxv1,maxv2=float(maxv1),float(maxv2)
    with open(os.path.abspath('data/epigenomes.txt'), 'r') as f:
        epigenomes = f.read().splitlines()

    bins = prediction['cop'].shape[-1]
    if epis=='':
        raise ValueError("Please choose epigenomic features to be visualized")
    num_mod = len(epis) + 1
    epi_idx=np.array([epigenomes.index(epi) for epi in epis])


    plt.rcParams['font.sans-serif'] = 'Arial'
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.size'] = 14

    if bins==480:
        fig = plt.figure(figsize=(9, num_mod + 4))
        gs = GridSpec(num_mod+4, 9)
        ax_map = [fig.add_subplot(gs[:4, :8])]
        axc=fig.add_subplot(gs[:4, 8:])
        axc.axis('off')
        axs = [fig.add_subplot(gs[4+i, :8]) for i in range(num_mod)]
    else:
        fig = plt.figure(figsize=(9, num_mod+12))
        gs = GridSpec(num_mod + 12, 9)
        ax_map = [fig.add_subplot(gs[4*i:4*i+4, :8]) for i in range(4)]
        axc = fig.add_subplot(gs[:8, 8:])
        axc.axis('off')
        axc1 = fig.add_subplot(gs[8:12, 8:])
        axc1.axis('off')
        axs = [fig.add_subplot(gs[12 + i, :8]) for i in range(num_mod)]

    if bins == 480:
        bin_coords = np.true_divide(np.arange(bins), np.sqrt(2))
        x, y = np.meshgrid(bin_coords, bin_coords)
        sin45 = np.sin(np.radians(45))
        x, y = x * sin45 + y * sin45, x * sin45 - y * sin45
        m=ax_map[0].pcolormesh(x, y, prediction['cop'], cmap='RdBu_r', vmin=0, vmax=maxv1)

        cbar=fig.colorbar(m,ax=axc,aspect=20,fraction=1)
    else:
        bin_coords = np.true_divide(np.arange(bins), np.sqrt(2))
        x, y = np.meshgrid(bin_coords, bin_coords)
        sin45 = np.sin(np.radians(45))
        x, y = x * sin45 + y * sin45, x * sin45 - y * sin45
        m = [ax_map[i].pcolormesh(x, y, prediction['cop'][i], cmap='RdBu_r', vmin=0, vmax=maxv1) for i in range(3)]
        cbar = fig.colorbar(m[0], ax=axc, aspect=30, fraction=1,shrink=0.85)
        cbar.set_label('log2(x)+1')
        cbar1 = fig.colorbar(m[2], ax=axc1, aspect=15, fraction=1,shrink=0.85)
        types=['CTCF ChIA-PET','POLR2 ChIA-PET','Hi-C']
        for i in range(3):
            ax_map[i].text(2, bins//2.5, types[i],va='top',fontsize=18,color='r')


    for i in range(len(ax_map)):
        ax_map[i].set_yticks([])
        ax_map[i].set_ylim(0, bins//2)
        ax_map[i].spines['left'].set_visible(False)

    for axm in axs+ax_map:
        axm.set_xticks([])
        axm.margins(x=0)
        axm.spines['top'].set_visible(False)
        axm.spines['right'].set_visible(False)
        axm.spines['bottom'].set_visible(False)
    for i in range(num_mod-1):
        if modal=='tracks':
            axs[i].fill_between(np.arange(prediction['epi'].shape[0]), 0, prediction['epi'][:,epi_idx[i]])
            axs[i].set_ylim(0, maxv2)
            axs[i].text(2, maxv2, epis[i],va='top')
        else:
            axs[i].fill_between(np.arange(prediction['epb'].shape[0]), 0, prediction['epb'][:, epi_idx[i]])
            axs[i].set_ylim(0, 1)
            axs[i].text(2, 1, epis[i], va='top')

    start=int(in_file.name.split('-')[1])
    chrom=int(in_file.name.split('prediction_')[1].split('-')[0])
    end= start+480000 if bins==480 else start + 960000
    seq_inter=1000 if bins==480 else 5000
    # tmp_cage=prediction['cage'].flatten().squeeze()
    # print(prediction['cage'].shape,tmp_cage.shape)
    axs[-1].fill_between(np.arange(prediction['cage'].shape[0]), 0, prediction['cage'])
    axs[-1].set_ylim(0, 8)
    axs[-1].text(2, 8, 'CAGE',va='top')
    axs[-1].set_xticks([i*prediction['cage'].shape[0]//4 for i in range(5)])
    axs[-1].set_xticklabels([start+i*bins*seq_inter//4 for i in range(5)])

    axs[-1].set_xlabel('chr%s:%s-%s'%(chrom,start,end))
    plt.show()
    return fig

# make_plots('tmps/prediction_11-10550000-10950000.npz',6,6,['CTCF'])