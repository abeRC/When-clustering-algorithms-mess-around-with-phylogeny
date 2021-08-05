from gensim.models import Doc2Vec
from gensim.models.doc2vec import TaggedDocument

from nltk.cluster import KMeansClusterer
import nltk
 
from sklearn import cluster
from sklearn import metrics

import pickle
import re, os, sys
from pprint import pprint

from pympler import asizeof ### DBG

NUM_CLUSTERS=5
DATA_FOLDER = "family_pages_mod"
MODEL_DUMP_NAME = "mymodel.dump"
idx_to_name = dict()

def set_from_file (filename):
    with open(filename, "r") as f:
        lines = f.readlines()
    s = set([l.replace('\n', '') for l in lines if l])
    return s

def fill_eq_tables (list_of_families):
    global idx_to_name

    with open("equivalence_table.txt", "w") as eq_table:
        for i, fam in enumerate(sorted(list_of_families)):
            idx_to_name[i] = fam
            eq_table.write(f"{i} {fam}\n") # just for paranoia's sake

def make_big_scary_document_matrix (folder):
    big_scary_document_matrix = []
    # os.listdir returns a list in arbitrary order
    for i, file in enumerate(sorted(os.listdir(folder))):
        if file.endswith(".txt"): # just in case, you know!
            # get proper path and read contents
            filepath = os.path.join(DATA_FOLDER, file)
            with open(filepath, "r") as f:
                raw = f.read()

            # (very fancy and innovative criteria)
            # replace punctuation and other weird characters with spaces (exception made for hyphen)
            raw = re.sub("[^A-z0-9-]", " ", raw)
            words = [s for s in raw.split() 
                                    if len(s) >= 4]

            # create TaggedDocument object for the Doc2Vec model
            tags = [i] # must be an iterable
            tagged_doc = TaggedDocument(words, tags)

            # add it to the pile
            big_scary_document_matrix.append(tagged_doc)  
    return big_scary_document_matrix

def main ():
    list_of_families = set_from_file("families in Gnathostomata.txt")
    fill_eq_tables(list_of_families)
    
    # use cached result if possible
    if os.path.isfile(MODEL_DUMP_NAME):
        model = Doc2Vec.load(MODEL_DUMP_NAME)
    else:
        big_scary_document_matrix = make_big_scary_document_matrix(DATA_FOLDER)
        #print(f"matrix size: {asizeof.asizeof(big_scary_document_matrix)} bytes")

        """
        # its actually pretty ok, I'm just paranoid
        with open("big_scary_document_matrix.dump", "wb") as p_name:
            pickle.dump(big_scary_document_matrix, p_name, pickle.HIGHEST_PROTOCOL)
        """

        # create Word2Vec model
        # we chose to use hierarchical softmax because it sounds cool
        model = Doc2Vec(documents=big_scary_document_matrix, hs=1) # maybe mess w/ min_count?
        with open(MODEL_DUMP_NAME, "wb") as mod_dump:
            model.save(mod_dump)
    
    # get document vectors
    X = model.dv.vectors.copy()
    docs = model.dv.index_to_key.copy() # these come from our tags and should be ints
    #print(len(X), len(docs))

    ### nltk kmeans
    if os.path.isfile("nltk_clust.dump"):
        with open("nltk_clust.dump", "rb") as nltk_dump:
            assigned_clusters = pickle.load(nltk_dump)
    else:
        kclusterer = KMeansClusterer(NUM_CLUSTERS, distance=nltk.cluster.util.cosine_distance, repeats=25)
        assigned_clusters = kclusterer.cluster(X, assign_clusters=True)
        with open("nltk_clust.dump", "wb") as nltk_dump:
            pickle.dump(assigned_clusters, nltk_dump, pickle.HIGHEST_PROTOCOL)
    
    ### sklearn kmeans
    if os.path.isfile("sklearn_clust.dump"):
        with open("sklearn_clust.dump", "rb") as sklearn_dump:
            kmeans = pickle.load(sklearn_dump)
    else:
        kmeans = cluster.KMeans(n_clusters=NUM_CLUSTERS)
        kmeans.fit(X)
        with open("sklearn_clust.dump", "wb") as sklearn_dump:
            pickle.dump(kmeans, sklearn_dump, pickle.HIGHEST_PROTOCOL)
    
    # save results
    with open("kmeans_nltk.log", "w") as f:
        f.write("Family    Cluster\n\n")
        for i, doc in enumerate(docs): # i == doc because redundancy always comes around
            f.write(str(idx_to_name[doc]) + " : " + str(assigned_clusters[i]) + "\n")
    with open("kmeans_sklearn.log", "w") as f:
        labels = kmeans.labels_
        centroids = kmeans.cluster_centers_
        silhouette_score = metrics.silhouette_score(X, labels, metric='euclidean')
        f.write("Cluster id labels for inputted data:\n")
        f.write(str(list(labels)) + "\n\n")
        f.write("Centroids data\n")
        f.write(str(centroids) + "\n\n") 
        f.write("Score (Opposite of the value of X on the K-means objective which is Sum of distances of samples to their closest cluster center):\n")
        f.write(str(kmeans.score(X)) + "\n")
        f.write("Silhouette_score (from -1 to +1): \n")
        f.write(str(silhouette_score) + "\n") 

    # check the actual philogeny
    chond = set_from_file("list_chond.txt")
    ost = set_from_file("list_ost.txt")
    mam = set_from_file("list_mam.txt")
    saur = set_from_file("list_saur.txt")
    amp = set_from_file("list_amp.txt")

    def determine_class (family_name):
        if family_name in chond:
            return 'chond'
        elif family_name in ost:
            return 'ost'
        elif family_name in mam:
            return 'mam'
        elif family_name in saur:
            return 'saur'
        elif family_name in amp:
            return 'amp'
        else:
            print(family_name)
            raise("bad")

    def check_clusters (assigned_cl, method_name):
        clusters = []
        # initialize clusters with empty counts
        for _ in range(NUM_CLUSTERS):
            clusters.append({'chond':0, 'ost': 0, 'mam': 0, 'saur': 0, 'amp': 0})
        
        # determine counts of each kind of animal in each cluster
        for i, val in enumerate(assigned_cl):
            group = determine_class(idx_to_name[i])
            clusters[val][group] += 1

        # print results
        print(f"{method_name}:")
        for i, clu in enumerate(clusters):
            print(f"Cluster {i}")
            pprint(clu)
        print()
    
    check_clusters(assigned_clusters, "NLTK")
    check_clusters(labels, "sklearn")
    totals = {'chond':len(chond), 'ost': len(ost), 'mam': len(mam), 'saur': len(saur), 'amp': len(amp)}
    print("Totals (for comparison):")
    pprint(totals)

if __name__ == "__main__":
    main()
