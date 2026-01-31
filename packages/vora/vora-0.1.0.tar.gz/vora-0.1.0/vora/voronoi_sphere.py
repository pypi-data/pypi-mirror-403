import numpy as np
from scipy.spatial import SphericalVoronoi, ConvexHull, Delaunay
from scipy import sparse
from shapely.geometry import Polygon, Point, LineString
from shapely.prepared import prep
from shapely.validation import make_valid
import alphashape
import warnings
warnings.filterwarnings("ignore")

def project_to_tangent_plane(points):
    """
    Projects spherical points (Nx3) to a 2D tangent plane (Nx2) 
    using Stereographic projection centered at the cluster centroid.
    """
    # 1. Calculate Centroid
    centroid = np.mean(points, axis=0)
    centroid /= np.linalg.norm(centroid) # normalize

    # 2. Construct Rotation Matrix to align centroid to North Pole (0,0,1)
    #    (Standard geometry trick to simplify projection)
    z_axis = np.array([0, 0, 1])
    v = np.cross(centroid, z_axis)
    c = np.dot(centroid, z_axis)
    k = 1.0 / (1.0 + c)

    # Skew-symmetric cross-product matrix
    vx = np.array([[0, -v[2], v[1]], 
                   [v[2], 0, -v[0]], 
                   [-v[1], v[0], 0]])
    
    # Rodrigues' rotation formula
    R = np.eye(3) + vx + np.dot(vx, vx) * k
    
    # Rotate points so the patch center is at the top of the sphere
    rotated_points = np.dot(points, R.T)

    # 3. Stereographic Projection: x = X / (1 + Z), y = Y / (1 + Z)
    #    This preserves circles and angles locally (conformal).
    denoms = 1.0 + rotated_points[:, 2]
    # Avoid division by zero for points opposite to the center (unlikely in a patch)
    denoms[np.abs(denoms) < 1e-9] = 1e-9 
    
    x_proj = rotated_points[:, 0] / denoms
    y_proj = rotated_points[:, 1] / denoms
    
    return np.column_stack([x_proj, y_proj]), R


def estimate_alphashape_alpha(points_2d, percentile=95):
    """ Same as your 2D function, acting on the projected 2D points """
    tri = Delaunay(points_2d)
    p = points_2d[tri.simplices]
    a = np.sqrt(np.sum((p[:, 0] - p[:, 1])**2, axis=1))
    b = np.sqrt(np.sum((p[:, 1] - p[:, 2])**2, axis=1))
    c = np.sqrt(np.sum((p[:, 2] - p[:, 0])**2, axis=1))
    lengths = np.concatenate([a, b, c])
    cutoff_length = np.percentile(lengths, percentile)
    return 1.0 / cutoff_length

def create_projected_boundary(points_2d):
    """ Creates the boundary polygon in the 2D projected space """
    expand_percent = 2.0
    alpha = estimate_alphashape_alpha(points_2d, percentile=98.0)
    polygon = alphashape.alphashape(points_2d, alpha)
    
    if not polygon.is_valid:
        polygon = make_valid(polygon)
        
    # Expand logic (same as yours)
    minx, miny, maxx, maxy = polygon.bounds
    diag = ((maxx-minx)**2 + (maxy-miny)**2) ** 0.5
    dist = diag * (expand_percent/100.0)
    
    return polygon.buffer(dist)


