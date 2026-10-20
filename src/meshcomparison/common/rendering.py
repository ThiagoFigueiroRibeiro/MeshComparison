import numpy as np


def add_default_lights(scene):
    import pyrender

    light = pyrender.DirectionalLight(color=np.ones(3), intensity=3.0)

    poses = []
    poses.append(np.eye(4))

    p2 = np.eye(4)
    p2[:3, 3] = [2, 2, 2]
    poses.append(p2)

    p3 = np.eye(4)
    p3[:3, 3] = [-2, -2, 2]
    poses.append(p3)

    for p in poses:
        scene.add(light, pose=p)


class OrthoRenderer:
    """
    Offscreen orthographic renderer that keeps its OpenGL context and uploaded meshes between calls.

    Creating a context and re-uploading the mesh for every image dominates the cost of rendering many views;
    pixels are identical to ``render_ortho_rgba``. Use as a context manager and call it from one thread only
    (an OpenGL context belongs to the thread that created it).
    """

    def __init__(self, bg_color, width=1600, height=1200, smooth=True):
        import pyrender

        self._pyrender = pyrender
        self._bg_color = np.asarray(bg_color, dtype=np.float32)
        self._smooth = smooth
        self._renderer = pyrender.OffscreenRenderer(viewport_width=width, viewport_height=height)
        self._scenes = {}  # name -> (scene, camera node or None)

    def add_mesh(self, name, mesh):
        pyrender = self._pyrender
        scene = pyrender.Scene(bg_color=self._bg_color, ambient_light=np.array([0.35, 0.35, 0.35, 1.0]))
        scene.add(pyrender.Mesh.from_trimesh(mesh, smooth=self._smooth))
        add_default_lights(scene)
        self._scenes[name] = [scene, None]

    def render(self, name, camera_cfg):
        """RGBA image (uint8) of mesh ``name`` seen through ``camera_cfg`` (xmag, ymag, zfar, pose)."""
        pyrender = self._pyrender
        entry = self._scenes[name]
        scene, node = entry
        if node is not None:
            scene.remove_node(node)
        camera = pyrender.OrthographicCamera(
            xmag=camera_cfg["xmag"], ymag=camera_cfg["ymag"], znear=0.01, zfar=camera_cfg["zfar"])
        entry[1] = scene.add(camera, pose=camera_cfg["pose"])
        color, _ = self._renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
        return color.copy()

    def close(self):
        if self._renderer is not None:
            self._renderer.delete()
            self._renderer = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def render_ortho_rgba(mesh, camera_cfg, bg_color, width=1600, height=1200, smooth=True):
    """Render ``mesh`` with an orthographic camera and return the RGBA image (uint8)."""
    import pyrender

    scene = pyrender.Scene(
        bg_color=np.asarray(bg_color, dtype=np.float32),
        ambient_light=np.array([0.35, 0.35, 0.35, 1.0])
    )

    scene.add(pyrender.Mesh.from_trimesh(mesh, smooth=smooth))

    cam = pyrender.OrthographicCamera(
        xmag=camera_cfg["xmag"],
        ymag=camera_cfg["ymag"],
        znear=0.01,
        zfar=camera_cfg["zfar"]
    )
    scene.add(cam, pose=camera_cfg["pose"])
    add_default_lights(scene)

    renderer = pyrender.OffscreenRenderer(viewport_width=width, viewport_height=height)
    color, _ = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
    renderer.delete()

    return color
