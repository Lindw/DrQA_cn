#!/usr/bin/env python3

# simple interactive model. only run a single thread process to void troubles

import torch
import code
import argparse
import logging
import prettytable
import time

from drqa.reader import Predictor
from drqa.pipeline.simpleDrQA import SDrQA

logger = logging.getLogger()
logger.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s: [ %(message)s ]', '%m/%d/%Y %I:%M:%S %p')
console = logging.StreamHandler()
console.setFormatter(fmt)
logger.addHandler(console)


# ------------------------------------------------------------------------------
# Commandline arguments & init
# ------------------------------------------------------------------------------


parser = argparse.ArgumentParser()
parser.add_argument('--model', type=str, default=None,
                    help='Path to model to use')
parser.add_argument('--tokenizer', type=str, default='zh',
                    help=("String option specifying tokenizer type to use "
                          "(e.g. 'corenlp')"))
parser.add_argument('--no-cuda', action='store_true',
                    help='Use CPU only')
parser.add_argument('--embedding-file', default=None,
                    help='embedding')
parser.add_argument('--gpu', type=int, default=-1,
                    help='Specify GPU device id to use')
parser.add_argument('--tfidf-model', type=str, default=None)
parser.add_argument('--db', type=str, default=None)
args = parser.parse_args()

args.cuda = not args.no_cuda and torch.cuda.is_available()
if args.cuda:
    torch.cuda.set_device(args.gpu)
    logger.info('CUDA enabled (GPU %d)' % args.gpu)
else:
    logger.info('Running on CPU only.')

predictor = Predictor(args.model, args.tokenizer, num_workers=0,
                      embedding_file=args.embedding_file)
if args.cuda:
    predictor.cuda()

# maybe a different embedding to save memory
drqa = SDrQA(predictor, args.tfidf_model, args.db, ebdPath=args.embedding_file)
# ------------------------------------------------------------------------------
# Drop in to interactive mode
# ------------------------------------------------------------------------------


def process(question, doc_n=1, pred_n=1, net_n=1):
    t0 = time.time()
    answers = drqa.predict(question, qasTopN=pred_n,
                           docTopN=doc_n, netTopN=net_n)

    def sort(a):
        return (0.2 + a['answerScore']) * a['contextScore']
    answers = sorted(answers, key=sort)
    for ans in answers:
        print('---------------------------------------------------------')
        print(ans['text'])
        print("======== answer :" + ans['answer'])
        print('answer score : ' + str(ans['answerScore']))
        print('context score : ' + str(ans['contextScore']))
    # predictions = predictor.predict(document, question, candidates, top_n)
    # table = prettytable.PrettyTable(['Rank', 'Span', 'Score'])
    # for i, p in enumerate(predictions, 1):
    #     table.add_row([i, p[0], p[1]])
    # print(table)
    print('Time: %.4f' % (time.time() - t0))


banner = """
DrQA Interactive Document Reader Module
>> process(question, doc_n=1, pred_n=1, net_n=1):
    doc_n: doc number in database
    pred_n: answer number for every context
    net_n: doc number in search engine
>> usage()
"""


def usage():
    print(banner)


code.interact(banner=banner, local=locals())
