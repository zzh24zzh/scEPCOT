import gdown,os,argparse
def parser_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--downloadRefseq', '-d',default=True, action='store_false',
                          help='whether download reference sequence')

    args = parser.parse_args()
    return args

def download_models():
    gdown.download_folder('https://drive.google.com/drive/u/1/folders/1oqrRToBfzjfkDoQzy8SGRY1x2qGhAwj1')

def download_examples():
    gdown.download('https://drive.google.com/uc?id=1QW4hVjgxZZeQYXO0XyWhALhLyy-fEpPP',output='examples/chr11.npz')
    gdown.download('https://drive.google.com/uc?id=1EZ-gE2Gs2hRpNIali1dSOijOkXYqx4Sv',
                   output='examples/GM12878_atac_chr11.npz')

def download_refseq_hg38():
    if not os.path.exists('refSeq'):
        os.mkdir('refSeq')
    gdown.download('https://drive.google.com/uc?id=1iqOKKNFwjl9hMZovxxhG-t_Y1MZw45R0',
                   output='refSeq/hg38.tar.gz')
    os.system('tar -xvf refSeq/hg38.tar.gz -C refSeq/')
    os.remove('refSeq/hg38.tar.gz')

def main():
    args=parser_args()
    download_models()
    download_examples()
    if args.downloadRefseq:
        download_refseq_hg38()

if __name__=='__main__':
    main()
