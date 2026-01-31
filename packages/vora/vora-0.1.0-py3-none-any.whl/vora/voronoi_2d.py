import alphashape
import numpy as np
from scipy import sparse
import matplotlib.pyplot as plt
from collections import defaultdict
from shapely.prepared import prep
from shapely.validation import make_valid
from shapely.geometry import Point, LineString
from scipy.spatial import Voronoi, Delaunay, voronoi_plot_2d
import warnings
warnings.filterwarnings("ignore")

def estimate_alphashape_alpha(points, percentile=95):
    """
    estimates alpha by looking at the distribution of edge lengths in the Delaunay triangulation.
    """
    # Delaunay triangulation
    tri = Delaunay(points)
    # edge lengths (A-B, B-C, C-A) of all triangles
    p = points[tri.simplices]
    a = np.sqrt(np.sum((p[:, 0] - p[:, 1])**2, axis=1))
    b = np.sqrt(np.sum((p[:, 1] - p[:, 2])**2, axis=1))
    c = np.sqrt(np.sum((p[:, 2] - p[:, 0])**2, axis=1))
    # Combine all lengths
    lengths = np.concatenate([a, b, c])
    # the cutoff length based on percentile
    # keep X% of the "small" connections.
    # The percentile depends on how "tight" you want the shape.
    # 90-95 is usually a good starting point.
    cutoff_length = np.percentile(lengths, percentile)
    # Convert to alpha (alpha = 1 / radius ~ 1 / length)
    # Note: The exact conversion depends on implementation, but 1/length 
    # is a solid heuristic for the 'alphashape' library.
    alpha_est = 1.0 / cutoff_length
    return alpha_est

def expand_polygon(polygon, percent=1.0):
    """
    expand polygon by a certain percentage of its bounding box diagonal.
    """
    # use diagonal of bounding box as reference
    minx, miny, maxx, maxy = polygon.bounds
    diag = ((maxx-minx)**2 + (maxy-miny)**2) ** 0.5
    dist = diag * (percent/100.0)
    return polygon.buffer(dist)

def create_default_boundary(points):
    """
    Create a default boundary polygon using alpha shape and expand it.
    The polygon is assumed to be the region where sources can be located.
    """
    expand_percent = 2.0  # percent to expand the alpha shape polygon
    alpha = estimate_alphashape_alpha(points, percentile=98.0)
    polygon = alphashape.alphashape(points, alpha)
    if not polygon.is_valid:
        polygon = make_valid(polygon)
    polygon = expand_polygon(polygon, expand_percent)
    return polygon

def plot_voronoi(points, boundary=None):
    if boundary is None:
        polygon = create_default_boundary(points)
    else:
        polygon = boundary
    vor = Voronoi(points)

    fig, ax = plt.subplots(figsize=(10, 8))
    voronoi_plot_2d(vor, ax=ax, 
                    show_vertices=False, show_points=False, 
                    line_colors='orange', line_width=1, point_size=10)
    ax.plot(points[:, 0], points[:, 1], '^', color='k')
    if polygon:
        x, y = polygon.exterior.xy
        ax.plot(x, y, color='red')
    plt.title('Voronoi Diagram with Boundary')
    plt.show()
    return fig, ax

def voronoi_neighbors_2d(points, boundary=None, order=1):
    """
    computation of nth-order Voronoi neighbors.
    """
    points = np.asarray(points)
    vor = Voronoi(points)
    if boundary is None:
        boundary = create_default_boundary(points)
    # step1: use 'prep' to only include neighbors whose shared ridge intersects the boundary.
    prepared_boundary = prep(boundary)
    valid_indices = []
    vertices = vor.vertices
    ridge_vertices = vor.ridge_vertices
    for i, ridge in enumerate(ridge_vertices):
        # ridge is a list of vertex indices. -1 indicates a vertex at infinity.
        if -1 in ridge:
            # infinite ridge: check if the finite start point is inside
            p_idx = ridge[0] if ridge[0] != -1 else ridge[1]
            pt = Point(vertices[p_idx])
            if prepared_boundary.contains(pt):
                valid_indices.append(i)
        else:
            # finite ridge: check intersection (False only if completely outside)
            line = LineString(vertices[ridge])
            if prepared_boundary.intersects(line):
                valid_indices.append(i)
    pairs = vor.ridge_points[valid_indices]

    # step2: construct a sparse boolean matrix where M[i, j] = 1 if i and j are neighbors
    N = len(points)
    if len(pairs) == 0:
        return {i: [] for i in range(N)}
    # create symmetric adjacency matrix
    row = np.concatenate([pairs[:, 0], pairs[:, 1]])
    col = np.concatenate([pairs[:, 1], pairs[:, 0]])
    data = np.ones(len(row), dtype=bool)
    adj_matrix = sparse.csr_matrix((data, (row, col)), shape=(N, N))

    # step3: compute higher orders via matrix power
    if order == 1:
        final_matrix = adj_matrix
    else:
        # Add Identity to include self-loops (needed to keep lower-order neighbors)
        # (A + I)^n captures all nodes reachable in n steps or fewer
        identity = sparse.eye(N, dtype=bool, format='csr')
        path_matrix = adj_matrix + identity
        # compute matrix power (this is much faster than Python loops)
        # result is boolean: non-zero means reachable within 'order' steps
        final_matrix = path_matrix ** order
        # remove the diagonal (self-neighbors) before returning
        final_matrix.setdiag(0)
        final_matrix.eliminate_zeros()

    # step4: convert to dictionary
    # convert sparse matrix rows to lists
    neighbors_dict = {}
    rows = final_matrix.tolil().rows 
    
    for i, neighbors in enumerate(rows):
        neighbors_dict[i] = [int(n) for n in neighbors]
        
    return neighbors_dict
