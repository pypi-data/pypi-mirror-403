from time import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import offsetbox
from sklearn import manifold, datasets, decomposition, ensemble, discriminant_analysis, random_projection

digits = datasets.load_digits(n_class=6)
X, y = digits.data, digits.target
n_neighbors = 30

def plot_embedding(X, title=None):
    X = (X - X.min(0)) / (X.max(0) - X.min(0))
    plt.figure(figsize=(10, 10))
    ax = plt.subplot(111)
    for i in range(X.shape[0]):
        plt.text(X[i,0], X[i,1], str(y[i]), color=plt.cm.Set1(y[i]/10.), fontdict={'weight':'bold','size':9})
    if hasattr(offsetbox,'AnnotationBbox'):
        shown = np.array([[1.,1.]])
        for i in range(X.shape[0]):
            if np.min(np.sum((X[i]-shown)**2,1))<4e-3: continue
            shown = np.r_[shown,[X[i]]]
            ax.add_artist(offsetbox.AnnotationBbox(offsetbox.OffsetImage(digits.images[i], cmap=plt.cm.gray_r), X[i]))
    plt.xticks([]); plt.yticks([]); 
    if title: plt.title(title)

# Show grid of digits
n_img = 20; img = np.zeros((10*n_img,10*n_img))
for i in range(n_img):
    for j in range(n_img):
        img[10*i+1:10*i+9, 10*j+1:10*j+9] = X[i*n_img+j].reshape(8,8)
plt.figure(figsize=(10,10)); plt.imshow(img, cmap=plt.cm.binary); plt.title('Sample digits'); plt.xticks([]); plt.yticks([])

# Embeddings
for name, emb in [
    ("Random Projection", random_projection.SparseRandomProjection(n_components=2, random_state=42)),
    ("PCA", decomposition.TruncatedSVD(n_components=2)),
    ("LDA", discriminant_analysis.LinearDiscriminantAnalysis(n_components=2)),
    ("Isomap", manifold.Isomap(n_neighbors=n_neighbors, n_components=2)),
    ("LLE", manifold.LocallyLinearEmbedding(n_neighbors=n_neighbors, n_components=2, method='standard')),
    ("Modified LLE", manifold.LocallyLinearEmbedding(n_neighbors=n_neighbors, n_components=2, method='modified')),
    ("Hessian LLE", manifold.LocallyLinearEmbedding(n_neighbors=n_neighbors, n_components=2, method='hessian')),
    ("LTSA", manifold.LocallyLinearEmbedding(n_neighbors=n_neighbors, n_components=2, method='ltsa')),
    ("MDS", manifold.MDS(n_components=2, n_init=1, max_iter=100, init='random')),
    ("Random Forest", decomposition.TruncatedSVD(n_components=2)),
    ("Spectral", manifold.SpectralEmbedding(n_components=2, random_state=0)),
    ("t-SNE", manifold.TSNE(n_components=2, init='pca', random_state=0))
]:
    print(name); t0=time()
    if name=="LDA": X2 = X.copy(); X2.flat[::X.shape[1]+1]+=0.01; X_emb = emb.fit_transform(X2,y)
    elif name=="Random Forest":
        X_rf = ensemble.RandomTreesEmbedding(n_estimators=200, random_state=0, max_depth=5).fit_transform(X)
        X_emb = emb.fit_transform(X_rf)
    else: X_emb = emb.fit_transform(X)
    plot_embedding(X_emb, f"{name} (time {time()-t0:.2f}s)")

plt.show()