def voronoi_neighbors_spherical_patch(points, order=1):
    """
    Computes nth-order Voronoi neighbors on a spherical patch.
    Filters neighbors based on an alpha-shape boundary.
    """
    points = np.asarray(points)
    # Ensure normalization
    norms = np.linalg.norm(points, axis=1, keepdims=True)
    points = points / norms

    # --- Step 1: Topology (Who is connected?) ---
    # We use ConvexHull because Spherical Voronoi is the dual of the Hull.
    # Neighbors in Voronoi = Vertices connected by an edge in the Convex Hull.
    hull = ConvexHull(points)
    
    # We also need the SphericalVoronoi object to get the coordinates of the "Ridges"
    # (The ridges connect the circumcenters of the hull triangles)
    sv = SphericalVoronoi(points, radius=1.0, center=[0, 0, 0], threshold=1.0/6371000.0)
    sv.sort_vertices_of_regions() # Ensure internal consistency

    # --- Step 2: Boundary (Where is the edge of the data?) ---
    # Project to 2D to create a valid planar polygon for filtering
    points_2d, rotation_matrix = project_to_tangent_plane(points)
    boundary_polygon = create_projected_boundary(points_2d)
    prepared_boundary = prep(boundary_polygon)

    # --- Step 3: Filter Ridges ---
    # We iterate over the Convex Hull faces (simplices).
    # Each edge between two simplices corresponds to a Voronoi Ridge.
    
    # Map: simplex_index -> Voronoi_vertex_coordinate
    # (In scipy, sv.vertices[i] corresponds to hull.simplices[i])
    voronoi_verts = sv.vertices
    
    # Rotate Voronoi vertices to the same 2D frame as our boundary
    # so we can check if the ridge is inside the polygon
    vor_verts_rotated = np.dot(voronoi_verts, rotation_matrix.T)
    denoms = 1.0 + vor_verts_rotated[:, 2]
    denoms[np.abs(denoms) < 1e-9] = 1e-9
    vx_proj = vor_verts_rotated[:, 0] / denoms
    vy_proj = vor_verts_rotated[:, 1] / denoms
    vor_verts_2d = np.column_stack([vx_proj, vy_proj])

    # Structure to store valid pairs
    pairs = []
    
    # hull.neighbors has shape (N_simplices, 3). 
    # It lists the 3 neighboring simplices for every simplex.
    for i, neighbors in enumerate(hull.neighbors):
        for j in neighbors:
            # Check each pair only once
            if i < j: 
                # The Ridge connects the Voronoi vertex of simplex i and simplex j
                p1 = vor_verts_2d[i]
                p2 = vor_verts_2d[j]
                
                # Create the ridge line in 2D
                ridge_line = LineString([p1, p2])
                
                # The CRITICAL CHECK: Does this ridge intersect our alpha shape?
                # (Same logic as your 2D code)
                if prepared_boundary.intersects(ridge_line):
                    # If yes, the points sharing this edge are neighbors.
                    # We need to find WHICH two points share the edge between simplex i and j.
                    simplex_i = hull.simplices[i]
                    simplex_j = hull.simplices[j]
                    
                    # Intersection of indices gives the shared edge vertices
                    shared_edge = np.intersect1d(simplex_i, simplex_j)
                    
                    if len(shared_edge) == 2:
                        pairs.append(shared_edge)

    if not pairs:
        return {i: [] for i in range(len(points))}

    pairs = np.array(pairs)

    # --- Step 4: Adjacency Matrix & Higher Order (Same as your 2D code) ---
    N = len(points)
    row = np.concatenate([pairs[:, 0], pairs[:, 1]])
    col = np.concatenate([pairs[:, 1], pairs[:, 0]])
    data = np.ones(len(row), dtype=bool)
    adj_matrix = sparse.csr_matrix((data, (row, col)), shape=(N, N))

    if order == 1:
        final_matrix = adj_matrix
    else:
        identity = sparse.eye(N, dtype=bool, format='csr')
        path_matrix = adj_matrix + identity
        final_matrix = path_matrix ** order
        final_matrix.setdiag(0)
        final_matrix.eliminate_zeros()

    neighbors_dict = {}
    rows = final_matrix.tolil().rows 
    for i, neighbors in enumerate(rows):
        neighbors_dict[i] = [int(n) for n in neighbors]
        
    return neighbors_dict


def voronoi_neighbors_spherical_globe(points, order=1):
    """
    Computes nth-order Voronoi neighbors on a sphere without boundary constraints.
    Suitable for global data where wrapping around the sphere is expected.
    """
    points = np.asarray(points)
    
    # 1. Normalize points to ensure they lie on the unit sphere
    #    (ConvexHull is sensitive to points slightly off-surface)
    norms = np.linalg.norm(points, axis=1, keepdims=True)
    points = points / norms
    N = len(points)

    # 2. Compute Convex Hull
    #    On a sphere, the Convex Hull is equivalent to the Delaunay Triangulation.
    #    Vertices connected by a Hull edge are Voronoi neighbors.
    try:
        hull = ConvexHull(points)
    except Exception as e:
        # Fallback for degenerate cases (e.g., all points on equator/coplanar)
        print(f"ConvexHull failed (likely coplanar points): {e}")
        return {i: [] for i in range(N)}

    # 3. Extract edges (neighbors) from the Hull Simplices (triangles)
    #    Each simplex is a triangle of indices [A, B, C]
    simplices = hull.simplices
    
    # We create arrays of "source" and "target" indices for the edges
    # Edges: column 0->1, 1->2, 2->0
    src = np.concatenate([simplices[:, 0], simplices[:, 1], simplices[:, 2]])
    dst = np.concatenate([simplices[:, 1], simplices[:, 2], simplices[:, 0]])

    # 4. Construct Sparse Adjacency Matrix
    #    We make it symmetric by concatenating (src->dst) and (dst->src)
    row = np.concatenate([src, dst])
    col = np.concatenate([dst, src])
    data = np.ones(len(row), dtype=bool)
    
    # Create the matrix
    adj_matrix = sparse.csr_matrix((data, (row, col)), shape=(N, N))

    # 5. Compute higher orders (Matrix Power)
    if order == 1:
        final_matrix = adj_matrix
    else:
        # Add identity to allow "staying in place" (captures neighbors within k steps)
        identity = sparse.eye(N, dtype=bool, format='csr')
        path_matrix = adj_matrix + identity
        
        # Matrix power is efficient for finding n-th degree connections
        final_matrix = path_matrix ** order
        
        # Clean up: remove self-loops and explicit zeros
        final_matrix.setdiag(0)
        final_matrix.eliminate_zeros()

    # 6. Convert to Dictionary
    neighbors_dict = {}
    # Convert to list of lists (tolil) for efficient row iteration
    rows = final_matrix.tolil().rows 
    
    for i, neighbors in enumerate(rows):
        neighbors_dict[i] = [int(n) for n in neighbors]
        
    return neighbors_dict