"""
pyLDAvis Gensim
===============
Helper functions to visualize LDA models trained by Gensim
"""

import funcy as fp
import numpy as np
import pandas as pd
from past.builtins import xrange
from . import prepare as vis_prepare


def _extract_data(topic_model, corpus, dictionary, doc_topic_dists=None):
   import gensim
   
   if not gensim.matutils.ismatrix(corpus):
      corpus_csc = gensim.matutils.corpus2csc(corpus)
   else:
      corpus_csc = corpus
   
   vocab = list(dictionary.token2id.keys())
   # TODO: add the hyperparam to smooth it out? no beta in online LDA impl.. hmm..
   # for now, I'll just make sure we don't ever get zeros...
   beta = 0.01
   fnames_argsort = np.asarray(list(dictionary.token2id.values()), dtype=np.int_)
   term_freqs = corpus_csc.sum(axis=1).A.ravel()[fnames_argsort]
   term_freqs[term_freqs == 0] = beta
   doc_lengths = corpus_csc.sum(axis=0).A.ravel()

   assert term_freqs.shape[0] == len(dictionary), 'Term frequencies and Dictionary have different sizes {} != {}'.format(term_freqs.shape[0], len(dictionary))
   assert doc_lengths.shape[0] == len(corpus), 'Document lengths and corpus have different sizes {} != {}'.format(doc_lengths.shape[0], len(corpus))

   if doc_topic_dists is None:
      gamma, _ = topic_model.inference(corpus)
      doc_topic_dists = gamma / gamma.sum(axis=1)[:, None]

   topic = topic_model.state.get_lambda()
   topic = topic / topic.sum(axis=1)[:, None]
   topic = topic[:, fnames_argsort]
   topics_df = pd.DataFrame(data=topic, columns=dictionary.token2id)
   topics_df = topics_df[vocab]

   topic_term_dists = topics_df.values

   return {'topic_term_dists': topic_term_dists, 'doc_topic_dists': doc_topic_dists,
           'doc_lengths': doc_lengths, 'vocab': vocab, 'term_frequency': term_freqs}

def prepare(topic_model, corpus, dictionary, doc_topic_dist=None, **kargs):
    """Transforms the Gensim TopicModel and related corpus and dictionary into
    the data structures needed for the visualization.

    Parameters
    ----------
    topic_model : gensim.models.ldamodel.LdaModel
        An already trained Gensim LdaModel. The other gensim model types are
        not supported (PRs welcome).

    corpus : array-like list of bag of word docs in tuple form or scipy CSC matrix
        The corpus in bag of word form, the same docs used to train the model.
        The corpus is transformed into a csc matrix internally, if you intend to
        call prepare multiple times it is a good idea to first call
        `gensim.matutils.corpus2csc(corpus)` and pass in the csc matrix instead.

    For example: [(50, 3), (63, 5), ....]

    dictionary: gensim.corpora.Dictionary
        The dictionary object used to create the corpus. Needed to extract the
        actual terms (not ids).

    doc_topic_dist (optional): Document topic distribution from LDA (default=None)
        The document topic distribution that is eventually visualised, if you will
        be calling `prepare` multiple times it's a good idea to explicitly pass in
        `doc_topic_dist` as inferring this for large corpora can be quite
        expensive.

    **kwargs :
        additional keyword arguments are passed through to :func:`pyldavis.prepare`.

    Returns
    -------
    prepared_data : PreparedData
        the data structures used in the visualization

    Example
    --------
    For example usage please see this notebook:
    http://nbviewer.ipython.org/github/bmabey/pyLDAvis/blob/master/notebooks/Gensim%20Newsgroup.ipynb

    See
    ------
    See `pyLDAvis.prepare` for **kwargs.
    """
    opts = fp.merge(_extract_data(topic_model, corpus, dictionary, doc_topic_dist), kargs)
    return vis_prepare(**opts)
