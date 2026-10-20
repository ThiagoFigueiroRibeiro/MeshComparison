import os

import trimesh


def ensure_dirs(base_out, subdirs):
    """Create ``base_out/<relative path>`` for each entry of ``subdirs`` ({key: relative path parts})."""
    paths = {key: os.path.join(base_out, *parts) for key, parts in subdirs.items()}
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    return paths


def load_mesh(path):
    """
    Loads STL/OBJ/PLY/etc. using trimesh.
    This does NOT support FBX.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".fbx":
        raise ValueError(
            f"FBX is not supported in this pipeline: {path}\n"
            f"Please convert FBX -> STL first and pass .stl files."
        )

    try:
        loaded = trimesh.load(path, force='scene', process=False, maintain_order=True)

        if isinstance(loaded, trimesh.Trimesh):
            mesh = loaded.copy()

        elif isinstance(loaded, trimesh.Scene):
            # bake transforms from the scene graph
            meshes = []
            for name, geom in loaded.geometry.items():
                # apply scene transform for each geometry instance
                for node_name in loaded.graph.nodes_geometry:
                    # graph.get returns transform from node to world
                    try:
                        transform, geom_name = loaded.graph[node_name]
                    except Exception:
                        continue
                    if geom_name != name:
                        continue
                    g = geom.copy()
                    g.apply_transform(transform)
                    meshes.append(g)

            if len(meshes) == 0:
                # fallback: concatenate geometries without transforms
                geoms = [g.copy() for g in loaded.geometry.values()]
                if len(geoms) == 0:
                    raise ValueError(f"No geometry found in: {path}")
                mesh = geoms[0] if len(geoms) == 1 else trimesh.util.concatenate(geoms)
            else:
                mesh = meshes[0] if len(meshes) == 1 else trimesh.util.concatenate(meshes)

        else:
            raise TypeError(f"Unsupported loaded type for {path}: {type(loaded)}")

        mesh.remove_unreferenced_vertices()
        return mesh

    except Exception as e:
        raise RuntimeError(f"Could not load mesh file: {path}\nReason: {e}")
